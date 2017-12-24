from amino import do, __, List, _, Boolean, L
from amino.do import Do
from amino.state import State

from ribosome.nvim.io import NS
from ribosome.trans.api import trans
from ribosome.trans.action import TransM, Info, LogMessage
from ribosome.trans.effect import GatherIOs

from chromatin.components.core.logic import (add_crm_venv, read_conf, activate_newly_installed, venv_setup_result,
                                             already_installed)
from chromatin import Env
from chromatin.model.rplugin import Rplugin, cons_rplugin
from chromatin.components.core.trans.install import install_missing, install_result
from chromatin.model.rplugin import RpluginReady, VenvRplugin
from chromatin.model.venv import bootstrap
from chromatin.rplugin import RpluginFacade
from chromatin.util import resources


@trans.free.result(trans.st)
@do(NS[Env, List[Rplugin]])
def init() -> Do:
    yield add_crm_venv()
    yield NS.delay(__.vars.set_p('started', True))
    yield NS.delay(__.vars.ensure_p('rplugins', []))
    yield read_conf()


@trans.free.unit(trans.st, trans.gather_ios, trans.st)
@do(NS[Env, GatherIOs])
def setup_venvs() -> Do:
    '''check whether a venv exists for each plugin in the env.
    for those that don't have one, create venvs in `g:chromatin_venv_dir`.
    '''
    venv_dir = yield NS.inspect_f(_.venv_dir)
    rplugin_facade = RpluginFacade(venv_dir)
    plugins = yield NS.inspect(_.rplugins)
    rplugin_status = plugins / rplugin_facade.check
    ready, absent = rplugin_status.split_type(RpluginReady)
    yield (ready / _.rplugin).traverse(L(already_installed)(venv_dir, _), State).nvim
    absent_venvs, other = (absent / _.rplugin).split_type(VenvRplugin)
    yield NS.pure(GatherIOs(absent_venvs.map(L(bootstrap)(venv_dir, _)), venv_setup_result, timeout=30))


@trans.free.unit(trans.st)
def post_setup() -> NS[Env, None]:
    return activate_newly_installed()


@trans.free.do()
@do(TransM)
def setup_plugins() -> Do:
    yield setup_venvs.m
    installed, errors = yield install_missing.m
    yield install_result(installed, errors).m
    yield post_setup.m


@trans.free.result(trans.st)
@do(NS[Env, Boolean])
def add_plugins(plugins: List[Rplugin]) -> None:
    yield NS.modify(__.add_plugins(plugins))
    yield NS.inspect_f(_.autostart)


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
@do(NS[Env, LogMessage])
def show_plugins() -> Do:
    venv_dir = yield NS.inspect_f(_.venv_dir)
    yield NS.inspect(lambda data: Info(resources.show_plugins(venv_dir, data.rplugins)))


@trans.free.do()
@do(TransM)
def add_plugin(spec: str, name=None) -> Do:
    name = name or spec
    plugin = cons_rplugin(name, spec)
    yield plugins_added(List(plugin)).m


__all__ = ('stage_1', 'show_plugins')
