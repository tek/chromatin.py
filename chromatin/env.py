from typing import Any

from ribosome.request.rpc import DefinedHandler
from ribosome.config import Data, Config, PluginSettings
from ribosome.nvim import NvimIO

from amino import List, _, Either, Path, Boolean, Map, __, Maybe, Nil, Nothing, L, do, Do
from amino.dat import Dat

from chromatin.logging import Logging
from chromatin.model.venv import Venv, cons_venv_under, VenvMeta
from chromatin.settings import CrmSettings
from chromatin.model.rplugin import Rplugin, ActiveRplugin, VenvRplugin, cons_rplugin, ActiveRpluginMeta
from chromatin.rplugin import venv_package_installed


def filter_venvs_by_name(venvs: List[Venv], names: List[str]) -> List[Venv]:
    return venvs if names.empty else venvs.filter(lambda v: v.name in names)


class Env(Dat['Env'], Logging, Data):

    @staticmethod
    def cons(config: Config[PluginSettings, 'Env']) -> 'Env':
        return Env(config, Nil, Nothing, Nothing, Map(), Nil, Nil, Nil, Map())

    def __init__(
            self,
            config: Config,
            rplugins: List[Rplugin],
            chromatin_plugin: Maybe[Rplugin],
            chromatin_venv: Maybe[VenvMeta],
            venvs: Map[str, VenvMeta],
            ready: List[str],
            active: List[ActiveRpluginMeta],
            uninitialized: List[ActiveRpluginMeta],
            handlers: Map[str, List[DefinedHandler]],
    ) -> None:
        self.config = config
        self.rplugins = rplugins
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
        return self.append1.rplugins(cons_rplugin(name, spec))

    def add_plugins(self, rplugins: List[Rplugin]) -> 'Env':
        return self.append.rplugins(rplugins)

    def add_venv(self, venv: VenvMeta) -> 'Env':
        return self if venv.rplugin in self.venvs else self.append.venvs((venv.rplugin, venv))

    def add_installed(self, rplugin: str) -> 'Env':
        return self.copy(ready=self.ready.cat(rplugin).distinct)

    @property
    def rplugins_with_crm(self) -> List[Rplugin]:
        return self.rplugins.cons_m(self.chromatin_plugin)

    def rplugin_by_name(self, name: str) -> Either[str, Rplugin]:
        return self.rplugins_with_crm.find(lambda a: a.name == name).to_either(f'no rplugin with name `{name}`')

    @property
    @do(NvimIO[List[Venv]])
    def missing(self) -> Do:
        venvs = yield self.venvs.v.traverse(self.venv_from_meta, NvimIO)
        yield NvimIO.pure(venvs.filter_not(venv_package_installed))

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.rplugins, self.venvs)

    @property
    def rplugins_setting(self) -> NvimIO[List[Map[str, str]]]:
        return self.settings.rplugins.value_or_default

    @property
    def venv_dir(self) -> NvimIO[Path]:
        return self.settings.venv_dir.value_or_default

    def venv_from_rplugin(self, rplugin: VenvRplugin) -> NvimIO[Venv]:
        return self.venv_dir / L(cons_venv_under)(_, rplugin)

    @do(NvimIO[Venv])
    def venv_from_meta(self, meta: VenvMeta) -> Do:
        rplugin = yield NvimIO.from_either(self.rplugin_by_name(meta.name))
        yield self.venv_dir / L(cons_venv_under)(_, rplugin)

    @property
    def autostart(self) -> NvimIO[Boolean]:
        return self.settings.autostart.value_or_default

    @property
    def handle_crm(self) -> NvimIO[Boolean]:
        return self.settings.handle_crm.value_or_default

    @property
    def autoreboot(self) -> NvimIO[Boolean]:
        return self.settings.autoreboot.value_or_default

    def rplugin(self, name: str) -> Either[str, Rplugin]:
        return self.rplugins.find(_.name == name).to_either(f'no rplugin named `{name}`')

    @property
    def active_packages(self) -> Either[str, List[Rplugin]]:
        return self.active_rplugins / __.map(_.rplugin)

    @property
    def active_package_names(self) -> Either[str, List[str]]:
        return self.active_rplugins / __.map(_.name)

    @property
    def ready_rplugins(self) -> Either[str, List[Rplugin]]:
        return self.ready.traverse(self.rplugin, Either)

    @property
    def inactive(self) -> List[Rplugin]:
        return self.ready.remove_all(self.active_package_names).traverse(self.rplugin, Either)

    def host_started(self, rplugin: ActiveRpluginMeta) -> 'Env':
        return self.append1.active(rplugin).append1.uninitialized(rplugin)

    def initialization_complete(self) -> 'Env':
        return self.set.uninitialized(List())

    def deactivate_rplugin(self, meta: ActiveRpluginMeta) -> 'Env':
        return self.mod.active(__.without(meta))

    def ready_by_name(self, names: List[str]) -> Either[str, List[Rplugin]]:
        return names.filter(self.ready.contains).traverse(self.rplugin, Either)

    def active_by_name(self, names: List[str]) -> List[ActiveRpluginMeta]:
        return self.active.filter(lambda v: v.rplugin in names)

    def active_rplugin(self, meta: ActiveRpluginMeta) -> Either[str, ActiveRplugin]:
        return (
            self.rplugins
            .find(_.name == meta.rplugin)
            .map(lambda p: ActiveRplugin(p, meta))
            .to_either(f'no rplugin for {meta}')
        )

    def as_active_rplugins(self, meta: List[ActiveRpluginMeta]) -> Either[str, List[ActiveRplugin]]:
        return meta.traverse(self.active_rplugin, Either)

    @property
    def active_rplugins(self) -> Either[str, List[ActiveRplugin]]:
        return self.as_active_rplugins(self.active)

    def active_rplugins_by_name(self, names: List[str]) -> Either[str, List[ActiveRplugin]]:
        return self.as_active_rplugins(self.active_by_name(names))

    @property
    def uninitialized_rplugins(self) -> Either[str, List[ActiveRplugin]]:
        return self.as_active_rplugins(self.uninitialized)

    def add_handlers(self, venv: Venv, handlers: List[DefinedHandler]) -> 'Env':
        return self.append.handlers((venv.name, handlers))

    def handlers_for(self, plugin: str) -> Either[str, List[DefinedHandler]]:
        return self.handlers.lift(plugin).to_either(f'no handlers defined for {plugin}')

    @property
    def installed_with_crm(self) -> List[VenvMeta]:
        return self.ready.flat_map(self.venvs.lift).cons_m(self.chromatin_venv)

    def updateable(self, rplugins: List[str]) -> NvimIO[List[Venv]]:
        all = self.installed_with_crm
        selected = all if rplugins.empty else filter_venvs_by_name(self.installed_with_crm, rplugins)
        return selected.traverse(self.venv_from_meta, NvimIO)


__all__ = ('Env',)
