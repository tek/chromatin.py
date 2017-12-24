from typing import Tuple, Any, cast

from amino.test import temp_dir

from kallikrein import Expectation, kf
from kallikrein.matchers.typed import have_type
from kallikrein.matchers.either import be_right
from amino.test.path import fixture_path
from amino import Maybe, Path, Nothing

from ribosome.test.integration.klk import later

from chromatin.model.rplugin import Rplugin, RpluginReady, cons_rplugin
from chromatin.model.venv import VenvExistent, Venv
from chromatin.rplugin import check_venv, rplugin_installed

from integration._support.base import DefaultSpec


class RpluginSpecBase(DefaultSpec):

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.vars.set_p('autostart', False)
        self.vim.vars.set_p('autoreboot', False)
        self.vim.vars.set_p('handle_crm', False)
        self.vim.vars.set_p('debug_pythonpath', True)

    def plug_exists(self, name: str, **kw: Any) -> Expectation:
        cmd = f'{name}Test'
        self.command_exists(cmd, **kw)
        return kf(self.cmd_sync, cmd).must(be_right)

    def venv_existent(self, base_dir: Path, rplugin: Rplugin, timeout: float=None) -> Expectation:
        return later(kf(check_venv, base_dir, rplugin).must(have_type(VenvExistent)), timeout=timeout, intval=.5)

    def package_installed(self, base_dir: Path, rplugin: Rplugin) -> Expectation:
        return later(
            self.venv_existent(base_dir, rplugin) &
            kf(rplugin_installed, base_dir, rplugin).must(have_type(RpluginReady)),
            20,
            .5,
        )

    def plugin_venv(self, base_dir: Path, rplugin: Rplugin) -> Venv:
        later(self.venv_existent(base_dir, rplugin))
        return cast(VenvExistent, check_venv(base_dir, rplugin)).venv

    def setup_venvs(self, venv_dir: Maybe[Path] = Nothing) -> Path:
        rtp = fixture_path('rplugin', 'config', 'rtp')
        self.vim.options.amend_l('runtimepath', rtp)
        dir = venv_dir | temp_dir('rplugin', 'venv')
        self.vim.vars.set_p('venv_dir', str(dir))
        return dir

    def setup_one(self, name: str, venv_dir: Maybe[Path]=Nothing) -> Rplugin:
        plugin = cons_rplugin(name, name)
        path = fixture_path('rplugin', name)
        self.cmd_sync('Cram', str(path), name)
        return plugin

    def setup_one_with_venvs(self, name: str, venv_dir: Maybe[Path] = Nothing) -> Tuple[Path, Rplugin]:
        base_dir = self.setup_venvs(venv_dir)
        plugin = self.setup_one(name, venv_dir)
        return base_dir, plugin

    def install_one(self, name: str, venv_dir: Maybe[Path]=Nothing) -> Tuple[Venv, Rplugin]:
        base_dir, plugin = self.setup_one_with_venvs(name, venv_dir)
        self.cmd('CrmSetupPlugins')
        self.venv_existent(base_dir, plugin)
        self.package_installed(base_dir, plugin)
        return base_dir, self.plugin_venv(base_dir, plugin), plugin

    def activate_one(self, name: str, prefix: str) -> Venv:
        base_dir, venv, plugin = self.install_one(name)
        self.cmd('CrmActivate')
        later(self.plug_exists(prefix))
        return venv

__all__ = ('RpluginSpecBase',)
