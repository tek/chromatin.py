from typing import Any

from ribosome.request.rpc import DefinedHandler
from ribosome.config import Data, Config, PluginSettings
from ribosome.nvim import NvimIO

from amino import List, _, Either, Path, Right, do, Boolean, Map, __, Maybe, Nil, Nothing
from amino.boolean import true, false
from amino.dat import Dat
from amino.do import Do

from chromatin.logging import Logging
from chromatin.plugin import RpluginSpec
from chromatin.venv import Venv, ActiveVenv, PluginVenv
from chromatin.venvs import VenvFacade
from chromatin.settings import CrmSettings


def filter_venvs_by_name(venvs: List[Venv], names: List[str]) -> List[Venv]:
    return venvs if names.empty else venvs.filter(lambda v: v.name in names)


class Env(Dat['Env'], Logging, Data):

    @staticmethod
    def cons(config: Config[PluginSettings, 'Env']) -> 'Env':
        return Env(config, false, Nil, Nothing, Nothing, Map(), Nil, Nil, Nil, Map())

    def __init__(
            self,
            config: Config,
            initialized: Boolean,
            plugins: List[RpluginSpec],
            chromatin_plugin: Maybe[RpluginSpec],
            chromatin_venv: Maybe[Venv],
            venvs: Map[str, Venv],
            installed: List[Venv],
            active: List[ActiveVenv],
            uninitialized: List[ActiveVenv],
            handlers: Map[str, List[DefinedHandler]],
    ) -> None:
        self.config = config
        self.initialized = initialized
        self.plugins = plugins
        self.chromatin_plugin = chromatin_plugin
        self.chromatin_venv = chromatin_venv
        self.venvs = venvs
        self.installed = installed
        self.active = active
        self.uninitialized = uninitialized
        self.handlers = handlers

    @property
    def settings(self) -> CrmSettings:
        return self.config.settings

    def add_plugin(self, name: str, spec: str) -> 'Env':
        return self.append1.plugins(RpluginSpec.cons(name=name, spec=spec))

    def add_plugins(self, plugins: List[RpluginSpec]) -> 'Env':
        return self.append.plugins(plugins)

    def add_venv(self, venv: Venv) -> 'Env':
        return self.append.venvs((venv.name, venv))

    def add_installed(self, venv: Venv) -> 'Env':
        return self.append1.installed(venv)

    @property
    def plugins_with_crm(self) -> List[RpluginSpec]:
        return self.plugins.cons_m(self.chromatin_plugin)

    def plugin_by_name(self, name: str) -> Either[str, RpluginSpec]:
        return self.plugins_with_crm.find(lambda a: a.name == name).to_either(f'no plugin with name `{name}`')

    @do(Either[str, PluginVenv])
    def plugin_venv(self, venv: Venv) -> Do:
        plugin = yield self.plugin_by_name(venv.name)
        yield Right(PluginVenv(venv=venv, plugin=plugin))

    def missing_in(self, venvs: VenvFacade) -> List[Venv]:
        return self.venvs.v.filter_not(venvs.package_installed)

    @property
    def missing(self) -> NvimIO[List[Venv]]:
        return self.venv_facade / self.missing_in

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.plugins, self.venvs)

    @property
    def rplugins(self) -> NvimIO[List[Map[str, str]]]:
        return self.settings.rplugins.value_or_default

    @property
    def venv_dir(self) -> NvimIO[Path]:
        return self.settings.venv_dir.value_or_default

    @property
    def venv_facade(self) -> NvimIO[VenvFacade]:
        return self.venv_dir / VenvFacade

    @property
    def autostart(self) -> NvimIO[Boolean]:
        return self.settings.autostart.value_or_default

    @property
    def handle_crm(self) -> NvimIO[Boolean]:
        return self.settings.handle_crm.value_or_default

    @property
    def autoreboot(self) -> NvimIO[Boolean]:
        return self.settings.autoreboot.value_or_default

    @property
    def active_venvs(self) -> List[Venv]:
        return self.active / _.venv

    @property
    def inactive(self) -> List[ActiveVenv]:
        return self.installed.remove_all(self.active_venvs)

    def host_started(self, venv: ActiveVenv) -> 'Env':
        return self.append1.active(venv).append1.uninitialized(venv)

    def initialization_complete(self) -> 'Env':
        return self.set.uninitialized(List())

    def deactivate_venv(self, venv: ActiveVenv) -> 'Env':
        return self.mod.active(__.without(venv))

    def installed_by_name(self, names: List[str]) -> List[Venv]:
        return self.installed.filter(lambda v: v.name in names)

    def active_by_name(self, names: List[str]) -> List[str]:
        return self.active.filter(lambda v: v.name in names)

    def add_handlers(self, venv: Venv, handlers: List[DefinedHandler]) -> 'Env':
        return self.append.handlers((venv.name, handlers))

    def handlers_for(self, plugin: str) -> Either[str, List[DefinedHandler]]:
        return self.handlers.lift(plugin).to_either(f'no handlers defined for {plugin}')

    @property
    def installed_with_crm(self) -> List[Venv]:
        return self.installed.cons_m(self.chromatin_venv)

    def updateable(self, plugins: List[str]) -> List[Venv]:
        return filter_venvs_by_name(self.installed_with_crm, plugins)


__all__ = ('Env',)
