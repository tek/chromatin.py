from kallikrein import Expectation, k, kf, pending
from kallikrein.matchers.length import have_length
from kallikrein.matchers.either import be_right
from kallikrein.matchers.maybe import be_just
from kallikrein.matchers import contain

from amino.test.path import fixture_path, base_dir
from amino.test import temp_dir
from amino import List, Path, _, do, Do
from amino.json import dump_json

from ribosome.test.integration.klk import later
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.exists import command_once_defined, wait_for_function, call_once_defined, wait_for_function_undef
from ribosome.test.klk import kn
from ribosome.nvim.api.variable import variable_set_prefixed
from ribosome.nvim.api.command import nvim_command, runtime
from ribosome.nvim.api.option import option_cat
from ribosome.nvim.api.function import nvim_call_function
from ribosome.nvim.io.api import N

from chromatin.model.rplugin import VenvRplugin, Rplugin

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
        @do(NvimIO[None])
        def set_vars() -> Do:
            yield variable_set_prefixed('rplugins', plugins)
            yield variable_set_prefixed('venv_dir', str(self.dir))
        set_vars().unsafe(self.vim)

    def read_conf(self) -> Expectation:
        return kf(lambda: self.state.rplugins).must(have_length(2))

    @pending
    def bootstrap(self) -> Expectation:
        @do(NvimIO[None])
        def run() -> Do:
            yield nvim_command('CrmSetupPlugins')
            self.seen_program('setup_venvs_ios')
            self.venv_existent(self.dir, plugin1)
            self.seen_program('missing_plugins')
            self.package_installed(self.dir, plugin1)
            self.package_installed(self.dir, plugin2)
            self.seen_program('post_setup')
            yield nvim_command('CrmActivate')
        run().unsafe(self.vim)
        return self.plug_exists('Flag') & self.plug_exists('Cil')


class AutostartAfterAddSpec(RpluginSpecBase):
    '''automatic initialization when using `Cram` $auto_cram
    '''

    @pending
    def auto_cram(self) -> Expectation:
        @do(NvimIO[None])
        def run() -> Do:
            yield variable_set_prefixed('autostart', True)
            venvs, plugin = yield self.setup_one_with_venvs('flagellum')
            self.seen_program('post_setup')
            self.venv_existent(venvs, plugin, timeout=4)
            self.package_installed(venvs, plugin)
        run().unsafe(self.vim)
        return later(self.plug_exists('Flag'))


class AutostartAtBootSpec(RpluginSpecBase):
    '''automatic initialization at vim startup $startup
    '''

    @property
    def dir(self) -> Path:
        return temp_dir('rplugin', 'venv')

    def _pre_start(self) -> None:
        super()._pre_start()
        @do(NvimIO[None])
        def run() -> Do:
            yield variable_set_prefixed('rplugins', plugins.take(1))
            yield variable_set_prefixed('venv_dir', str(self.dir))
            yield variable_set_prefixed('autostart', True)
        run().unsafe(self.vim)

    @pending
    def startup(self) -> Expectation:
        self.seen_program('post_setup')
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
        @do(NvimIO[None])
        def run() -> Do:
            yield option_cat('runtimepath', List(str(self.pkg_dir)))
            yield variable_set_prefixed('autobootstrap', False)
            yield variable_set_prefixed('venv_dir', str(self.dir))
            yield variable_set_prefixed('pip_req', str(self.pkg_dir))
            yield variable_set_prefixed('rplugins', plugins)
        run().unsafe(self.vim)

    def bootstrap(self) -> Expectation:
        self.command_exists_not('Cram')
        @do(NvimIO[None])
        def run() -> Do:
            yield runtime('chromatin.nvim/plugin/bootstrap')
            yield nvim_command('BootstrapChromatin')
            self.command_exists('ChromatinPoll', timeout=20)
            yield nvim_command('CrmSetupPlugins')
        run().unsafe(self.vim)
        return self.plug_exists('Flag', timeout=20)


# TODO move to `ActivateSpec`, change `ensure_env` to move the temp venv to `_temp` instead of using the `temp` dir
# directly
class RebootSpec(RpluginSpecBase):
    '''deactivate and reactivate a plugin $reboot
    '''

    def reboot(self) -> Expectation:
        reboot_test = 'FlagRebootTest'
        path = fixture_path('rplugin', 'flagellum2')
        update_query = dict(patch=dict(query=f'rplugins(name={name1})', data=dict(spec=str(path))))
        @do(NvimIO[None])
        def run() -> Do:
            yield self.activate_one(name1, 'Flag')
            before = yield call_once_defined(reboot_test)
            json = yield N.e(dump_json(update_query))
            yield nvim_command(f'CrmUpdateState {json}')
            self.seen_program('update_state')
            later(kf(lambda: self.state.rplugins.head.map(_.spec)).must(be_just(str(path))))
            yield nvim_command('CrmUpdate')
            self.seen_program('updated_plugins')
            yield nvim_command('CrmReboot')
            yield wait_for_function_undef(reboot_test)
            after = yield call_once_defined(reboot_test)
            return before, after
        return kn(self.vim, run).must(contain((13, 17)))


__all__ = ('TwoExplicitSpec', 'AutostartAfterAddSpec', 'AutostartAtBootSpec', 'BootstrapSpec')
