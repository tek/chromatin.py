from chromatin.state import ChromatinTransitions, ChromatinComponent
from chromatin.plugins.core.messages import (AddPlugin, ShowPlugins, Start, SetupPlugins, SetupVenvs, InstallMissing,
                                             AddVenv, IsInstalled, Activated, PostSetup, Installed, UpdatePlugins,
                                             Updated, Reboot, Activate, AlreadyActive, ReadConf, Deactivate,
                                             Deactivated, DefinedHandlers)
from chromatin.venvs import VenvExistent
from chromatin.env import Env
from chromatin.venv import Venv, ActiveVenv
from chromatin.logging import Logging
from chromatin.host import PluginHost
from chromatin.util import resources
from chromatin.plugin import VimPlugin

from amino.state import State, EitherState
from amino import __, do, _, Either, L, Just, Future, List, Right, Boolean, Lists, Maybe, curried, Nothing
from amino.util.string import camelcaseify
from amino.boolean import true, false
from amino.list import Nil

from ribosome.machine import Message
from ribosome.machine.base import io, RunIOsParallel, SubProcessSync
from ribosome.machine.transition import Error
from ribosome.machine import trans
from ribosome.nvim import NvimFacade, NvimIO
from ribosome.machine.messages import Info, RunNvimIO
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
        channel, pid = yield host.start(venv)
        yield Right(Activated(ActiveVenv(venv=venv, channel=channel, pid=pid)))

    @do
    def activate_multi(self, venvs: List[Venv]) -> EitherState[Env, List[Message]]:
        vim = yield EitherState.inspect(_.vim)
        active = yield EitherState.inspect(_.active_venvs)
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

    def deactivate_venv(self, venv: ActiveVenv) -> State[Env, RunNvimIO]:
        def undef(spec: RpcHandlerSpec) -> NvimIO[str]:
            return NvimIO.cmd(spec.undef_cmdline, verbose=True)
        @do
        def run(env: Env) -> NvimIO[List[Deactivated]]:
            handlers = (env.handlers_for(venv.name) | Nil) / _.spec
            yield NvimIO.call('jobstop', venv.channel)
            yield handlers.traverse(undef, NvimIO)
            yield NvimIO.pure(List(Deactivated(venv)))
        return State.inspect(run) / RunNvimIO

    def deactivate_multi(self, venvs: List[ActiveVenv]) -> State[Env, List[RunNvimIO]]:
        return venvs.traverse(self.deactivate_venv, State)

    @do
    def deactivate_by_names(self, plugins: List[str]) -> State[Env, List[Message]]:
        getter = _.active if plugins.empty else __.active_by_name(plugins)
        venvs = yield State.inspect(getter)
        yield (
            State.pure(List(Error(resources.no_plugins_match_for_deactivation(plugins))))
            if venvs.empty else
            self.deactivate_multi(venvs)
        )

    def activate_all(self) -> EitherState[Env, List[Message]]:
        return self.activate_by_names(List())

    @do
    def activate_newly_installed(self) -> EitherState[Env, List[Message]]:
        new = yield EitherState.inspect(_.inactive)
        yield self.activate_multi(new)

    @do
    def define_handlers(self, active_venv: ActiveVenv) -> NvimIO[List[DefinedHandler]]:
        venv = active_venv.venv
        name = venv.name
        channel = active_venv.channel
        cname = camelcaseify(name)
        rpc_handlers_fun = f'{cname}RpcHandlers'
        handlers_spec = RpcHandlerSpec.fun(1, rpc_handlers_fun, dict())
        handler_rpc = yield define_handler(channel, handlers_spec, name, venv.plugin_path)
        result = yield NvimIO.call_once_defined(rpc_handlers_fun, timeout=3)
        handler_specs = Lists.wrap(result).flat_map(RpcHandlerSpec.decode)
        handlers = yield handler_specs.traverse(L(define_handler)(channel, _, name, venv.plugin_path), NvimIO)
        yield NvimIO.pure(handlers.cons(handler_rpc))

    @do
    def add_plugins(self, plugins: List[VimPlugin]) -> EitherState[Env, Maybe[Message]]:
        yield EitherState.modify(__.add_plugins(plugins))
        init = yield EitherState.inspect(_.want_init)
        yield EitherState.pure(init.m(SetupPlugins()))

    @do
    def read_conf(self) -> EitherState[Env, Maybe[Message]]:
        vim = yield EitherState.inspect(_.vim)
        plugins = vim.vars.pl('rplugins').flat_map(__.traverse(VimPlugin.from_config, Either))
        yield (
            EitherState.pure(Nothing)
            if plugins.exists(_.empty) else
            plugins.map(self.add_plugins).value_or(lambda a: EitherState.pure(Just(Error(a))))
        )


class CoreTransitions(ChromatinTransitions):

    @property
    def funcs(self) -> PluginFunctions:
        return PluginFunctions()

    @trans.multi(Start)
    def stage_i(self) -> State[Env, List[Message]]:
        return List(io(__.vars.set_p('started', True)), io(__.vars.ensure_p('rplugins', [])), ReadConf().at(0.6))

    @trans.one(ReadConf, trans.est, trans.m)
    def read_conf(self) -> EitherState[Env, Maybe[Message]]:
        return self.funcs.read_conf()

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

    @trans.multi(Deactivate, trans.st)
    def deactivate(self) -> State[Env, List[Message]]:
        return self.funcs.deactivate_by_names(self.msg.plugins)

    @trans.one(Activated, trans.st, trans.nio)
    @do
    def activated(self) -> State[Env, NvimIO[Message]]:
        self.log.debug(f'activated {self.msg.venv}')
        active_venv = self.msg.venv
        venv = active_venv.venv
        @do
        def io() -> NvimIO[DefinedHandlers]:
            handlers = yield self.funcs.define_handlers(active_venv)
            yield self.vim.runtime(f'chromatin/{venv.name}/*')
            yield NvimIO.pure(DefinedHandlers(venv, handlers))
        yield State.modify(__.activate_venv(active_venv))
        yield State.pure(io())

    @trans.unit(DefinedHandlers, trans.st)
    def defined_handlers(self) -> State[Env, None]:
        return State.modify(__.add_handlers(self.msg.venv, self.msg.handlers))

    @trans.multi(UpdatePlugins, trans.est)
    def update_plugins(self) -> State[Env, List[Message]]:
        return self.funcs.update_plugins(self.msg.plugins)

    @trans.unit(AlreadyActive)
    def already_active(self) -> None:
        pass


class Plugin(ChromatinComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
