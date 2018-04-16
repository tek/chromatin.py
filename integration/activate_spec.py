import abc
import shutil
from typing import Callable, TypeVar

from kallikrein import Expectation, kf
from kallikrein.matchers.maybe import be_just
from kallikrein.matchers.end_with import end_with
from kallikrein.matchers.comparison import not_equal, greater
from kallikrein.matchers.either import be_right
from kallikrein.matchers import equal

from amino.test.path import base_dir
from amino import Path, Just, _, L, List, do, Do

from ribosome.test.integration.klk import later
from ribosome.nvim.api.command import nvim_command, doautocmd
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.function import nvim_call_tpe

from chromatin.util import resources
from chromatin.model.rplugin import Rplugin

from integration._support.rplugin_spec_base import RpluginSpecBase


class ActivateSpec(RpluginSpecBase):

    @abc.abstractproperty
    def names(self) -> List[str]:
        ...

    @abc.abstractmethod
    def check_exists(self) -> Expectation:
        ...

    @property
    def venvs_path(self) -> Path:
        return base_dir().parent / 'temp' / 'venv'

    def venv_path(self, name: str) -> Path:
        return self.venvs_path / name

    def remove(self) -> None:
        shutil.rmtree(str(self.venvs_path), ignore_errors=True)
        self.venvs_path.mkdir(parents=True, exist_ok=True)


AS = TypeVar('AS', bound=ActivateSpec)


@do(NvimIO[None])
def setup_venvs(self: AS) -> Do:
    self.command_exists('Cram')
    venvs = yield self.setup_venv_dir(Just(self.venvs_path))
    create = self.names.exists(lambda a: not self.venv_path(a).exists())
    if create:
        self.remove()
    def setup(venv: str) -> NvimIO[Rplugin]:
        return self.setup_one(venv, Just(self.venvs_path))
    plugins = yield self.names.traverse(setup, NvimIO)
    yield nvim_command('CrmSetupPlugins')
    self._wait(1)
    for plugin in plugins:
        self.venv_existent(venvs, plugin, 30)
        self.package_installed(venvs, plugin)
    self.check_exists()


def cached_venvs(f: Callable[[AS], Expectation]) -> Callable[[AS], Expectation]:
    def wrap(self: AS) -> Expectation:
        setup_venvs(self).unsafe(self.vim)
        return f(self)
    return wrap


class ActivateFlagSpec(ActivateSpec):
    '''activate and deactivate plugin hosts
    test command with a parameter $cmd_parameter
    execute autocommand $autocmd
    load plugin config from `rtp/chromatin/flagellum` after activation $config
    update a plugin $update
    don't start two hosts if `SetupPlugins` runs again $twice
    deactivate a plugin $deactivate
    '''

    @property
    def name(self) -> str:
        return 'flagellum'

    @property
    def names(self) -> List[str]:
        return List(self.name)

    def check_exists(self) -> Expectation:
        return later(self.plug_exists('Flag'))

    @cached_venvs
    def cmd_parameter(self) -> Expectation:
        nvim_command('FlagArgTest', 1).unsafe(self.vim)
        return self._log_line(-1, be_just(end_with('success 1')))

    @cached_venvs
    def autocmd(self) -> Expectation:
        doautocmd('VimEnter').unsafe(self.vim)
        return self._log_line(-1, be_just(end_with('autocmd works')))

    @cached_venvs
    def config(self) -> Expectation:
        self.var_becomes('flagellum_value', 'success')
        nvim_command('FlagConfTest').unsafe(self.vim)
        return self._log_line(-1, be_just(end_with('success')))

    @cached_venvs
    def update(self) -> Expectation:
        nvim_command('CrmUpdate').unsafe(self.vim)
        return self._log_line(-1, be_just(end_with(resources.updated_plugin(self.name))))

    @cached_venvs
    def twice(self) -> Expectation:
        nvim_command('CrmActivate').unsafe(self.vim)
        return self._log_line(-1, be_just(end_with(resources.already_active(List(self.name)))))

    # FIXME channel is not being shut down ???
    @cached_venvs
    def deactivate(self) -> Expectation:
        self.seen_program('setup_plugins')
        plug_channel: Callable[[], int] = lambda: self.state.active.head / _.channel | -1
        later(kf(plug_channel).must(not_equal(-1)))
        channel = plug_channel()
        pid = lambda: nvim_call_tpe(int, 'jobpid', channel).unsafe(self.vim)
        later(kf(pid).must(be_right(greater(0))))
        nvim_command('CrmDeactivate').unsafe(self.vim)
        self.seen_program('deactivate')
        return (
            self.command_exists_not('FlagTest') &
            self.var_becomes('flagellum_quit', 1) &
            later(kf(pid).must(equal(0)))
        )


class ActivateTwoSpec(ActivateSpec):
    '''run initialization stages in sequence $stages
    '''

    @property
    def names(self) -> List[str]:
        return List('flagellum', 'cilia')

    def check_exists(self) -> Expectation:
        return later(self.plug_exists('Flag') & self.plug_exists('Cil'))

    @cached_venvs
    def stages(self) -> Expectation:
        self.names % (lambda a: self._log_contains(end_with(f'{a} initialized')))
        return self.var_becomes('flag', 2) & self.var_is('cil', 1)


class ActivateMiscSpec(ActivateSpec):

    @property
    def name(self) -> str:
        return 'proteome'

    @cached_venvs
    def proteome(self) -> Expectation:
        self._init()
        return later(self.command_exists('ProAdd'))


__all__ = ('ActivateFlagSpec', 'ActivateTwoSpec')
