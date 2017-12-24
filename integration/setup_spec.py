from kallikrein import Expectation, k, kf
from kallikrein.matchers.length import have_length
from kallikrein.matchers.either import be_right
from kallikrein.matchers.maybe import be_just

from amino.test.path import fixture_path, base_dir
from amino.test import temp_dir
from amino import List, Path, _
from amino.json import dump_json

from ribosome.test.integration.klk import later

from chromatin.model.rplugin import VenvRplugin

from integration._support.rplugin_spec_base import RpluginSpecBase

name1 = 'flagellum'
name2 = 'cilia'
path1 = fixture_path('rplugin', name1)
path2 = fixture_path('rplugin', name2)

plugin1 = VenvRplugin.cons(name1, name1)
plugin2 = VenvRplugin.cons(name2, name2)

plugins = List(
    dict(name=name1, spec=str(path1)),
    dict(name=name2, spec=str(path2)),
)


class TwoExplicitSpec(RpluginSpecBase):
    '''two plugins in separate venvs
    read plugin config from `g:chromatin_rplugins` $read_conf
    bootstrap and activate, explicit initialization $bootstrap
    '''

    @property
    def dir(self) -> Path:
        return temp_dir('rplugin', 'venv')

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.vars.set_p('rplugins', plugins)
        self.vim.vars.set_p('venv_dir', str(self.dir))

    def read_conf(self) -> Expectation:
        return k(self.state.rplugins).must(have_length(2))

    def bootstrap(self) -> Expectation:
        self.vim.cmd_once_defined('ChromatinStage1')
        self.cmd_sync('CrmSetupPlugins')
        self.seen_trans('setup_venvs')
        self.venv_existent(self.dir, plugin1)
        self.seen_trans('install_missing')
        self.package_installed(self.dir, plugin1)
        self.package_installed(self.dir, plugin2)
        self.seen_trans('post_setup')
        self.cmd_sync('CrmActivate')
        return self.plug_exists('Flag') & self.plug_exists('Cil')


class AutostartAfterAddSpec(RpluginSpecBase):
    '''automatic initialization when using `Cram` $auto_cram
    '''

    def auto_cram(self) -> Expectation:
        self.vim.vars.set_p('autostart', True)
        venvs, plugin = self.setup_one_with_venvs('flagellum')
        self.seen_trans('setup_plugins')
        self.venv_existent(venvs, plugin, timeout=4)
        self.package_installed(venvs, plugin)
        return later(self.plug_exists('Flag'))


class AutostartAtBootSpec(RpluginSpecBase):
    '''automatic initialization at vim startup $startup
    '''

    @property
    def dir(self) -> Path:
        return temp_dir('rplugin', 'venv')

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.vars.set_p('rplugins', plugins.take(1))
        self.vim.vars.set_p('venv_dir', str(self.dir))
        self.vim.vars.set_p('autostart', True)

    def startup(self) -> Expectation:
        self.vim.cmd_once_defined('ChromatinStage1')
        self.seen_trans('setup_plugins')
        self.seen_trans('setup_venvs')
        self.seen_trans('install_missing')
        self.seen_trans('post_setup')
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
        self.vim.runtime('chromatin.nvim/plugin/bootstrap')
        self.cmd('BootstrapChromatin')
        self.command_exists('ChromatinStage1', timeout=10)
        self.cmd_sync('ChromatinStage1')
        self.cmd_sync('CrmSetupPlugins')
        return self.plug_exists('Flag', timeout=10)


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
        json = dump_json(dict(patch=dict(query=f'rplugins(name={name})', data=dict(spec=str(path))))).get_or_raise()
        self.vim.cmd(f'CrmUpdateState {json}')
        self.seen_trans('update_state')
        later(kf(lambda: self.state.rplugins.head.map(_.spec)).must(be_just(str(path))))
        self.cmd_sync('CrmUpdate')
        self.seen_trans('update_plugins_io')
        self.seen_trans('updated_plugins')
        self.cmd_sync('CrmReboot')
        return later(kf(self.vim.call, 'FlagRebootTest').must(be_right(17)))

__all__ = ('TwoExplicitSpec', 'AutostartAfterAddSpec', 'AutostartAtBootSpec', 'BootstrapSpec')
