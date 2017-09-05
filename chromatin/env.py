from typing import Any, Generator

from ribosome.data import Data
from ribosome.record import dfield, list_field, map_field, maybe_field
from ribosome.nvim import NvimFacade, AsyncVimProxy
from ribosome.rpc import DefinedHandler

from amino import List, _, Either, Path, Try, Right, do, Boolean, Map, __
from amino.boolean import true

from chromatin.logging import Logging
from chromatin.plugin import RpluginSpec
from chromatin.venv import Venv, ActiveVenv, PluginVenv
from chromatin.venvs import VenvFacade
from chromatin.util.resources import xdg_cache_home, create_venv_dir_error


@do
def _default_venv_dir() -> Generator[Either[str, Path], Any, None]:
    xdg_cache_path = xdg_cache_home.value / Path | (Path.home() / '.cache')
    venv_dir = xdg_cache_path / 'chromatin' / 'venvs'
    yield Try(venv_dir.mkdir, parents=True, exist_ok=True).lmap(lambda a: create_venv_dir_error(venv_dir))
    yield Right(venv_dir)


class Env(Logging, Data):
    vim_facade = maybe_field((NvimFacade, AsyncVimProxy))
    initialized = dfield(False)
    plugins = list_field(RpluginSpec)
    venvs = map_field()
    installed = list_field(Venv)
    active = list_field(ActiveVenv)
    uninitialized = list_field(ActiveVenv)
    handlers = map_field()

    def add_plugin(self, name: str, spec: str) -> 'Env':
        return self.append1.plugins(RpluginSpec(name=name, spec=spec))

    def add_plugins(self, plugins: List[RpluginSpec]) -> 'Env':
        return self.append.plugins(plugins)

    @property
    def show_plugins(self) -> List[str]:
        def format(plug: RpluginSpec) -> str:
            return plug.spec
        return self.plugins.map(format).cons('Configured plugins:')

    def add_venv(self, venv: Venv) -> 'Env':
        return self.modder.venvs(_ + (venv.name, venv))

    def add_installed(self, venv: Venv) -> 'Env':
        return self.append1.installed(venv)

    def plugin_by_name(self, name: str) -> Either[str, RpluginSpec]:
        return self.plugins.find(lambda a: a.name == name)

    @do
    def plugin_venv(self, venv: Venv) -> Either[str, PluginVenv]:
        plugin = yield self.plugin_by_name(venv.name)
        yield Right(PluginVenv(venv=venv, plugin=plugin))

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
    def autoreboot(self) -> Boolean:
        return self.vim.vars.pb('autoreboot') | true

    @property
    def active_venvs(self) -> List[Venv]:
        return self.active / _.venv

    @property
    def inactive(self) -> List[ActiveVenv]:
        return self.installed.remove_all(self.active_venvs)

    def host_started(self, venv: ActiveVenv) -> 'Env':
        return self.append1.active(venv).append1.uninitialized(venv)

    def initialization_complete(self) -> 'Env':
        return self.setter.uninitialized(List())

    def deactivate_venv(self, venv: ActiveVenv) -> 'Env':
        return self.modder.active(__.without(venv))

    def installed_by_name(self, names: List[str]) -> List[Venv]:
        return self.installed.filter(lambda v: v.name in names)

    def active_by_name(self, names: List[str]) -> List[str]:
        return self.active.filter(lambda v: v.name in names)

    def to_map(self) -> Map[str, Any]:
        return super().to_map() - 'vim_facade'

    @property
    def vim(self) -> NvimFacade:
        return self.vim_facade | (lambda: NvimFacade(None, 'no vim was set in `Env`'))

    def add_handlers(self, venv: Venv, handlers: List[DefinedHandler]) -> 'Env':
        return self.modder.handlers(_ + (venv.name, handlers))

    def handlers_for(self, plugin: str) -> Either[str, List[DefinedHandler]]:
        return self.handlers.lift(plugin).to_either(f'no handlers defined for {plugin}')

__all__ = ('Env',)
