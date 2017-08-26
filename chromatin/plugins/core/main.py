from chromatin.state import ChromatinTransitions, ChromatinComponent
from chromatin.plugins.core.messages import (AddPlugin, ShowPlugins, Start, SetupPlugins, SetupVenvs, InstallMissing,
                                             AddVenv, IsInstalled, Activated, PostSetup, Installed, UpdatePlugins,
                                             Updated, Reboot, Activate, AlreadyActive)
from chromatin.venvs import VenvExistent
from chromatin.env import Env
from chromatin.venv import Venv
from chromatin.logging import Logging
from chromatin.host import PluginHost
from chromatin.util import resources

from amino.state import State, EitherState
from amino import __, do, _, Either, L, Just, Future, List, Right, Boolean, Lists, Maybe, curried
from amino.util.string import camelcaseify
from amino.boolean import true, false

from ribosome.machine import Message
from ribosome.machine.base import io, RunIOsParallel, SubProcessSync
from ribosome.machine.transition import Error
from ribosome.machine import trans
from ribosome.nvim import NvimFacade, NvimIO
from ribosome.machine.messages import Info, NvimIOTask
from ribosome.rpc import define_handler, RpcHandlerSpec, DefinedHandler


class PluginFunctions(Logging):

    @do
    def setup_venvs(self) -> EitherState[Env, List[Message]]:
        '''check whether a venv exists for each plugin in the self.env.
        for those that don't, create self.venvs in `g:chromatin_venv_dir`.
        '''
        venv_facade = yield EitherState.inspect_f(_.venv_facade)
        plugins = yield EitherState.inspect(_.plugins)
        jobs = plugins / venv_facade.check
        existent, absent = jobs.split_type(VenvExistent)
        ios = absent / _.plugin / venv_facade.bootstrap / __.map(AddVenv).map(_.pub)
        yield EitherState.pure(existent.map(_.venv).map(IsInstalled).cat(RunIOsParallel(ios)))

    @do
    def install_plugins(self, venvs: List[Venv], update: Boolean) -> EitherState[Env, List[Message]]:
        '''run subprocesses in sequence that install packages into their venvs using pip.
        cannot be run in parallel as they seem to deadlock.
        '''
        Done = update.cata(Updated, Installed)
        def trans_result(venv: Venv, result: Future) -> Message:
            return Just((Done(venv) if result.success else Error(result.err)).pub)
        @do
        def install_proc(venv: Venv) -> Either[str, SubProcessSync]:
            job = yield venv_facade.install(venv)
            yield Right(SubProcessSync(job, curried(trans_result)(venv)))
        venv_facade = yield EitherState.inspect_f(_.venv_facade)
        yield EitherState.lift(venvs.traverse(install_proc, Either))

    @do
    def install_missing(self) -> EitherState[Env, List[Message]]:
        missing = yield EitherState.inspect_f(_.missing)
        yield self.install_plugins(missing, false)

    @do
    def update_plugins(self, plugins: List[str]) -> EitherState[Env, List[Message]]:
        getter = _.installed if plugins.empty else __.installed_by_name(plugins)
        venvs = yield EitherState.inspect(getter)
        yield (
            EitherState.pure(List(Error(resources.no_plugins_match_for_update(plugins))))
            if venvs.empty else
            self.install_plugins(venvs, true)
        )

    @do
    def activate_venv(self, vim: NvimFacade, venv: Venv) -> Either[str, Activated]:
        host = PluginHost(vim)
        channel = yield host.start(venv)
        yield Right(Activated(venv, channel))

    @do
    def activate_multi(self, venvs: List[Venv]) -> EitherState[Env, List[Message]]:
        vim = yield EitherState.inspect(_.vim)
        active = yield EitherState.inspect(_.active)
        already_active, inactive = venvs.split(active.contains)
        aa_msgs = already_active / AlreadyActive
        activated_msgs = inactive / L(self.activate_venv)(vim, _) / __.value_or(Error)
        yield EitherState.pure(aa_msgs + activated_msgs)

    @do
    def activate_by_names(self, plugins: List[str]) -> EitherState[Env, List[Message]]:
        getter = _.installed if plugins.empty else __.installed_by_name(plugins)
        venvs = yield EitherState.inspect(getter)
        yield (
            EitherState.pure(List(Error(resources.no_plugins_match_for_activation(plugins))))
            if venvs.empty else
            self.activate_multi(venvs)
        )

    def activate_all(self) -> EitherState[Env, List[Message]]:
        return self.activate_by_names(List())

    @do
    def activate_newly_installed(self) -> EitherState[Env, List[Message]]:
        new = yield EitherState.inspect(_.inactive)
        yield self.activate_multi(new)

    @do
    def define_handlers(self, venv: Venv, channel: int) -> NvimIO[List[DefinedHandler]]:
        name = venv.name
        cname = camelcaseify(name)
        rpc_handlers_fun = f'{cname}RpcHandlers'
        handlers_spec = RpcHandlerSpec.fun(1, rpc_handlers_fun, dict())
        handler_rpc = yield define_handler(channel, handlers_spec, name, venv.plugin_path)
        result = yield NvimIO.call_once_defined(rpc_handlers_fun, timeout=3)
        handler_specs = Lists.wrap(result).flat_map(RpcHandlerSpec.decode)
        handlers = yield handler_specs.traverse(L(define_handler)(channel, _, name, venv.plugin_path), NvimIO)
        yield NvimIO.pure(handlers.cons(handler_rpc))


class CoreTransitions(ChromatinTransitions):

    @property
    def funcs(self) -> PluginFunctions:
        return PluginFunctions()

    @trans.multi(Start)
    def stage_i(self) -> State[Env, List[Message]]:
        return List(io(__.vars.set_p('started', True)), io(__.runtime('chromatin/plugins')))

    @trans.one(AddPlugin, trans.st, trans.m)
    @do
    def add_plugin(self) -> State[Env, Maybe[Message]]:
        init = yield State.inspect(_.want_init)
        spec = self.msg.spec
        name = self.msg.options.get('name') | spec
        yield State.modify(__.add_plugin(name, spec))
        yield State.pure(init.m(SetupPlugins().at(.75)))

    @trans.one(ShowPlugins, trans.st)
    @do
    def show_plugins(self) -> State[Env, Message]:
        venv_dir = yield State.inspect(_.venv_dir)
        venv_dir_msg = f'virtualenv dir: {venv_dir.value}'
        yield State.pure(Info(self.data.show_plugins.cons(venv_dir_msg).join_lines))

    @trans.multi(SetupPlugins)
    def setup_plugins(self) -> List[Message]:
        return List(SetupVenvs(), InstallMissing().at(.9).pub, PostSetup().at(.95).pub)

    @trans.multi(SetupVenvs, trans.est)
    def setup_venvs(self) -> EitherState[Env, List[Message]]:
        return self.funcs.setup_venvs()

    @trans.multi(InstallMissing, trans.est)
    def install_missing(self) -> EitherState[Env, List[Message]]:
        return self.funcs.install_missing()

    @trans.multi(Installed, trans.st)
    def installed(self) -> State[Env, List[Message]]:
        venv = self.msg.venv
        return State.pure(List(IsInstalled(venv), Info(resources.installed_plugin(venv.name))))

    @trans.multi(Updated, trans.st)
    def updated(self) -> State[Env, List[Message]]:
        venv = self.msg.venv
        return State.pure(List(Reboot(venv), Info(resources.updated_plugin(venv.name))))

    @trans.unit(IsInstalled, trans.st)
    def is_installed(self) -> State[Env, None]:
        return State.modify(__.add_installed(self.msg.venv))

    @trans.multi(PostSetup, trans.est)
    def post_setup(self) -> EitherState[Env, List[Message]]:
        return self.funcs.activate_newly_installed()

    @trans.unit(AddVenv, trans.st)
    def add_venv(self) -> State[Env, None]:
        return State.modify(__.add_venv(self.msg.venv))

    @trans.multi(Activate, trans.est)
    def activate(self) -> EitherState[Env, List[Message]]:
        return self.funcs.activate_by_names(self.msg.plugins)

    @trans.one(Activated, trans.st)
    @do
    def activated(self) -> State[Env, Message]:
        self.log.debug(f'activated {self.msg.venv}')
        venv = self.msg.venv
        @do
        def io() -> NvimIO[None]:
            yield self.funcs.define_handlers(venv, self.msg.channel)
            yield self.vim.runtime(f'chromatin/{venv.name}/*')
        yield State.modify(__.activate_venv(venv))
        yield State.pure(NvimIOTask(io()))

    @trans.multi(UpdatePlugins, trans.est)
    def update_plugins(self) -> State[Env, List[Message]]:
        return self.funcs.update_plugins(self.msg.plugins)


class Plugin(ChromatinComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
