from typing import Tuple

from amino import do, __, _, Just, Maybe, List, Either, Nothing, L, Nil
from amino.do import Do
from amino.state import State

from ribosome.nvim.io import NS
from ribosome.trans.message_base import Message
from ribosome.trans.effect import GatherIOs
from ribosome.trans.send_message import transform_data_state

from chromatin import Env
from chromatin.plugin import RpluginSpec
from chromatin.venvs import VenvExistent, VenvAbsent
from chromatin.venv import Venv


def add_venv(venv: Venv) -> State[Env, None]:
    return State.modify(__.add_venv(venv))


def is_installed(venv: Venv) -> State[Env, None]:
    return State.modify(__.add_installed(venv))


def bootstrap(venv_facade, venv: VenvAbsent) -> None:
    return venv_facade.bootstrap(venv.plugin)


@do(State[Env, Maybe[Message]])
def venv_setup_result(result: List[Either[str, Venv]]) -> Do:
    def split(z: Tuple[List[str], List[Venv]], a: Either[str, Venv]) -> Tuple[List[str], List[Venv]]:
        err, vs = z
        return a.cata((lambda e: (err.cat(e), vs)), (lambda v: (err, vs.cat(v))))
    errors, venvs = result.fold_left((Nil, Nil))(split)
    yield transform_data_state(venvs.traverse(add_venv, State))
    error = errors.map(str).join_comma
    ret = Just(f'failed to setup venvs: {error}') if errors else Nothing
    yield State.pure(ret)


@do(NS[Env, GatherIOs])
def setup_venvs() -> Do:
    '''check whether a venv exists for each plugin in the env.
    for those that don't, create venvs in `g:chromatin_venv_dir`.
    '''
    venv_facade = yield NS.inspect_f(_.venv_facade)
    plugins = yield NS.inspect(_.plugins)
    jobs = plugins / venv_facade.check
    existent, absent = jobs.split_type(VenvExistent)
    yield existent.traverse(is_installed, State).nvim
    yield NS.pure(GatherIOs(absent.map(L(bootstrap)(venv_facade, _)), venv_setup_result, timeout=30))


def setup_plugins() -> NS[Env, None]:
    return setup_venvs()


@do(NS[Env, None])
def add_crm_venv() -> Do:
    handle = yield NS.inspect_f(_.handle_crm)
    if handle:
        plugin = RpluginSpec.simple('chromatin')
        yield NS.modify(__.set.chromatin_plugin(Just(plugin)))
        venv_facade = yield NS.inspect_f(_.venv_facade)
        venv = venv_facade.cons(plugin)
        yield NS.modify(__.set.chromatin_venv(Just(venv)))


@do(NS[Env, Maybe[Message]])
def add_plugins(plugins: List[RpluginSpec]) -> Do:
    yield NS.modify(__.add_plugins(plugins))
    init = yield NS.inspect_f(_.autostart)
    yield init.c(setup_plugins, lambda: NS.pure(Nothing))


@do(NS[Env, List[RpluginSpec]])
def read_conf() -> Do:
    plugin_conf = yield NS.inspect_f(_.rplugins)
    specs = plugin_conf.traverse(RpluginSpec.from_config, Either)
    yield NS.from_either(specs)


__all__ = ('add_crm_venv', 'add_plugins', 'read_conf')
