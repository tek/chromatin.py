from chromatin.state import ChromatinTransitions, ChromatinComponent
from chromatin.plugins.core.messages import (AddPlugin, ShowPlugins, StageI, SetupPlugins, SetupVenvs, InstallMissing,
                                             AddVenv, Installed, ActivateAll, Activated)
from chromatin.venvs import VenvFacade, VenvExistent
from chromatin.env import Env
from chromatin.venv import Venv
from chromatin.logging import Logging
from chromatin.host import PluginHost

from amino.state import IdState, EitherState
from amino import __, do, _, Either, L, Just, Future, List, Right
from amino.lazy import lazy

from ribosome.machine import Message
from ribosome.machine.base import io, RunIOsParallel, SubProcessSync
from ribosome.machine.transition import Error
from ribosome.machine import trans
from ribosome.nvim import NvimFacade


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
        yield EitherState.pure(existent.map(_.venv).map(Installed).cat(RunIOsParallel(ios)))

    @do
    def install_missing(self) -> EitherState[Env, List[Message]]:
        '''run subprocesses in sequence that install packages into their venvs using pip.
        cannot be run in parallel as they seem to deadlock.
        '''
        def trans_result(venv: Venv, result: Future) -> Message:
            return Just((Installed(venv) if result.success else Error(result.err)).pub)
        venv_facade = yield EitherState.inspect_f(_.venv_facade)
        missing = yield EitherState.inspect(__.missing(venv_facade))
        msgs = missing / (lambda v: SubProcessSync(venv_facade.install(v), L(trans_result)(v, _)))
        yield EitherState.pure(msgs)

    @do
    def activate(self, vim: NvimFacade, venv: Venv) -> Either[str, Activated]:
        host = PluginHost(vim)
        yield host.start(venv)
        yield host.require(venv)
        yield Right(Activated(venv))

    @do
    def activate_all(self) -> EitherState[Env, List[Message]]:
        vim = yield EitherState.inspect(_.vim)
        installed = yield EitherState.inspect(_.installed)
        msgs = installed / L(self.activate)(vim, _) / __.value_or(Error)
        yield EitherState.pure(msgs)


class CoreTransitions(ChromatinTransitions):

    @property
    def funcs(self) -> PluginFunctions:
        return PluginFunctions()

    @lazy
    def venvs(self) -> Either[str, VenvFacade]:
        return self.vim.vars.ppath('venv_dir') / VenvFacade

    @trans.one(StageI)
    def stage_i(self) -> Message:
        return io(__.vars.set_p('started', True))

    @trans.unit(AddPlugin, trans.st)
    def add_plugin(self) -> IdState[Env, None]:
        spec = self.msg.spec
        name = self.msg.options.get('name') | spec
        return IdState.modify(__.add_plugin(name, spec))

    @trans.unit(ShowPlugins)
    def show_plugins(self) -> None:
        self.log.info(self.data.show_plugins.join_lines)

    @trans.multi(SetupPlugins)
    def setup_plugins(self) -> Message:
        return List(SetupVenvs(), InstallMissing().at(1.0).pub)

    @trans.multi(SetupVenvs, trans.est)
    def setup_venvs(self) -> Message:
        return self.funcs.setup_venvs()

    @trans.multi(InstallMissing, trans.est)
    def install_missing(self) -> Message:
        return self.funcs.install_missing()

    @trans.unit(Installed, trans.st)
    def installed(self) -> Message:
        return IdState.modify(__.add_installed(self.msg.venv))

    @trans.unit(AddVenv, trans.st)
    def add_venv(self) -> Message:
        return IdState.modify(__.add_venv(self.msg.venv))

    @trans.multi(ActivateAll, trans.est)
    def activate_all(self) -> Message:
        return self.funcs.activate_all()


class Plugin(ChromatinComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
