from typing import Any

from ribosome.data import Data
from ribosome.record import dfield, list_field, map_field, field, maybe_field
from ribosome.nvim import NvimFacade, AsyncVimProxy

from amino import List, _, Either, Path, Try, env, Right, do, Boolean, Map
from amino.boolean import true

from chromatin.logging import Logging
from chromatin.plugin import VimPlugin
from chromatin.venv import Venv
from chromatin.venvs import VenvFacade
from chromatin.util.resources import xdg_cache_home_env_var, create_venv_dir_error


@do
def _default_venv_dir() -> Either[str, Path]:
    xdg_cache_path = env[xdg_cache_home_env_var] / Path | (Path.home() / '.cache')
    venv_dir = xdg_cache_path / 'chromatin' / 'venvs'
    yield Try(venv_dir.mkdir, parents=True, exist_ok=True).lmap(lambda a: create_venv_dir_error(venv_dir))
    yield Right(venv_dir)


class Env(Logging, Data):
    vim_facade = maybe_field((NvimFacade, AsyncVimProxy))
    initialized = dfield(False)
    plugins = list_field(VimPlugin)
    venvs = map_field()
    installed = list_field(Venv)
    active = list_field(Venv)

    def add_plugin(self, name: str, spec: str) -> 'Env':
        return self.append1.plugins(VimPlugin(name=name, spec=spec))

    def add_plugins(self, plugins: List[VimPlugin]) -> 'Env':
        return self.append.plugins(plugins)

    @property
    def show_plugins(self) -> List[str]:
        def format(plug: VimPlugin) -> str:
            return plug.spec
        return self.plugins.map(format).cons('Configured plugins:')

    def add_venv(self, venv: Venv) -> 'Env':
        return self.modder.venvs(_ + (venv.plugin, venv))

    def add_installed(self, venv: Venv) -> 'Env':
        return self.append1.installed(venv)

    def missing_in(self, venvs: VenvFacade) -> List[Venv]:
        return self.venvs.v.filter_not(venvs.package_installed)

    @property
    @do
    def missing(self) -> Either[str, List[Venv]]:
        venv_facade = yield self.venv_facade
        yield Right(self.missing_in(venv_facade))

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.plugins, self.venvs)

    @property
    def venv_dir(self) -> Either[str, Path]:
        return self.vim.vars.ppath('venv_dir').o(_default_venv_dir)

    @property
    def venv_facade(self) -> Either[str, VenvFacade]:
        return self.venv_dir / VenvFacade

    @property
    def want_init(self) -> Boolean:
        return self.vim.vars.pb('autostart') | true

    @property
    def inactive(self) -> List[Venv]:
        return self.installed.remove_all(self.active)

    def activate_venv(self, venv: Venv) -> 'Env':
        return self.append1.active(venv)

    def installed_by_name(self, names: List[str]) -> List[Venv]:
        return self.installed.filter(lambda v: v.name in names)

    def to_map(self) -> Map[str, Any]:
        return super().to_map() - 'vim_facade'

    @property
    def vim(self) -> NvimFacade:
        return self.vim_facade | (lambda: NvimFacade(None, 'no vim was set in `Env`'))

__all__ = ('Env',)
