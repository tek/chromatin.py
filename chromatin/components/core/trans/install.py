from typing import Tuple

from amino import do, List, _, Lists, Maybe, Just, L, Path
from amino.do import Do
from amino.boolean import false, true
from amino.io import IOException
from amino.lenses.lens import lens

from ribosome.nvim.io import NS
from ribosome.trans.api import trans
from ribosome.logging import ribo_log
from ribosome.process import SubprocessResult
from ribosome.trans.action import Info, Error, LogMessage
from ribosome.trans.effects import GatherSubprocs
from ribosome.config.config import Resources

from chromatin.components.core.logic import (install_plugins, add_installed, reboot_plugins, activate_by_names,
                                             deactivate_by_names, missing_plugins, venv_from_meta, venv_dir_setting)
from chromatin import Env
from chromatin.util import resources
from chromatin.model.venv import Venv, VenvMeta
from chromatin.settings import ChromatinSettings, setting
from chromatin.config.component import ChromatinComponent
from chromatin.config.resources import ChromatinResources


@trans.free.cons(trans.st, trans.m, trans.log)
@do(NS[Env, Maybe[LogMessage]])
def install_result(installed: List[SubprocessResult[Venv]], errors: List[IOException]) -> Do:
    errors.foreach(lambda e: ribo_log.caught_exception('installing plugin', e))
    success, failed = installed.split(_.success)
    success_venvs = success / _.data
    failed_venvs = failed / _.data
    rplugins = success_venvs / _.rplugin
    yield rplugins.traverse(add_installed, NS)
    msg = failed.empty.c(
        lambda: (~success.empty).m(lambda: Info(resources.installed_plugins(success_venvs / _.name))),
        lambda: Just(Error(resources.plugins_install_failed(failed_venvs / _.name))),
    )
    return msg


@trans.free.result(trans.st, trans.gather_subprocs)
@do(NS[ChromatinResources, GatherSubprocs[Venv, Tuple[List[Venv], List[IOException]]]])
def install_missing() -> Do:
    missing = yield missing_plugins()
    yield NS.from_either(install_plugins(missing, false))


@trans.free.cons(trans.st, trans.m, trans.log)
@do(NS[ChromatinResources, Maybe[LogMessage]])
def activate(*plugins: str) -> Do:
    already_installed = yield activate_by_names(Lists.wrap(plugins))
    names = already_installed / _.name
    return (~already_installed.empty).m(lambda: Info(resources.already_active(names)))


@trans.free.unit(trans.st)
def deactivate(*plugins: str) -> NS[Env, None]:
    return deactivate_by_names(Lists.wrap(plugins))


@do(NS[Env, None])
def updated(result: List[Venv]) -> Do:
    venvs = result.filter_not(_.name == 'chromatin')
    autoreboot = yield setting(_.autoreboot)
    if autoreboot:
        yield reboot_plugins(venvs / _.name)


def filter_venvs_by_name(venvs: List[Venv], names: List[str]) -> List[Venv]:
    return venvs if names.empty else venvs.filter(lambda v: v.name in names)


def installed_with_crm() -> NS[Env, List[VenvMeta]]:
    return NS.inspect(lambda a: a.ready.flat_map(a.venvs.lift).cons_m(a.chromatin_venv))


@do(NS[Env, List[Venv]])
def updateable(venv_dir: Path, rplugins: List[str]) -> Do:
    all = yield installed_with_crm()
    selected = all if rplugins.empty else filter_venvs_by_name(all, rplugins)
    yield selected.traverse(L(venv_from_meta)(venv_dir, _), NS)


@trans.free.result(trans.st, trans.gather_subprocs)
@do(NS[Resources[Env, ChromatinSettings, ChromatinComponent],
       GatherSubprocs[Venv, Tuple[List[Venv], List[IOException]]]])
def update_plugins_io(plugins: List[str]) -> Do:
    venv_dir = yield venv_dir_setting()
    venvs = yield updateable(venv_dir, plugins).zoom(lens.data)
    yield (
        NS.error(resources.no_plugins_match_for_update(plugins))
        if venvs.empty else
        NS.from_either(install_plugins(venvs, true))
    )


@trans.free.cons(trans.st, trans.log)
@do(NS[ChromatinResources, LogMessage])
def updated_plugins(results: List[SubprocessResult[Venv]], errors: List[IOException]) -> Do:
    errors.foreach(lambda e: ribo_log.caught_exception('updating plugin', e))
    success, failed = results.split(_.success)
    success_venvs = success / _.data
    failed_venvs = failed / _.data
    yield updated(success_venvs)
    return failed.empty.c(
        lambda: Info(resources.updated_plugins(success_venvs / _.name)),
        lambda: Error(resources.plugins_install_failed(failed_venvs / _.name)),
    )


@trans.free.do()
@do(NS[Env, None])
def update_plugins(*ps: str) -> Do:
    plugins = Lists.wrap(ps)
    success, fail = yield update_plugins_io(plugins).m
    yield updated_plugins(success, fail).m


@trans.free.unit(trans.st)
def reboot(*plugins: str) -> NS[ChromatinResources, None]:
    return reboot_plugins(Lists.wrap(plugins)).replace(None)


__all__ = ('install_result', 'install_missing', 'update_plugins')
