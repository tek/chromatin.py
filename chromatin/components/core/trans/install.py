from amino import do, List, _, Lists, L, Path
from amino.do import Do
from amino.boolean import false, true
from amino.io import IOException
from amino.lenses.lens import lens
from amino.state import State
from amino.logging import module_log

from ribosome.nvim.io.state import NS
from ribosome.logging import ribo_log
from ribosome.process import SubprocessResult
from ribosome.compute.api import prog
from ribosome.compute.output import Echo
from ribosome.compute.prog import Prog
from ribosome.compute.ribosome_api import Ribo

from chromatin.components.core.logic import (install_plugins, add_installed, reboot_plugins, activate_by_names,
                                             deactivate_by_names, split_plugins_by_install_status)
from chromatin.util import resources
from chromatin.model.venv import Venv
from chromatin.env import Env
from chromatin.settings import venv_dir, autoreboot
from chromatin.components.core.trans.tpe import CrmRibosome

log = module_log()


@prog.echo
@do(NS[Env, Echo])
def install_result(installed: List[SubprocessResult[str]], preinstalled: List[str], errors: List[IOException]) -> Do:
    errors.foreach(lambda e: ribo_log.caught_exception('installing plugin', e))
    success, failed = installed.split(_.success)
    success_rplugins = success / _.data
    failed_rplugins = failed / _.data
    yield (success_rplugins + preinstalled).traverse(add_installed, NS)
    return (
        Echo.error(resources.plugins_install_failed(failed_rplugins))
        if not failed.empty else
        Echo.unit
        if success.empty else
        Echo.info(resources.installed_plugins(success_rplugins))
    )


@prog.do(None)
def install_rplugins() -> Do:
    preinstalled, missing = yield split_plugins_by_install_status()
    installed, errors = yield install_plugins(missing, false)
    yield install_result(installed, preinstalled, errors)


@prog.echo
@do(NS[CrmRibosome, Echo])
def activate(*plugins: str) -> Do:
    already_installed = yield activate_by_names(Lists.wrap(plugins))
    names = already_installed / _.name
    return (
        Echo.unit
        if already_installed.empty else
        Echo.info(resources.already_active(names))
    )


@prog
def deactivate(*plugins: str) -> NS[Env, None]:
    return deactivate_by_names(Lists.wrap(plugins))


@do(NS[CrmRibosome, None])
def updated(result: List[str]) -> Do:
    venvs = result.filter_not(lambda a: a == 'chromatin')
    reboot = yield NS.lift(autoreboot.value_or_default())
    if reboot:
        yield reboot_plugins(venvs)


def filter_venvs_by_name(venvs: List[str], names: List[str]) -> List[str]:
    return venvs if names.empty else venvs.filter(lambda v: v in names)


def installed_with_crm() -> State[Env, List[str]]:
    return State.inspect(lambda a: a.ready.cons_m(a.chromatin_venv))


@do(State[Env, List[str]])
def updateable(venv_dir: Path, requested: List[str]) -> Do:
    all = yield installed_with_crm()
    selected = all if requested.empty else all.filter(lambda v: v in requested)


@prog
@do(NS[CrmRibosome, List[str]])
def updateable_venvs(plugins: List[str]) -> Do:
    dir = yield Ribo.setting(venv_dir)
    yield Ribo.zoom_main(updateable(dir, plugins).nvim)


@prog.do(None)
def update_plugins_io(plugins: List[str]) -> Do:
    venvs = yield updateable_venvs(plugins)
    yield (
        Prog.error(resources.no_plugins_match_for_update(plugins))
        if venvs.empty else
        install_plugins(venvs, true)
    )


@prog.echo
@do(NS[CrmRibosome, Echo])
def updated_plugins(results: List[SubprocessResult[Venv]], errors: List[IOException]) -> Do:
    errors.foreach(lambda e: ribo_log.caught_exception('updating plugin', e))
    success, failed = results.split(_.success)
    success_venvs = success / _.data
    failed_venvs = failed / _.data
    yield updated(success_venvs)
    return (
        Echo.info(resources.updated_plugins(success_venvs))
        if failed.empty else
        Echo.error(resources.plugins_install_failed(failed_venvs))
    )


@prog.do(None)
def update_plugins(*ps: str) -> Do:
    plugins = Lists.wrap(ps)
    success, fail = yield update_plugins_io(plugins)
    yield updated_plugins(success, fail)


@prog
def reboot(*plugins: str) -> NS[CrmRibosome, None]:
    return reboot_plugins(Lists.wrap(plugins)).replace(None)


__all__ = ('install_result', 'install_missing', 'update_plugins')
