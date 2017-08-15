from chromatin.state import ChromatinTransitions, ChromatinComponent
from chromatin.plugins.core.messages import (AddPlugin, ShowPlugins, StageI, SetupPlugins, SetupVenvs, InstallMissing,
                                             AddVenv, VenvJob, Installed)
from chromatin.venvs import Venvs, VenvExistent
from chromatin.env import Env
from chromatin.venv import Venv

from amino.state import IdState
from amino import __, Maybe, do, _, Either, L, Lists, Just
from amino.lazy import lazy

from ribosome.machine import may_handle, Message, handle
from ribosome.machine.base import io, RunIOsParallel, RunCorosParallel
from ribosome.process import NvimProcessExecutor
from ribosome.machine.transition import Fatal


class CoreTransitions(ChromatinTransitions):

    @lazy
    def venvs(self) -> Either[str, Venvs]:
        return self.vim.vars.ppath('venv_dir') / Venvs

    @may_handle(StageI)
    def stage_i(self) -> Maybe[Message]:
        return io(__.vars.set_p('started', True))

    @may_handle(AddPlugin)
    def add_plugin(self) -> Message:
        return IdState.modify(__.add_plugin(self.msg.spec))

    @may_handle(ShowPlugins)
    def show_plugins(self) -> Message:
        self.log.info(self.data.show_plugins.join_lines)

    @may_handle(SetupPlugins)
    def setup_plugins(self) -> Message:
        return SetupVenvs(), InstallMissing().at(1.0).pub

    @handle(VenvJob)
    def venv_job(self) -> Message:
        return self.venvs / self.msg.job

    @may_handle(SetupVenvs)
    def setup_venvs(self) -> Message:
        return VenvJob(self._setup_plugins)

    @may_handle(InstallMissing)
    def install_missing(self) -> Message:
        return VenvJob(lambda venvs: IdState.inspect(L(self._install_missing)(_, venvs)))

    @may_handle(Installed)
    def installed(self) -> Message:
        return IdState.modify(__.add_installed(self.msg.venv))

    async def _install_missing(self, env: Env, venvs: Venvs) -> Message:
        executor = NvimProcessExecutor(env.vim)
        async def install(venv: Venv) -> None:
            result = await executor.run(venvs.install(venv))
            return (Installed(venv) if result.success else Fatal(result.err)).pub
        return Just(Lists.wrap([await install(c) for c in env.missing(venvs)]))

    @may_handle(AddVenv)
    def add_venv(self) -> Message:
        return IdState.modify(__.add_venv(self.msg.venv))

    @do
    def _setup_plugins(self, venvs: Venvs) -> IdState:
        plugins = yield IdState.inspect(_.plugins)
        jobs = plugins / venvs.check
        existent, absent = jobs.split_type(VenvExistent)
        ios = absent / _.plugin / venvs.bootstrap / __.map(AddVenv).map(_.pub)
        yield IdState.pure(RunIOsParallel(ios))


class Plugin(ChromatinComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
