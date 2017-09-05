from kallikrein import Expectation, k, kf
from kallikrein.matchers.length import have_length
from kallikrein.matchers.either import be_right
from kallikrein.matchers.maybe import be_just

from amino.test.path import fixture_path, base_dir
from amino.test import temp_dir
from amino import List, Path, _

from ribosome.test.integration.klk import later
from ribosome.machine.messages import UpdateState

from chromatin.venvs import VenvFacade
from chromatin.plugin import RpluginSpec
from chromatin.plugins.core.messages import (SetupPlugins, SetupVenvs, PostSetup, AddVenv, InstallMissing, Installed,
                                             UpdatePlugins, Updated)

from integration._support.rplugin_spec_base import RpluginSpecBase

name1 = 'flagellum'
name2 = 'cilia'
path1 = fixture_path('rplugin', name1)
path2 = fixture_path('rplugin', name2)

plugin1 = RpluginSpec(name=name1, spec=name1)
plugin2 = RpluginSpec(name=name2, spec=name2)

plugins = List(
    dict(name=name1, spec=str(path1)),
    dict(name=name2, spec=str(path2)),
)


class TwoExplicitSpec(RpluginSpecBase):
    '''two plugins in separate venvs
    read plugin config from `g:chromatin_rplugins` $read_conf
    setup venvs $setup_venvs
    bootstrap and activate, explicit initialization $bootstrap
    '''

    @property
    def dir(self) -> Path:
        return temp_dir('rplugin', 'venv')

    @property
    def venvs(self) -> VenvFacade:
        return VenvFacade(self.dir)

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.vars.set_p('rplugins', plugins)
        self.vim.vars.set_p('venv_dir', str(self.dir))

    def read_conf(self) -> Expectation:
        return k(self.state.plugins).must(have_length(2))

    def setup_venvs(self) -> Expectation:
        self.cmd_sync('CrmPlug core setup_venvs')
        self.seen_message(SetupVenvs)
        return self.venv_existent(self.venvs, plugin1) & self.venv_existent(self.venvs, plugin2)

    def bootstrap(self) -> Expectation:
        self.cmd_sync('CrmSetupPlugins')
        self.seen_message(SetupVenvs)
        self.venv_existent(self.venvs, plugin1)
        self.seen_message(InstallMissing)
        self.package_installed(self.venvs, plugin1)
        self.package_installed(self.venvs, plugin2)
        self.seen_message(PostSetup)
        self.cmd_sync('CrmActivate')
        return self.plug_exists('Flag') & self.plug_exists('Cil')


class AutostartAfterAddSpec(RpluginSpecBase):
    '''automatic initialization when using `Cram` $auto_cram
    '''

    def auto_cram(self) -> Expectation:
        self.vim.vars.set_p('autostart', True)
        venvs, plugin = self.setup_one_with_venvs('flagellum')
        self.seen_message(SetupPlugins)
        self.venv_existent(venvs, plugin, timeout=4)
        self.package_installed(venvs, plugin)
        return later(self.plug_exists('Flag'))


class AutostartAtBootSpec(RpluginSpecBase):
    '''automatic initialization at vim startup $startup
    '''

    @property
    def dir(self) -> Path:
        return temp_dir('rplugin', 'venv')

    @property
    def venvs(self) -> VenvFacade:
        return VenvFacade(self.dir)

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.vars.set_p('rplugins', plugins.take(1))
        self.vim.vars.set_p('venv_dir', str(self.dir))
        self.vim.vars.set_p('autostart', True)

    def startup(self) -> Expectation:
        self.seen_message(SetupPlugins)
        self.seen_message(SetupVenvs)
        self.seen_message(AddVenv)
        self.seen_message(InstallMissing)
        self.seen_message(Installed)
        return later(self.plug_exists('Flag'))


class BootstrapSpec(RpluginSpecBase):
    '''auto-install chromatin at boot $bootstrap
    '''

    @property
    def autostart_plugin(self) -> bool:
        return False

    @property
    def pkg_dir(self) -> Path:
        return base_dir().parent

    @property
    def dir(self) -> Path:
        return self.pkg_dir / 'temp' / 'venv'

    @property
    def venvs(self) -> VenvFacade:
        return VenvFacade(self.dir)

    def _pre_start(self) -> None:
        super()._pre_start()
        plugins = List(dict(name=name1, spec=str(path1)))
        self.vim.options.amend_l('runtimepath', str(self.pkg_dir))
        self.vim.vars.set_p('autobootstrap', False)
        self.vim.vars.set_p('venv_dir', str(self.dir))
        self.vim.vars.set_p('pip_req', str(self.pkg_dir))
        self.vim.vars.set_p('rplugins', plugins)

    def bootstrap(self) -> Expectation:
        self.command_exists_not('Cram')
        self.vim.runtime('plugin/bootstrap')
        self.cmd('BootstrapChromatin')
        self.command_exists('ChromatinStage1', timeout=20)
        self.cmd_sync('ChromatinStage1')
        self.cmd_sync('CrmSetupPlugins')
        return self.plug_exists('Flag', timeout=15)


# TODO move to `ActivateSpec`, change `ensure_env` to move the temp venv to `_temp` instead of using the `temp` dir
# directly
class RebootSpec(RpluginSpecBase):
    '''deactivate and reactivate a plugin $reboot
    '''

    def reboot(self) -> Expectation:
        name = 'flagellum'
        self.activate_one(name, 'Flag')
        later(kf(self.vim.call, 'FlagRebootTest').must(be_right(13)))
        path = fixture_path('rplugin', 'flagellum2')
        self.json_cmd_sync('CrmUpdateState', 'vim_plugin', name, spec=str(path))
        self.seen_message(UpdateState)
        later(kf(lambda: self.state.plugins.head.map(_.spec)).must(be_just(str(path))))
        self.cmd_sync('CrmUpdate')
        self.seen_message(UpdatePlugins)
        self.seen_message(Updated)
        self.cmd_sync('CrmReboot')
        return later(kf(self.vim.call, 'FlagRebootTest').must(be_right(17)))

__all__ = ('TwoExplicitSpec', 'AutostartAfterAddSpec', 'AutostartAtBootSpec')
