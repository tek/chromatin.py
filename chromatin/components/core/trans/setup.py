from typing import Tuple

from amino import do, __, List, _, Boolean, L, Either, Nil, Right, Left, IO
from amino.do import Do
from amino.state import State, EitherState
from amino.lenses.lens import lens
from ribosome.nvim.io import NS
from ribosome.trans.api import trans
from ribosome.trans.action import TransM, Info, LogMessage
from ribosome.trans.effects import GatherIOs
from ribosome import ribo_log

from chromatin.components.core.logic import (add_crm_venv, read_conf, activate_newly_installed, already_installed,
                                             add_venv, venv_dir_setting)
from chromatin import Env
from chromatin.model.rplugin import Rplugin, cons_rplugin
from chromatin.components.core.trans.install import install_missing, install_result
from chromatin.model.rplugin import RpluginReady, VenvRplugin
from chromatin.model.venv import bootstrap, Venv
from chromatin.rplugin import rplugin_installed
from chromatin.util import resources
from chromatin.settings import setting, ensure_setting
from chromatin.config.resources import ChromatinResources


@trans.free.result(trans.st)
@do(NS[ChromatinResources, List[Rplugin]])
def init() -> Do:
    yield add_crm_venv()
    yield ensure_setting(_.rplugins, Nil)
    yield read_conf()


@trans.free.unit(trans.st)
@do(EitherState[Env, None])
def bootstrap_result(result: List[Either[str, Venv]]) -> Do:
    def split(z: Tuple[List[str], List[Venv]], a: Either[str, Venv]) -> Tuple[List[str], List[Venv]]:
        err, vs = z
        return a.cata((lambda e: (err.cat(e), vs)), (lambda v: (err, vs.cat(v))))
    errors, venvs = result.fold_left((Nil, Nil))(split)
    ribo_log.debug(f'bootstrapped venvs: {venvs}')
    yield venvs.map(_.meta).traverse(add_venv, State).to(EitherState)
    error = errors.map(str).join_comma
    ret = Left(f'failed to setup venvs: {error}') if errors else Right(None)
    yield EitherState.lift(ret)


@trans.free.unit(trans.st, trans.gather_ios)
@do(NS[ChromatinResources, GatherIOs])
def setup_venvs() -> Do:
    '''check whether a venv exists for each plugin in the env.
    for those that don't have one, create venvs in `g:chromatin_venv_dir`.
    '''
    venv_dir = yield venv_dir_setting()
    plugins = yield NS.inspect(_.rplugins).zoom(lens.data)
    rplugin_status = yield NS.from_io(plugins.traverse(rplugin_installed(venv_dir), IO))
    ready, absent = rplugin_status.split_type(RpluginReady)
    yield (ready / _.rplugin).traverse(L(already_installed)(venv_dir, _), NS).zoom(lens.data)
    absent_venvs, other = (absent / _.rplugin).split_type(VenvRplugin)
    yield NS.pure(GatherIOs(absent_venvs.map(L(bootstrap)(venv_dir, _)), bootstrap_result, timeout=30))


@trans.free.unit(trans.st)
def post_setup() -> NS[ChromatinResources, None]:
    return activate_newly_installed()


@trans.free.do()
@do(TransM)
def setup_plugins() -> Do:
    yield setup_venvs.m
    installed, errors = yield install_missing.m
    yield install_result(installed, errors).m
    yield post_setup.m


@trans.free.result(trans.st)
@do(NS[ChromatinResources, Boolean])
def add_plugins(plugins: List[Rplugin]) -> None:
    yield NS.modify(__.add_plugins(plugins)).zoom(lens.data)
    yield setting(_.autostart)


@trans.free.do()
@do(TransM)
def plugins_added(plugins: List[Rplugin]) -> Do:
    autostart = yield add_plugins(plugins).m
    if autostart:
        yield setup_plugins.m


@trans.free.do()
@do(TransM)
def stage_1() -> Do:
    plugins = yield init.m
    yield plugins_added(plugins).m


@trans.free.cons(trans.st, trans.log)
@do(NS[ChromatinResources, LogMessage])
def show_plugins() -> Do:
    venv_dir = yield venv_dir_setting()
    yield NS.inspect(lambda data: Info(resources.show_plugins(venv_dir, data.rplugins))).zoom(lens.data)


@trans.free.do()
@do(TransM)
def add_plugin(spec: str, name=None) -> Do:
    name = name or spec
    plugin = cons_rplugin(name, spec)
    yield plugins_added(List(plugin)).m


__all__ = ('stage_1', 'show_plugins')
