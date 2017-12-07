from typing import Tuple

from amino import do, __, _, Just, Maybe, List, Either, Nil, Boolean, Right, Left, Path, Lists
from amino.do import Do
from amino.state import State, EitherState
from amino.io import IOException
from amino.func import ReplaceVal
from amino.util.string import camelcaseify, camelcase

from ribosome.nvim.io import NS
from ribosome.trans.message_base import Message
from ribosome.trans.effect import GatherSubprocs
from ribosome.trans.send_message import transform_data_state
from ribosome.process import SubprocessResult
from ribosome.logging import ribo_log
from ribosome.request.rpc import DefinedHandler, RpcHandlerSpec
from ribosome.nvim import NvimIO

from chromatin import Env
from chromatin.plugin import RpluginSpec
from chromatin.venvs import VenvAbsent, VenvFacade
from chromatin.venv import Venv, ActiveVenv
from chromatin.host import start_host, stop_host
from chromatin.util import resources


@do(NvimIO[List[DefinedHandler]])
def define_handlers(active_venv: ActiveVenv) -> Do:
    venv = active_venv.venv
    name = venv.name
    channel = active_venv.channel
    cname = camelcaseify(name)
    rpc_handlers_fun = f'{cname}RpcHandlers'
    result = yield NvimIO.call_once_defined(rpc_handlers_fun, timeout=3)
    handlers = (
        Lists.wrap(result)
        .flat_map(RpcHandlerSpec.decode)
        .map(lambda spec: DefinedHandler(spec=spec, channel=channel))
    )
    yield NvimIO.pure(handlers)


@do(NS[Env, None])
def activated(active_venv: ActiveVenv) -> Do:
    ribo_log.debug(f'activated {active_venv}')
    venv = active_venv.venv
    yield NS.delay(__.runtime(f'chromatin/{venv.name}/*'))
    yield NS.modify(__.host_started(active_venv))
    handlers = yield NS.lift(define_handlers(active_venv))
    yield NS.modify(__.add_handlers(venv, handlers))


@do(NS[Env, ActiveVenv])
def start_venv_host(venv: Venv, python_exe: Path, bin_path: Path) -> Do:
    debug = yield NS.inspect_f(_.settings.debug_pythonpath.value_or_default)
    channel, pid = yield NS.lift(start_host(python_exe, bin_path, venv.plugin_path, debug))
    yield NS.pure(ActiveVenv(venv=venv, channel=channel, pid=pid))


@do(Either[str, NS[Env, ActiveVenv]])
def venv_activation_io(venv: Venv) -> Do:
    python_exe = yield venv.python_executable
    bin_path = yield venv.bin_path
    yield Right(start_venv_host(venv, python_exe, bin_path))


@do(NS[Env, None])
def activate_venv(venv: Venv) -> Do:
    active_env = yield venv_activation_io(venv).value_or(NS.failed)
    yield activated(active_env)


@do(NS[Env, None])
def activate_multi(venvs: List[Venv]) -> Do:
    active = yield NS.inspect(_.active_venvs)
    already_active, inactive = venvs.split(active.contains)
    yield inactive.traverse(activate_venv, NS)


@do(NS[Env, None])
def activate_by_names(plugins: List[str]) -> Do:
    getter = _.installed if plugins.empty else __.installed_by_name(plugins)
    venvs = yield NS.inspect(getter)
    yield (
        NS.error(resources.no_plugins_match_for_activation(plugins))
        if venvs.empty else
        activate_multi(venvs)
    )


def activate_all() -> NS[Env, None]:
    return activate_by_names(List())


@do(NS[Env, None])
def deactivate_venv(venv: ActiveVenv) -> Do:
    def undef(spec: RpcHandlerSpec) -> NvimIO[str]:
        return NvimIO.cmd(spec.undef_cmdline, verbose=True)
    @do(NvimIO[None])
    def run(handlers: List[RpcHandlerSpec]) -> Do:
        yield NvimIO.cmd(f'{camelcase(venv.name)}Quit')
        yield stop_host(venv.channel)
        yield handlers.traverse(undef, NvimIO)
        ribo_log.debug(f'deactivated {venv}')
    handlers = yield NS.inspect(__.handlers_for(venv.name))
    specs = (handlers | Nil) / _.spec
    yield NS.modify(__.deactivate_venv(venv))
    yield NS.lift(run(specs))


def deactivate_multi(venvs: List[ActiveVenv]) -> NS[Env, List[NvimIO[None]]]:
    return venvs.traverse(deactivate_venv, NS)


@do(NS[Env, List[NvimIO[None]]])
def deactivate_by_names(plugins: List[str]) -> Do:
    getter = _.active if plugins.empty else __.active_by_name(plugins)
    venvs = yield NS.inspect(getter)
    yield (
        NS.error(resources.no_plugins_match_for_deactivation(plugins))
        if venvs.empty else
        deactivate_multi(venvs)
    )


@do(NS[Env, None])
def reboot_plugins(plugins: List[str]) -> Do:
    yield activate_by_names(plugins)
    yield deactivate_by_names(plugins)


@do(NS[Env, None])
def activation_complete() -> Do:
    venvs = yield NS.inspect(_.uninitialized)
    prefixes = venvs / _.name / camelcase
    def stage(num: int) -> NvimIO[None]:
        return prefixes.traverse(lambda a: NvimIO.cmd_sync(f'{a}Stage{num}'), NvimIO)
    yield NS.lift(Lists.range(1, 5).traverse(stage, NvimIO))
    yield NS.modify(__.initialization_complete())


@do(NS[Env, None])
def activate_newly_installed() -> Do:
    new = yield NS.inspect(_.inactive)
    yield activate_multi(new)
    yield activation_complete()


def add_venv(venv: Venv) -> State[Env, None]:
    return State.modify(__.add_venv(venv))


def add_installed(venv: Venv) -> State[Env, None]:
    return State.modify(__.add_installed(venv))


def bootstrap(venv_facade: VenvFacade, venv: VenvAbsent) -> None:
    return venv_facade.bootstrap(venv.plugin)


@do(EitherState[Env, None])
def venv_setup_result(result: List[Either[str, Venv]]) -> Do:
    def split(z: Tuple[List[str], List[Venv]], a: Either[str, Venv]) -> Tuple[List[str], List[Venv]]:
        err, vs = z
        return a.cata((lambda e: (err.cat(e), vs)), (lambda v: (err, vs.cat(v))))
    errors, venvs = result.fold_left((Nil, Nil))(split)
    yield transform_data_state(venvs.traverse(add_venv, State)).to(EitherState)
    error = errors.map(str).join_comma
    ret = Left(f'failed to setup venvs: {error}') if errors else Right(None)
    yield EitherState.lift(ret)


def install_plugins_result(results: List[Either[IOException, SubprocessResult[Venv]]]) -> Maybe[Message]:
    venvs = results.flat_map(__.cata(ReplaceVal(Nil), List))
    errors = results.flat_map(__.cata(List, ReplaceVal(Nil)))
    return venvs, errors


# FIXME why not parallel?
@do(NS[Env, GatherSubprocs[Venv, Tuple[List[Venv], List[IOException]]]])
def install_plugins(venvs: List[Venv], update: Boolean) -> Do:
    '''run subprocesses in sequence that install packages into their venvs using pip.
    cannot be run in parallel as they seem to deadlock.
    '''
    venv_facade = yield NS.inspect_f(_.venv_facade)
    @do(Either[str, GatherSubprocs])
    def plugin_venvs(env: Env) -> Do:
        pvenvs = yield venvs.traverse(env.plugin_venv, Either)
        procs = yield pvenvs.traverse(venv_facade.install, Either)
        yield Right(GatherSubprocs(procs, install_plugins_result, timeout=60))
    pvenvs = yield NS.inspect(plugin_venvs)
    yield NS.from_either(pvenvs)


@do(NS[Env, None])
def add_crm_venv() -> Do:
    handle = yield NS.inspect_f(_.handle_crm)
    if handle:
        plugin = RpluginSpec.simple('chromatin')
        yield NS.modify(__.set.chromatin_plugin(Just(plugin)))
        venv_facade = yield NS.inspect_f(_.venv_facade)
        venv = venv_facade.cons(plugin)
        yield NS.modify(__.set.chromatin_venv(Just(venv)))


@do(NS[Env, List[RpluginSpec]])
def read_conf() -> Do:
    plugin_conf = yield NS.inspect_f(_.rplugins)
    specs = plugin_conf.traverse(RpluginSpec.from_config, Either)
    yield NS.from_either(specs)


__all__ = ('add_crm_venv', 'read_conf', 'install_plugins', 'bootstrap', 'add_installed', 'defined_handlers')
