from typing import Any

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.io.api import N
from ribosome.rpc.define import ActiveRpcTrigger

from amino import List, _, Either, Boolean, Map, __, Maybe, Nil, L, do, Do
from amino.dat import Dat

from chromatin.model.venv import Venv, VenvMeta
from chromatin.model.rplugin import Rplugin, ActiveRplugin, cons_rplugin, ActiveRpluginMeta
from chromatin.venv import venv_package_installed, cons_venv_under


class Env(Dat['Env']):

    @staticmethod
    def cons(
            rplugins: List[Rplugin]=Nil,
            chromatin_rplugin: Rplugin=None,
            chromatin_venv: str=None,
            venvs: List[str]=Nil,
            ready: List[str]=Nil,
            active: List[ActiveRpluginMeta]=Nil,
            uninitialized: List[ActiveRpluginMeta]=Nil,
            triggers: Map[str, List[ActiveRpcTrigger]]=Map(),
    ) -> 'Env':
        return Env(
            rplugins,
            Maybe.optional(chromatin_rplugin),
            Maybe.optional(chromatin_venv),
            venvs,
            ready,
            active,
            uninitialized,
            triggers,
        )

    def __init__(
            self,
            rplugins: List[Rplugin],
            chromatin_rplugin: Maybe[Rplugin],
            chromatin_venv: Maybe[str],
            venvs: List[str],
            ready: List[str],
            active: List[ActiveRpluginMeta],
            uninitialized: List[ActiveRpluginMeta],
            triggers: Map[str, List[ActiveRpcTrigger]],
    ) -> None:
        self.rplugins = rplugins
        self.chromatin_rplugin = chromatin_rplugin
        self.chromatin_venv = chromatin_venv
        self.venvs = venvs
        self.ready = ready
        self.active = active
        self.uninitialized = uninitialized
        self.triggers = triggers

    def add_plugin(self, name: str, spec: str) -> 'Env':
        return self.append1.rplugins(cons_rplugin(name, spec))

    def add_installed(self, rplugin: str) -> 'Env':
        return self.copy(ready=self.ready.cat(rplugin).distinct)

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.rplugins, self.venvs)

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

    def add_handlers(self, venv: Venv, triggers: List[ActiveRpcTrigger]) -> 'Env':
        return self.append.triggers((venv.name, triggers))

    def handlers_for(self, plugin: str) -> Either[str, List[ActiveRpcTrigger]]:
        return self.triggers.lift(plugin).to_either(f'no triggers defined for {plugin}')

    @property
    def installed_with_crm(self) -> List[VenvMeta]:
        return self.venvs.filter(self.ready.contains).cons_m(self.chromatin_venv)


__all__ = ('Env',)
