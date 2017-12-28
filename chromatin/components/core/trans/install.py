from typing import Tuple

from amino import do, List, _, Lists, __, Maybe, Just
from amino.do import Do
from amino.boolean import false, true
from amino.io import IOException
from amino.util.string import plural_s

from ribosome.nvim.io import NS
from ribosome.trans.api import trans
from ribosome.logging import ribo_log
from ribosome.process import SubprocessResult
from ribosome.trans.effect import GatherSubprocs
from ribosome.trans.action import Info, Error, LogMessage

from chromatin.components.core.logic import (install_plugins, add_installed, reboot_plugins, activate_by_names,
                                             deactivate_by_names)
from chromatin import Env
from chromatin.util import resources
from chromatin.model.venv import Venv


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
    yield NS.pure(msg)


@trans.free.result(trans.st, trans.gather_subprocs)
@do(NS[Env, GatherSubprocs[Venv, Tuple[List[Venv], List[IOException]]]])
def install_missing() -> Do:
    missing = yield NS.inspect_f(_.missing)
    yield NS.from_either(install_plugins(missing, false))


@trans.free.cons(trans.st, trans.m, trans.log)
@do(NS[Env, Maybe[LogMessage]])
def activate(*plugins: str) -> Do:
    already_installed = yield activate_by_names(Lists.wrap(plugins))
    names = already_installed / _.name
    msg = (~already_installed.empty).m(lambda: Info(resources.already_active(names)))
    yield NS.pure(msg)


@trans.free.unit(trans.st)
def deactivate(*plugins: str) -> NS[Env, None]:
    return deactivate_by_names(Lists.wrap(plugins))


@do(NS[Env, None])
def updated(result: List[Venv]) -> Do:
    venvs = result.filter_not(_.name == 'chromatin')
    autoreboot = yield NS.inspect_f(_.autoreboot)
    if autoreboot:
        yield reboot_plugins(venvs / _.name)


@trans.free.result(trans.st, trans.gather_subprocs)
@do(NS[Env, GatherSubprocs[Venv, Tuple[List[Venv], List[IOException]]]])
def update_plugins_io(plugins: List[str]) -> Do:
    venvs = yield NS.inspect_f(__.updateable(plugins))
    yield (
        NS.error(resources.no_plugins_match_for_update(plugins))
        if venvs.empty else
        NS.from_either(install_plugins(venvs, true))
    )


@trans.free.cons(trans.st, trans.log)
@do(NS[Env, LogMessage])
def updated_plugins(results: List[SubprocessResult[Venv]], errors: List[IOException]) -> Do:
    errors.foreach(lambda e: ribo_log.caught_exception('updating plugin', e))
    success, failed = results.split(_.success)
    success_venvs = success / _.data
    failed_venvs = failed / _.data
    yield updated(success_venvs)
    msg = failed.empty.c(
        lambda: Info(resources.updated_plugins(success_venvs / _.name)),
        lambda: Error(resources.plugins_install_failed(failed_venvs / _.name)),
    )
    yield NS.pure(msg)


@trans.free.do()
@do(NS[Env, None])
def update_plugins(*ps: str) -> Do:
    plugins = Lists.wrap(ps)
    success, fail = yield update_plugins_io(plugins).m
    yield updated_plugins(success, fail).m


@trans.free.unit(trans.st)
def reboot(*plugins: str) -> NS[Env, None]:
    return reboot_plugins(Lists.wrap(plugins)).replace(None)


__all__ = ('install_result', 'install_missing', 'update_plugins')
