from amino import do, List, _, Lists, L, Path
from amino.do import Do
from amino.boolean import false, true
from amino.io import IOException
from amino.lenses.lens import lens

from ribosome.nvim.io.state import NS
from ribosome.logging import ribo_log
from ribosome.process import SubprocessResult
from ribosome.compute.api import prog
from ribosome.compute.output import Echo
from ribosome.compute.prog import Prog
from ribosome.compute.ribosome_api import Ribo

from chromatin.components.core.logic import (install_plugins, add_installed, reboot_plugins, activate_by_names,
                                             deactivate_by_names, missing_plugins, venv_from_meta)
from chromatin.util import resources
from chromatin.model.venv import Venv, VenvMeta
from chromatin.config.resources import ChromatinResources
from chromatin.env import Env
from chromatin.settings import venv_dir, autoreboot
from chromatin.components.core.trans.tpe import CrmRibosome


@prog.echo
@do(NS[Env, Echo])
def install_result(installed: List[SubprocessResult[Venv]], errors: List[IOException]) -> Do:
    errors.foreach(lambda e: ribo_log.caught_exception('installing plugin', e))
    success, failed = installed.split(_.success)
    success_venvs = success / _.data
    failed_venvs = failed / _.data
    rplugins = success_venvs / _.rplugin
    yield rplugins.traverse(add_installed, NS)
    return (
        Echo.error(resources.plugins_install_failed(failed_venvs / _.name))
        if not failed.empty else
        Echo.unit
        if success.empty else
        Echo.info(resources.installed_plugins(success_venvs / _.name))
    )


@prog.do(None)
def install_missing() -> Do:
    missing = yield missing_plugins()
    yield install_plugins(missing, false)


@prog.echo
@do(NS[ChromatinResources, Echo])
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


@do(NS[Env, None])
def updated(result: List[Venv]) -> Do:
    venvs = result.filter_not(_.name == 'chromatin')
    reboot = yield NS.lift(autoreboot.value_or_default())
    if reboot:
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


@prog
@do(NS[CrmRibosome, List[Venv]])
def updateable_venvs(plugins: List[str]) -> Do:
    dir = yield Ribo.setting(venv_dir)
    yield Ribo.zoom_main(updateable(dir, plugins))


@prog.do(None)
def update_plugins_io(plugins: List[str]) -> Do:
    venvs = yield updateable_venvs(plugins)
    yield (
        Prog.error(resources.no_plugins_match_for_update(plugins))
        if venvs.empty else
        install_plugins(venvs, true)
    )


@prog.echo
@do(NS[ChromatinResources, Echo])
def updated_plugins(results: List[SubprocessResult[Venv]], errors: List[IOException]) -> Do:
    errors.foreach(lambda e: ribo_log.caught_exception('updating plugin', e))
    success, failed = results.split(_.success)
    success_venvs = success / _.data
    failed_venvs = failed / _.data
    yield updated(success_venvs)
    return (
        Echo.info(resources.updated_plugins(success_venvs / _.name))
        if failed.empty else
        Echo.error(resources.plugins_install_failed(failed_venvs / _.name))
    )


@prog.do(None)
def update_plugins(*ps: str) -> Do:
    plugins = Lists.wrap(ps)
    success, fail = yield update_plugins_io(plugins)
    yield updated_plugins(success, fail)


@prog
def reboot(*plugins: str) -> NS[ChromatinResources, None]:
    return reboot_plugins(Lists.wrap(plugins)).replace(None)


__all__ = ('install_result', 'install_missing', 'update_plugins')
