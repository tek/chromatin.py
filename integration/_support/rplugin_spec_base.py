from typing import Tuple, Any, cast

from amino.test import temp_dir

from kallikrein import Expectation, kf
from kallikrein.matchers.typed import have_type
from amino.test.path import fixture_path
from amino import Maybe, Path, Nothing

from ribosome.test.integration.klk import later

from chromatin.venvs import VenvFacade, VenvExistent
from chromatin.plugin import RpluginSpec
from chromatin.venv import Venv

from integration._support.base import ChromatinPluginIntegrationSpec


class RpluginSpecBase(ChromatinPluginIntegrationSpec):

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.vars.set_p('autostart', False)
        self.vim.vars.set_p('autoreboot', False)
        self.vim.vars.set_p('handle_crm', False)

    def command_exists(self, name: str, **kw) -> Expectation:
        return later(kf(self.vim.command_exists, name).true, **kw)

    def command_exists_not(self, name: str, **kw: Any) -> Expectation:
        return later(kf(self.vim.command_exists, name).false, **kw)

    def plug_exists(self, name: str, **kw: Any) -> Expectation:
        return self.command_exists(f'{name}Test', **kw)

    def venv_existent(self, venvs: VenvFacade, plugin: RpluginSpec, timeout: float=None) -> Expectation:
        return later(kf(venvs.check, plugin).must(have_type(VenvExistent)), timeout=timeout, intval=.5)

    def package_installed(self, venvs: VenvFacade, plugin: RpluginSpec) -> Expectation:
        return later(
            self.venv_existent(venvs, plugin) & kf(venvs.package_installed, venvs.check(plugin).venv).true, 20, .5
        )

    def plugin_venv(self, venvs: VenvFacade, plugin: RpluginSpec) -> Venv:
        later(self.venv_existent(venvs, plugin))
        return cast(VenvExistent, venvs.check(plugin)).venv

    def setup_venvs(self, venv_dir: Maybe[Path] = Nothing) -> VenvFacade:
        rtp = fixture_path('rplugin', 'config', 'rtp')
        self.vim.options.amend_l('runtimepath', rtp)
        dir = venv_dir | temp_dir('rplugin', 'venv')
        self.vim.vars.set_p('venv_dir', str(dir))
        return VenvFacade(dir)

    def setup_one(self, name: str, venv_dir: Maybe[Path] = Nothing) -> RpluginSpec:
        plugin = RpluginSpec(name=name, spec=name)
        path = fixture_path('rplugin', name)
        self.json_cmd_sync('Cram', str(path), name=name)
        return plugin

    def setup_one_with_venvs(self, name: str, venv_dir: Maybe[Path] = Nothing) -> Tuple[VenvFacade, RpluginSpec]:
        venvs = self.setup_venvs(venv_dir)
        plugin = self.setup_one(name, venv_dir)
        return venvs, plugin

    def install_one(self, name: str, venv_dir: Maybe[Path] = Nothing) -> Tuple[Venv, RpluginSpec]:
        venvs, plugin = self.setup_one_with_venvs(name, venv_dir)
        self.cmd('CrmSetupPlugins')
        self.venv_existent(venvs, plugin)
        self.package_installed(venvs, plugin)
        return venvs, self.plugin_venv(venvs, plugin), plugin

    def activate_one(self, name: str, prefix: str) -> Venv:
        venvs, venv, plugin = self.install_one(name)
        self.cmd('CrmActivate')
        later(self.plug_exists(prefix))
        return venv

__all__ = ('RpluginSpecBase',)
