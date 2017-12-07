from amino import do, __, List, _, Boolean, L, Map, Path
from amino.do import Do
from amino.state import State

from ribosome.nvim.io import NS
from ribosome.trans.api import trans
from ribosome.trans.message_base import Message
from ribosome.trans.action import TransM
from ribosome.trans.effect import GatherIOs
from ribosome.trans.messages import Info

from chromatin.components.core.logic import (add_crm_venv, read_conf, activate_newly_installed, bootstrap,
                                             venv_setup_result, add_installed)
from chromatin import Env
from chromatin.plugin import RpluginSpec
from chromatin.venvs import VenvExistent
from chromatin.components.core.trans.install import install_missing, install_result


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


@trans.free.unit(trans.st)
def post_setup() -> NS[Env, List[Message]]:
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


def show_plugins_message(venv_dir: Path, plugins: List[RpluginSpec]) -> str:
    venv_dir_msg = f'virtualenv dir: {venv_dir}'
    plugins_desc = plugins.map(_.spec).cons('Configured plugins:')
    return plugins_desc.cons(venv_dir_msg).join_lines


@trans.free.one(trans.st)
@do(NS[Env, Message])
def show_plugins() -> Do:
    venv_dir = yield NS.inspect_f(_.venv_dir)
    yield NS.inspect(lambda data: Info(show_plugins_message(venv_dir, data.plugins)))


@trans.free.do()
@do(NS[Env, None])
def add_plugin(spec: str, name=None) -> Do:
    name = name or spec
    plugin = RpluginSpec.cons(name, spec)
    autostart = yield add_plugins(List(plugin)).m
    if autostart:
        yield setup_plugins.m


__all__ = ('stage_1', 'show_plugins')
