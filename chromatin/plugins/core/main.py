from chromatin.state import ChromatinTransitions, ChromatinComponent
from chromatin.plugins.core.messages import (AddPlugin, ShowPlugins, StageI, SetupPlugins, SetupVenvs, InstallMissing,
                                             AddVenv, IsInstalled, Activated, StageII, PostSetup, Installed,
                                             UpdatePlugins, Updated, Reboot, Activate)
from chromatin.venvs import VenvExistent
from chromatin.env import Env
from chromatin.venv import Venv
from chromatin.logging import Logging
from chromatin.host import PluginHost
from chromatin.util import resources

from amino.state import State, EitherState
from amino import __, do, _, Either, L, Just, Future, List, Right, Boolean
from amino.util.string import camelcaseify
from amino.boolean import true, false

from ribosome.machine import Message
from ribosome.machine.base import io, RunIOsParallel, SubProcessSync
from ribosome.machine.transition import Error
from ribosome.machine import trans
from ribosome.nvim import NvimFacade
from ribosome.machine.messages import Info
from ribosome.rpc import define_handler, RpcHandlerSpec


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
        venv_facade = yield EitherState.inspect_f(_.venv_facade)
        msgs = venvs / (lambda v: SubProcessSync(venv_facade.install(v), L(trans_result)(v, _)))
        yield EitherState.pure(msgs)

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
        yield host.start(venv)
        yield host.require(venv)
        yield Right(Activated(venv))

    @do
    def activate_multi(self, venvs: List[Venv]) -> EitherState[Env, List[Message]]:
        vim = yield EitherState.inspect(_.vim)
        yield EitherState.pure(venvs / L(self.activate_venv)(vim, _) / __.value_or(Error))

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


class CoreTransitions(ChromatinTransitions):

    @property
    def funcs(self) -> PluginFunctions:
        return PluginFunctions()

    @trans.one(StageI)
    def stage_i(self) -> Message:
        return io(__.vars.set_p('started', True))

    @trans.multi(StageII, trans.st)
    @do
    def stage_ii(self) -> State[Env, List[Message]]:
        init = yield State.inspect(_.want_init)
        yield State.pure(List(SetupPlugins()) if init else List())

    @trans.unit(AddPlugin, trans.st)
    def add_plugin(self) -> State[Env, None]:
        spec = self.msg.spec
        name = self.msg.options.get('name') | spec
        return State.modify(__.add_plugin(name, spec))

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
        return self.funcs.activate_all(self.msg.plugins)

    @trans.unit(Activated, trans.st)
    def activated(self) -> State[Env, None]:
        self.log.debug(f'activated {self.msg.venv}')
        venv = self.msg.venv
        cname = camelcaseify(venv.name)
        spec = RpcHandlerSpec.cmd(1, f'{cname}SetupRpc', dict())
        define_handler(self.vim, venv.name, spec, venv.plugin_path)
        self.vim.cmd_sync(f'{cname}SetupRpc', verbose=True)
        self.vim.runtime(f'chromatin/{venv.name}/*')
        return State.modify(__.activate_venv(venv))

    @trans.multi(UpdatePlugins, trans.est)
    def update_plugins(self) -> State[Env, List[Message]]:
        return self.funcs.update_plugins(self.msg.plugins)


class Plugin(ChromatinComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
