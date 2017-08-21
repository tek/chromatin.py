from chromatin.state import ChromatinTransitions, ChromatinComponent
from chromatin.plugins.core.messages import (AddPlugin, ShowPlugins, StageI, SetupPlugins, SetupVenvs, InstallMissing,
                                             AddVenv, VenvJob, Installed, EnvVenvJob, ActivateAll, Activated, PluginJob)
from chromatin.venvs import VenvFacade, VenvExistent
from chromatin.env import Env
from chromatin.venv import Venv
from chromatin.logging import Logging
from chromatin.host import PluginHost

from amino.state import IdState, StateT, EitherState
from amino import __, do, _, Either, L, Just, Future, List, Right
from amino.lazy import lazy

from ribosome.machine import may_handle, Message, handle
from ribosome.machine.base import io, RunIOsParallel, SubProcessSync
from ribosome.machine.transition import Error
from ribosome.machine import trans


class PluginFacade(Logging):

    def __init__(self, env: Env, venvs: VenvFacade) -> None:
        self.env = env
        self.venvs = venvs
        self.vim = env.vim

    def install_missing(self) -> Message:
        '''run subprocesses in sequence that install packages into their venvs using pip.
        cannot be run in parallel as they seem to deadlock.
        '''
        def trans_result(venv: Venv, result: Future) -> Message:
            return Just((Installed(venv) if result.success else Error(result.err)).pub)
        return self.env.missing(self.venvs) / (lambda v: SubProcessSync(self.venvs.install(v), L(trans_result)(v, _)))

    @do
    def activate(self, venv: Venv) -> Either[str, Activated]:
        host = PluginHost(self.vim)
        yield host.start(venv)
        yield host.require(venv)
        yield Right(Activated(venv))

    def activate_all(self) -> List[Message]:
        return self.env.installed / self.activate / __.value_or(Error)


class PluginFunctions(Logging):

    @do
    def setup_venvs(self) -> EitherState:
        '''check whether a venv exists for each plugin in the self.env.
        for those that don't, create self.venvs in `g:chromatin_venv_dir`.
        '''
        venv_facade = yield EitherState.inspect_f(_.venv_facade)
        plugins = yield EitherState.inspect(_.plugins)
        jobs = plugins / venv_facade.check
        existent, absent = jobs.split_type(VenvExistent)
        ios = absent / _.plugin / venv_facade.bootstrap / __.map(AddVenv).map(_.pub)
        yield EitherState.pure(existent.map(_.venv).map(Installed).cat(RunIOsParallel(ios)))


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

    @may_handle(ShowPlugins)
    def show_plugins(self) -> Message:
        self.log.info(self.data.show_plugins.join_lines)

    @may_handle(SetupPlugins)
    def setup_plugins(self) -> Message:
        return SetupVenvs(), InstallMissing().at(1.0).pub

    @handle(VenvJob)
    def venv_job(self) -> Message:
        return self.venvs / self.msg.job

    @may_handle(EnvVenvJob)
    def env_venv_job(self) -> Message:
        return VenvJob(lambda venvs: IdState.inspect(L(self.msg.job)(_, venvs)))

    @may_handle(PluginJob)
    def plugin_job(self) -> Message:
        return EnvVenvJob(L(PluginFacade)(_, _) >> self.msg.job)

    @may_handle(SetupVenvs)
    def setup_venvs(self) -> Message:
        return self.funcs.setup_venvs()

    @may_handle(InstallMissing)
    def install_missing(self) -> Message:
        return PluginJob(__.install_missing())

    @may_handle(Installed)
    def installed(self) -> Message:
        return IdState.modify(__.add_installed(self.msg.venv))

    @may_handle(AddVenv)
    def add_venv(self) -> Message:
        return IdState.modify(__.add_venv(self.msg.venv))

    @may_handle(ActivateAll)
    def activate_all(self) -> Message:
        return PluginJob(__.activate_all())


class Plugin(ChromatinComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
