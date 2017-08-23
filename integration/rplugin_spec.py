from typing import Tuple

from kallikrein import Expectation, kf
from kallikrein.matchers.either import be_right
from kallikrein.matchers.typed import have_type
from kallikrein.matchers.maybe import be_just

from amino.test.path import fixture_path
from amino.test import temp_dir

from ribosome.test.integration.klk import later

from chromatin.venvs import VenvFacade, VenvExistent
from chromatin.plugin import VimPlugin
from chromatin.util import resources

from integration._support.base import ChromatinPluginIntegrationSpec


class RpluginSpec(ChromatinPluginIntegrationSpec):
    '''launch rplugins from venvs
    two plugins in separate venvs, explicit initialization $two_explicit
    automatic initialization $auto
    update a plugin $update
    '''

    def plug_exists(self, name: str) -> Expectation:
        return kf(self.vim.call, 'exists', f':{name}Test').must(be_right(2))

    def venv_existent(self, venvs: VenvFacade, plugin: VimPlugin) -> Expectation:
        return later(kf(venvs.check, plugin).must(have_type(VenvExistent)), intval=.5)

    def package_installed(self, venvs: VenvFacade, plugin: VimPlugin) -> Expectation:
        return later(kf(venvs.package_installed, venvs.check(plugin).venv).true, 20, .5)

    def two_explicit(self) -> Expectation:
        self.vim.vars.set_p('autostart', False)
        name1 = 'flagellum'
        name2 = 'cilia'
        dir = temp_dir('rplugin', 'venv')
        venvs = VenvFacade(dir)
        plugin1 = VimPlugin(name=name1, spec=name1)
        plugin2 = VimPlugin(name=name2, spec=name2)
        self.vim.vars.set_p('venv_dir', str(dir))
        path1 = fixture_path('rplugin', name1)
        path2 = fixture_path('rplugin', name2)
        self.cmd_sync(f'''Cram {path1} {{ 'name': '{name1}' }}''')
        self.cmd_sync(f'''Cram {path2} {{ 'name': '{name2}' }}''')
        self.cmd_sync('CrmSetupPlugins')
        self.venv_existent(venvs, plugin1)
        self.package_installed(venvs, plugin1)
        self.package_installed(venvs, plugin2)
        self.cmd('CrmActivate')
        return later(self.plug_exists('Flag') & self.plug_exists('Cil'))

    def setup_one(self) -> Tuple[VenvFacade, VimPlugin]:
        name = 'flagellum'
        dir = temp_dir('rplugin', 'venv')
        venvs = VenvFacade(dir)
        plugin = VimPlugin(name=name, spec=name)
        self.vim.vars.set_p('venv_dir', str(dir))
        path1 = fixture_path('rplugin', name)
        self.json_cmd_sync('Cram', path1, name=name)
        return venvs, plugin

    def auto(self) -> Expectation:
        venvs, plugin = self.setup_one()
        self.vim.doautocmd('VimEnter')
        self.venv_existent(venvs, plugin)
        self.package_installed(venvs, plugin)
        return later(self.plug_exists('Flag'))

    def update(self) -> Expectation:
        venvs, plugin = self.setup_one()
        self.cmd_sync('CrmSetupPlugins')
        self.venv_existent(venvs, plugin)
        self.package_installed(venvs, plugin)
        self.cmd_sync('CrmActivate')
        later(self.plug_exists('Flag'))
        self.cmd_sync('CrmUpdate')
        return self._log_line(-1, be_just(resources.updated_plugin(plugin.name)))

__all__ = ('RpluginSpec',)
