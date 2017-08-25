from kallikrein import Expectation

from amino.test.path import fixture_path
from amino.test import temp_dir

from ribosome.test.integration.klk import later

from chromatin.venvs import VenvFacade
from chromatin.plugin import VimPlugin

from integration._support.rplugin_spec import RpluginSpec


class SetupSpec(RpluginSpec):
    '''bootstrap and activate plugins in venvs
    two plugins in separate venvs, explicit initialization $two_explicit
    automatic initialization $auto
    '''

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

    def auto(self) -> Expectation:
        venvs, plugin = self.setup_one('flagellum')
        self.vim.doautocmd('VimEnter')
        self.venv_existent(venvs, plugin)
        self.package_installed(venvs, plugin)
        return later(self.plug_exists('Flag'))

__all__ = ('SetupSpec',)
