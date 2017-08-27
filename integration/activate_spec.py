import abc
import shutil
from typing import Callable

from kallikrein import Expectation
from kallikrein.matchers.maybe import be_just
from kallikrein.matchers.end_with import end_with

from amino.test.path import base_dir
from amino import Path, Just

from ribosome.test.integration.klk import later

from chromatin.util import resources
from chromatin.plugins.core.messages import AlreadyActive

from integration._support.rplugin_spec import RpluginSpec


class ActivateSpec(RpluginSpec):

    @abc.abstractproperty
    def name(self) -> str:
        ...

    @property
    def venvs_path(self) -> Path:
        return base_dir().parent / 'temp' / 'venv'

    @property
    def venv_path(self) -> Path:
        return self.venvs_path / self.name

    def setup_venv(self) -> None:
        shutil.rmtree(self.venv_path, ignore_errors=True)
        self.venvs_path.mkdir(parents=True, exist_ok=True)
        venv, venvs, plugin = self.install_one(self.name, Just(self.venvs_path))


def ensure_venv(f: Callable[[ActivateSpec], Expectation]) -> Callable[[ActivateSpec], Expectation]:
    def wrap(self: ActivateSpec) -> Expectation:
        if not self.venv_path.exists():
            self.setup_venv()
        else:
            self.setup_one(self.name, Just(self.venvs_path))
        self.cmd('CrmSetupPlugins')
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
    '''

    @property
    def name(self) -> str:
        return 'flagellum'

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
        self._var_becomes('flagellum_value', 'success')
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


class ActivateMiscSpec(ActivateSpec):

    @property
    def name(self) -> str:
        return 'proteome'

    @ensure_venv
    def proteome(self) -> Expectation:
        self._init()
        return later(self.command_exists('ProAdd'))

__all__ = ('ActivateFlagSpec',)
