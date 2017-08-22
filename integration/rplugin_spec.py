from kallikrein import Expectation, kf
from kallikrein.matchers.either import be_right
from kallikrein.matchers.typed import have_type

from amino.test.path import fixture_path
from amino.test import temp_dir

from ribosome.test.integration.klk import later

from chromatin.venvs import VenvFacade, VenvExistent
from chromatin.plugin import VimPlugin

from integration._support.base import ChromatinPluginIntegrationSpec


class RpluginSpec(ChromatinPluginIntegrationSpec):
    '''launch rplugins from venvs
    two plugins in separate venvs $two
    '''

    def two(self) -> Expectation:
        name1 = 'flagellum'
        name2 = 'cilia'
        dir = temp_dir('rplugin', 'venv')
        venvs = VenvFacade(dir)
        plugin1 = VimPlugin(name=name1, spec=name1)
        plugin2 = VimPlugin(name=name2, spec=name2)
        self.vim.vars.set_p('venv_dir', str(dir))
        path1 = fixture_path('rplugin', name1)
        path2 = fixture_path('rplugin', name2)
        self.vim.cmd_sync(f'''Cram {path1} {{ 'name': '{name1}' }}''')
        self._wait(.1)
        self.vim.cmd_sync(f'''Cram {path2} {{ 'name': '{name2}' }}''')
        self._wait(.1)
        self.vim.cmd_sync('CrmSetupPlugins')
        self._wait(.1)
        later(kf(venvs.check, plugin1).must(have_type(VenvExistent)), intval=.5)
        self._wait(.1)
        later(kf(venvs.package_installed, venvs.check(plugin1).venv).true, 20, .5)
        self._wait(.1)
        later(kf(venvs.package_installed, venvs.check(plugin2).venv).true, 20, .5)
        self._wait(.1)
        self.vim.cmd('CrmActivateAll')
        self._wait(.1)
        exp = lambda n: kf(self.vim.call, 'exists', f':{n}Test').must(be_right(2))
        return later(exp('Flag') & exp('Cil'))

__all__ = ('RpluginSpec',)
