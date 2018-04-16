from typing import Tuple, Any, cast

from amino.test import temp_dir

from kallikrein import Expectation, kf
from kallikrein.matchers.typed import have_type
from kallikrein.matchers.either import be_right
from kallikrein.expectable import kio
from kallikrein.matchers import contain
from amino.test.path import fixture_path
from amino import Maybe, Path, Nothing, do, Do, List

from ribosome.test.integration.klk import later
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.variable import variable_set_prefixed
from ribosome.nvim.api.option import option_cat
from ribosome.nvim.api.command import nvim_command
from ribosome.nvim.io.api import N
from ribosome.test.klk import kn

from chromatin.model.rplugin import Rplugin, RpluginReady, cons_rplugin
from chromatin.model.venv import VenvExistent, Venv
from chromatin.rplugin import check_venv, rplugin_installed

from integration._support.base import DefaultSpec


class RpluginSpecBase(DefaultSpec):

    def _pre_start(self) -> None:
        super()._pre_start()
        @do(NvimIO[None])
        def set_vars() -> Do:
            yield variable_set_prefixed('autostart', False)
            yield variable_set_prefixed('autoreboot', False)
            yield variable_set_prefixed('handle_crm', False)
            yield variable_set_prefixed('debug_pythonpath', True)
        set_vars().unsafe(self.vim)

    def plug_exists(self, name: str, **kw: Any) -> Expectation:
        cmd = f'{name}Test'
        return self.command_exists(cmd, **kw)

    def venv_existent(self, base_dir: Path, rplugin: Rplugin, timeout: float=None) -> Expectation:
        return later(kio(check_venv, base_dir, rplugin).must(have_type(VenvExistent)), timeout=timeout, intval=.5)

    def package_installed(self, base_dir: Path, rplugin: Rplugin) -> Expectation:
        return later(
            self.venv_existent(base_dir, rplugin) &
            kio(rplugin_installed(base_dir), rplugin).must(have_type(RpluginReady)),
            20,
            .5,
        )

    @do(NvimIO[Venv])
    def plugin_venv(self, base_dir: Path, rplugin: Rplugin) -> Do:
        later(self.venv_existent(base_dir, rplugin))
        venv_status = yield N.from_io(check_venv(base_dir, rplugin))
        yield (
            N.pure(venv_status.venv)
            if isinstance(venv_status, VenvExistent) else
            N.error(f'venv for {rplugin} did not appear')
        )

    @do(NvimIO[Path])
    def setup_venv_dir(self, venv_dir: Maybe[Path] = Nothing) -> Do:
        rtp = fixture_path('rplugin', 'config', 'rtp')
        yield option_cat('runtimepath', List(rtp))
        dir = venv_dir | temp_dir('rplugin', 'venv')
        yield variable_set_prefixed('venv_dir', str(dir))
        return dir

    @do(NvimIO[Rplugin])
    def setup_one(self, name: str, venv_dir: Maybe[Path]=Nothing) -> Do:
        plugin = cons_rplugin(name, name)
        path = fixture_path('rplugin', name)
        yield nvim_command('Cram', str(path), name)
        return plugin

    @do(NvimIO[Tuple[Path, Rplugin]])
    def setup_one_with_venvs(self, name: str, venv_dir: Maybe[Path] = Nothing) -> Do:
        base_dir = yield self.setup_venv_dir(venv_dir)
        plugin = yield self.setup_one(name, venv_dir)
        return base_dir, plugin

    @do(NvimIO[Tuple[Venv, Rplugin]])
    def install_one(self, name: str, venv_dir: Maybe[Path]=Nothing) -> Do:
        base_dir, plugin = yield self.setup_one_with_venvs(name, venv_dir)
        yield nvim_command('CrmSetupPlugins')
        self.venv_existent(base_dir, plugin)
        self.package_installed(base_dir, plugin)
        venv = yield self.plugin_venv(base_dir, plugin)
        return base_dir, venv, plugin

    @do(NvimIO[Venv])
    def activate_one(self, name: str, prefix: str) -> Do:
        base_dir, venv, plugin = yield self.install_one(name)
        yield nvim_command('CrmActivate')
        later(self.plug_exists(prefix))
        return venv


__all__ = ('RpluginSpecBase',)
