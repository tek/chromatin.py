from typing import Any

from ribosome.request.rpc import DefinedHandler
from ribosome.config import Data, Config, PluginSettings
from ribosome.nvim import NvimIO

from amino import List, _, Either, Path, Right, do, Boolean, Map, __, Maybe, Nil, Nothing, L
from amino.boolean import false
from amino.dat import Dat
from amino.do import Do

from chromatin.logging import Logging
from chromatin.model.venv import Venv, ActiveVenv, cons_venv
from chromatin.settings import CrmSettings
from chromatin.model.rplugin import Rplugin, ActiveRplugin, VenvRplugin, cons_rplugin
from chromatin.rplugin import venv_package_installed


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
            plugins: List[Rplugin],
            chromatin_plugin: Maybe[Rplugin],
            chromatin_venv: Maybe[Venv],
            venvs: Map[str, Venv],
            ready: List[Rplugin],
            active: List[ActiveRplugin],
            uninitialized: List[ActiveRplugin],
            handlers: Map[str, List[DefinedHandler]],
    ) -> None:
        self.config = config
        self.initialized = initialized
        self.plugins = plugins
        self.chromatin_plugin = chromatin_plugin
        self.chromatin_venv = chromatin_venv
        self.venvs = venvs
        self.ready = ready
        self.active = active
        self.uninitialized = uninitialized
        self.handlers = handlers

    @property
    def settings(self) -> CrmSettings:
        return self.config.settings

    def add_plugin(self, name: str, spec: str) -> 'Env':
        return self.append1.plugins(cons_rplugin(name, spec))

    def add_plugins(self, plugins: List[Rplugin]) -> 'Env':
        return self.append.plugins(plugins)

    def add_venv(self, venv: Venv) -> 'Env':
        return self.append.venvs((venv.name, venv))

    def add_installed(self, venv: Venv) -> 'Env':
        return self.append1.ready(venv)

    @property
    def plugins_with_crm(self) -> List[Rplugin]:
        return self.plugins.cons_m(self.chromatin_plugin)

    def plugin_by_name(self, name: str) -> Either[str, Rplugin]:
        return self.plugins_with_crm.find(lambda a: a.name == name).to_either(f'no plugin with name `{name}`')

    def missing_in(self, base_dir: Path) -> List[Venv]:
        return self.venvs.v.filter_not(venv_package_installed)

    @property
    def missing(self) -> NvimIO[List[Venv]]:
        return self.venv_dir / self.missing_in

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.plugins, self.venvs)

    @property
    def rplugins(self) -> NvimIO[List[Map[str, str]]]:
        return self.settings.rplugins.value_or_default

    @property
    def venv_dir(self) -> NvimIO[Path]:
        return self.settings.venv_dir.value_or_default

    def venv(self, rplugin: VenvRplugin) -> NvimIO[Venv]:
        return self.venv_dir / L(cons_venv)(rplugin, _)

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
    def active_packages(self) -> List[Rplugin]:
        return self.active / _.rplugin

    @property
    def inactive(self) -> List[ActiveRplugin]:
        return self.ready.remove_all(self.active_packages)

    def host_started(self, venv: ActiveVenv) -> 'Env':
        return self.append1.active(venv).append1.uninitialized(venv)

    def initialization_complete(self) -> 'Env':
        return self.set.uninitialized(List())

    def deactivate_venv(self, venv: ActiveVenv) -> 'Env':
        return self.mod.active(__.without(venv))

    def installed_by_name(self, names: List[str]) -> List[Venv]:
        return self.ready.filter(lambda v: v.name in names)

    def active_by_name(self, names: List[str]) -> List[str]:
        return self.active.filter(lambda v: v.name in names)

    def add_handlers(self, venv: Venv, handlers: List[DefinedHandler]) -> 'Env':
        return self.append.handlers((venv.name, handlers))

    def handlers_for(self, plugin: str) -> Either[str, List[DefinedHandler]]:
        return self.handlers.lift(plugin).to_either(f'no handlers defined for {plugin}')

    @property
    def installed_with_crm(self) -> List[Venv]:
        return self.ready.flat_map(lambda r: self.venvs.lift(r.name)).cons_m(self.chromatin_venv)

    def updateable(self, plugins: List[str]) -> List[Venv]:
        return filter_venvs_by_name(self.installed_with_crm, plugins)


__all__ = ('Env',)
