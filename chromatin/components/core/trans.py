from typing import Tuple

from amino import do, __, List, _, Boolean, L
from amino.do import Do
from amino.state import State
from amino.boolean import false
from amino.io import IOException

from ribosome.nvim.io import NS
from ribosome.trans.api import trans
from ribosome.trans.message_base import Message
from ribosome.trans.action import TransM
from ribosome.trans.effect import GatherIOs
from ribosome.trans.messages import Error, Info
from ribosome.logging import ribo_log
from ribosome.process import SubprocessResult

from chromatin.components.core.logic import (add_crm_venv, read_conf, activate_newly_installed, install_plugins,
                                             bootstrap, venv_setup_result, add_installed)
from chromatin import Env
from chromatin.plugin import RpluginSpec
from chromatin.venvs import VenvExistent
from chromatin.util import resources
from chromatin.venv import Venv


@trans.free.result(trans.st)
@do(NS[Env, Message])
def init() -> Do:
    yield add_crm_venv()
    yield NS.delay(__.vars.set_p('started', True))
    yield NS.delay(__.vars.ensure_p('rplugins', []))
    yield read_conf()


@trans.free.unit(trans.st, trans.gather_ios, trans.st)
@do(NS[Env, GatherIOs])
def setup_venvs() -> Do:
    '''check whether a venv exists for each plugin in the env.
    for those that don't, create venvs in `g:chromatin_venv_dir`.
    '''
    venv_facade = yield NS.inspect_f(_.venv_facade)
    plugins = yield NS.inspect(_.plugins)
    jobs = plugins / venv_facade.check
    existent, absent = jobs.split_type(VenvExistent)
    yield existent.traverse(add_installed, State).nvim
    yield NS.pure(GatherIOs(absent.map(L(bootstrap)(venv_facade, _)), venv_setup_result, timeout=30))


@trans.free.result(trans.st, trans.gather_subprocs)
@do(NS[Env, Tuple[List[IOException], List[Venv]]])
def install_missing() -> Do:
    missing = yield NS.inspect_f(_.missing)
    yield install_plugins(missing, false)


@trans.free.unit(trans.st)
def post_setup() -> NS[Env, List[Message]]:
    return activate_newly_installed()


@trans.free.one(trans.st)
@do(NS[Env, None])
def install_result(installed: List[SubprocessResult[Venv]], errors: List[IOException]) -> Do:
    errors.foreach(lambda e: ribo_log.caught_exception('installing venv', e))
    success, failed = installed.split(_.success)
    success_venvs = success / _.data
    failed_venvs = failed / _.data
    yield success_venvs.traverse(add_installed, State).nvim
    msg = failed.empty.c(
        lambda: Info(resources.installed_plugins(success_venvs / _.name)),
        lambda: Error(resources.plugins_install_failed(failed_venvs / _.name)),
    )
    yield NS.pure(msg)


@trans.free.do()
@do(TransM)
def setup_plugins() -> Do:
    yield setup_venvs.m
    installed, errors = yield install_missing.m
    yield install_result(installed, errors).m
    yield post_setup.m


@trans.free.result(trans.st)
@do(NS[Env, Boolean])
def add_plugins(plugins: List[RpluginSpec]) -> None:
    yield NS.modify(__.add_plugins(plugins))
    yield NS.inspect_f(_.autostart)


@trans.free.do()
@do(TransM)
def stage_1() -> Do:
    plugins = yield init.m
    autostart = yield add_plugins(plugins).m
    if autostart:
        yield setup_plugins.m


__all__ = ('stage_1',)
