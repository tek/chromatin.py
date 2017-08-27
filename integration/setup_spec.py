from kallikrein import Expectation, k
from kallikrein.matchers.length import have_length

from amino.test.path import fixture_path
from amino.test import temp_dir
from amino import List, Path

from ribosome.test.integration.klk import later

from chromatin.venvs import VenvFacade
from chromatin.plugin import VimPlugin
from chromatin.plugins.core.messages import SetupPlugins, SetupVenvs, InstallMissing, PostSetup, Installed

from integration._support.rplugin_spec import RpluginSpec


class TwoExplicitSpec(RpluginSpec):
    '''two plugins in separate venvs
    read plugin config from `g:chromatin_rplugins` $read_conf
    setup venvs $setup_venvs
    bootstrap and activate, explicit initialization $bootstrap
    '''

    name1 = 'flagellum'
    name2 = 'cilia'
    path1 = fixture_path('rplugin', name1)
    path2 = fixture_path('rplugin', name2)

    @property
    def dir(self) -> Path:
        return temp_dir('rplugin', 'venv')

    @property
    def plugin1(self) -> VimPlugin:
        return VimPlugin(name=self.name1, spec=self.name1)

    @property
    def plugin2(self) -> VimPlugin:
        return VimPlugin(name=self.name2, spec=self.name2)

    @property
    def venvs(self) -> VenvFacade:
        return VenvFacade(self.dir)

    def _pre_start(self) -> None:
        super()._pre_start()
        plugins = List(
            dict(name=self.name1, spec=str(self.path1)),
            dict(name=self.name2, spec=str(self.path2)),
        )
        self.vim.vars.set_p('rplugins', plugins)
        self.vim.vars.set_p('venv_dir', str(self.dir))

    def read_conf(self) -> Expectation:
        return k(self.state.plugins).must(have_length(2))

    def setup_venvs(self) -> Expectation:
        self.cmd_sync('CrmPlug core setup_venvs')
        self.seen_message(SetupVenvs)
        self._wait(5)
        print(self.message_log())
        return self.venv_existent(self.venvs, self.plugin1) & self.venv_existent(self.venvs, self.plugin2)

    def bootstrap(self) -> Expectation:
        self.cmd_sync('CrmSetupPlugins')
        self.seen_message(SetupVenvs)
        self.venv_existent(self.venvs, self.plugin1)
        self.seen_message(InstallMissing)
        self.package_installed(self.venvs, self.plugin1)
        self.package_installed(self.venvs, self.plugin2)
        self.seen_message(PostSetup)
        self.cmd_sync('CrmActivate')
        return later(self.plug_exists('Flag') & self.plug_exists('Cil'), timeout=2)


class AutostartSpec(RpluginSpec):
    '''automatic initialization $auto
    '''

    def auto(self) -> Expectation:
        self.vim.vars.set_p('autostart', True)
        venvs, plugin = self.setup_one('flagellum')
        self.seen_message(SetupPlugins)
        self.venv_existent(venvs, plugin, timeout=4)
        self.package_installed(venvs, plugin)
        return later(self.plug_exists('Flag'))

__all__ = ('TwoExplicitSpec', 'AutostartSpec')
