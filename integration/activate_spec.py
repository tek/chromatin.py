import abc
import shutil
from typing import Callable, TypeVar

from kallikrein import Expectation, kf
from kallikrein.matchers.maybe import be_just
from kallikrein.matchers.end_with import end_with
from kallikrein.matchers.comparison import not_equal, greater
from kallikrein.matchers.either import be_right

from amino.test.path import base_dir
from amino import Path, Just, _, L, List

from ribosome.test.integration.klk import later

from chromatin.util import resources
from chromatin.plugins.core.messages import AlreadyActive, Deactivated, Deactivate, Activated
from chromatin.plugin import RpluginSpec

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


def ensure_venv(f: Callable[[AS], Expectation]) -> Callable[[AS], Expectation]:
    def wrap(self: AS) -> Expectation:
        venvs = self.setup_venvs(Just(self.venvs_path))
        create = self.names.exists(lambda a: not self.venv_path(a).exists())
        if create:
            self.remove()
        def setup(venv: str) -> RpluginSpec:
            return self.setup_one(venv, Just(self.venvs_path))
        plugins = self.names / setup
        self.cmd_sync('CrmSetupPlugins')
        for plugin in plugins:
            self.venv_existent(venvs, plugin, 20)
            self.package_installed(venvs, plugin)
        self.check_exists()
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

    @ensure_venv
    def cmd_parameter(self) -> Expectation:
        self.vim.cmd_sync('FlagArgTest 1')
        return self._log_line(-1, be_just(end_with('success 1')))

    @ensure_venv
    def autocmd(self) -> Expectation:
        self.vim.doautocmd('VimEnter')
        return self._log_line(-1, be_just(end_with('autocmd works')))

    @ensure_venv
    def config(self) -> Expectation:
        later(self.command_exists('FlagConfTest'))
        self.var_becomes('flagellum_value', 'success')
        self.vim.cmd_sync('FlagConfTest')
        return self._log_line(-1, be_just(end_with('success')))

    @ensure_venv
    def update(self) -> Expectation:
        self.cmd_sync('CrmUpdate')
        return self._log_line(-1, be_just(resources.updated_plugin(self.name)))

    @ensure_venv
    def twice(self) -> Expectation:
        self.cmd_sync('CrmActivate')
        return self.seen_message(AlreadyActive)

    @ensure_venv
    def deactivate(self) -> Expectation:
        self.seen_message(Activated)
        plug_channel = lambda: self.state.active.head / _.channel | -1
        later(kf(plug_channel).must(not_equal(-1)))
        channel = plug_channel()
        pid = L(self.vim.call)('jobpid', channel)
        later(kf(pid).must(be_right(greater(0))))
        self.cmd_sync('CrmDeactivate')
        self.seen_message(Deactivate)
        self.seen_message(Deactivated)
        self.command_exists_not('FlagTest')
        return kf(pid).must(be_right(0))


class ActivateTwoSpec(ActivateSpec):
    '''run initialization stages in sequence $stages
    '''

    @property
    def names(self) -> List[str]:
        return List('flagellum', 'cilia')

    def check_exists(self) -> Expectation:
        return later(self.plug_exists('Flag') & self.plug_exists('Cil'))

    @ensure_venv
    def stages(self) -> Expectation:
        self.names % (lambda a: self._log_contains(end_with(f'{a} initialized')))
        return self.var_is('flag', 2) & self.var_is('cil', 1)


class ActivateMiscSpec(ActivateSpec):

    @property
    def name(self) -> str:
        return 'proteome'

    @ensure_venv
    def proteome(self) -> Expectation:
        self._init()
        return later(self.command_exists('ProAdd'))

__all__ = ('ActivateFlagSpec', 'ActivateTwoSpec')
