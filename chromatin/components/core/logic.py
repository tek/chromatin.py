import sys
from typing import Tuple

from amino import do, __, _, Just, Maybe, List, Either, Nil, Boolean, Right, Left, Path, Lists, L
from amino.do import Do
from amino.state import State, EitherState
from amino.io import IOException
from amino.func import ReplaceVal
from amino.util.string import camelcaseify, camelcase
from amino.dispatch import dispatch_alg
from amino.json import decode_json

from ribosome.nvim.io import NS
from ribosome.trans.message_base import Message
from ribosome.trans.effect import GatherSubprocs
from ribosome.trans.send_message import transform_data_state
from ribosome.process import SubprocessResult, Subprocess
from ribosome.logging import ribo_log
from ribosome.request.rpc import DefinedHandler, RpcHandlerSpec
from ribosome.nvim import NvimIO

from chromatin import Env
from chromatin.model.venv import Venv, cons_venv, VenvMeta
from chromatin.host import start_host, stop_host
from chromatin.util import resources
from chromatin.model.rplugin import Rplugin, ActiveRplugin, DirRplugin, VenvRplugin, SiteRplugin, ActiveRpluginMeta


@do(NvimIO[List[DefinedHandler]])
def define_handlers(active_rplugin: ActiveRplugin) -> Do:
    channel = active_rplugin.channel
    cname = camelcaseify(active_rplugin.name)
    rpc_handlers_fun = f'{cname}RpcHandlers'
    result = yield NvimIO.call_once_defined(rpc_handlers_fun, timeout=3)
    handlers = (
        Lists.wrap(result)
        .flat_map(RpcHandlerSpec.decode)
        .map(lambda spec: DefinedHandler(spec=spec, channel=channel))
    )
    yield NvimIO.pure(handlers)


# FIXME handlers cannot be obtained while the plugin is initializing, as the RpcHandlers function will be reported as
# 'in use' when it is being polled during definition
# fetch handlers when using them, i.e. during shutdown
@do(NS[Env, None])
def activated(active_rplugin: ActiveRplugin) -> Do:
    ribo_log.debug(f'activated {active_rplugin}')
    spec = active_rplugin.rplugin
    yield NS.delay(__.runtime(f'chromatin/{spec.name}/*'))
    yield NS.modify(__.host_started(active_rplugin.meta))


@do(NS[Env, ActiveRplugin])
def start_rplugin_host(rplugin: Rplugin, python_exe: Path, bin_path: Path, plugin_path: Path) -> Do:
    debug = yield NS.inspect_f(_.settings.debug_pythonpath.value_or_default)
    channel, pid = yield NS.lift(start_host(python_exe, bin_path, plugin_path, debug))
    yield NS.pure(ActiveRplugin(rplugin, ActiveRpluginMeta(rplugin.name, channel, pid)))


class ActivateRpluginIO:

    def dir_rplugin(self, rplugin: DirRplugin) -> NS[Env, ActiveRplugin]:
        python_exe = Path(sys.executable)
        bin_path = python_exe.parent
        plugin_path = Path(rplugin.spec) / '__init__.py'
        return start_rplugin_host(rplugin, python_exe, bin_path, plugin_path)

    @do(NS[Env, ActiveRplugin])
    def venv_rplugin(self, rplugin: VenvRplugin) -> Do:
        venv = yield NS.inspect_f(__.venv_from_rplugin(rplugin))
        python_exe = yield NS.from_either(venv.meta.python_executable)
        bin_path = yield NS.from_either(venv.meta.bin_path)
        yield start_rplugin_host(venv.rplugin, python_exe, bin_path, venv.plugin_path)

    # TODO start with module
    def site_rplugin(self, rplugin: SiteRplugin) -> NS[Env, ActiveRplugin]:
        return NS.error('site rplugins not implemented yet')


activate_rplugin_io = dispatch_alg(ActivateRpluginIO(), Rplugin)


@do(NS[Env, None])
def activate_rplugin(rplugin: Rplugin) -> Do:
    active_rplugin = yield activate_rplugin_io(rplugin)
    yield activated(active_rplugin)


@do(NS[Env, List[Rplugin]])
def activate_multi(new_rplugins: List[Rplugin]) -> Do:
    active = yield NS.inspect_either(_.active_rplugins)
    active_rplugins = active / _.rplugin
    already_active, inactive = new_rplugins.split(active_rplugins.contains)
    yield inactive.traverse(activate_rplugin, NS).replace(already_active)


@do(NS[Env, List[Rplugin]])
def activate_by_names(plugins: List[str]) -> Do:
    getter = _.ready_rplugins if plugins.empty else __.ready_by_name(plugins)
    rplugins = yield NS.inspect_either(getter)
    yield (
        NS.error(resources.no_plugins_match_for_activation(plugins))
        if rplugins.empty else
        activate_multi(rplugins)
    )


def activate_all() -> NS[Env, List[Rplugin]]:
    return activate_by_names(Nil)


@do(NS[Env, None])
def deactivate_rplugin(active_rplugin: ActiveRplugin) -> Do:
    rplugin = active_rplugin.rplugin
    meta = active_rplugin.meta
    def undef(spec: RpcHandlerSpec) -> NvimIO[str]:
        return NvimIO.cmd(spec.undef_cmdline, verbose=True)
    @do(NvimIO[None])
    def run(handlers: List[RpcHandlerSpec]) -> Do:
        yield NvimIO.cmd(f'{camelcase(rplugin.name)}Quit')
        yield stop_host(meta.channel)
        yield handlers.traverse(undef, NvimIO)
        ribo_log.debug(f'deactivated {active_rplugin}')
    cname = camelcaseify(rplugin.name)
    rpc_handlers_fun = f'{cname}RpcHandlers'
    result = yield NS.call(rpc_handlers_fun)
    handlers = yield NS.from_either(result // decode_json)
    yield NS.modify(__.deactivate_rplugin(meta))
    yield NS.lift(run(handlers))
    yield NS.pure(None)


def deactivate_multi(rplugins: List[ActiveRplugin]) -> NS[Env, None]:
    return rplugins.traverse(deactivate_rplugin, NS).replace(None)


@do(NS[Env, None])
def deactivate_by_names(plugins: List[str]) -> Do:
    getter = _.active_rplugins if plugins.empty else __.active_rplugins_by_name(plugins)
    rplugins = yield NS.inspect_either(getter)
    yield (
        NS.error(resources.no_plugins_match_for_deactivation(plugins))
        if rplugins.empty else
        deactivate_multi(rplugins)
    )


@do(NS[Env, List[Rplugin]])
def reboot_plugins(plugins: List[str]) -> Do:
    yield deactivate_by_names(plugins)
    yield activate_by_names(plugins)


@do(NS[Env, None])
def activation_complete() -> Do:
    rplugins = yield NS.inspect_either(_.uninitialized_rplugins)
    prefixes = rplugins / _.name / camelcase
    def wait() -> NvimIO[None]:
        return prefixes.traverse(lambda p: NvimIO.delay(__.wait_for_command(f'{p}Poll')), NvimIO)
    @do(NvimIO[None])
    def rplugin_stage(prefix: str, num: int) -> Do:
        cmd = f'{prefix}Stage{num}'
        exists = yield NvimIO.delay(__.command_exists(cmd))
        if exists:
            yield NvimIO.cmd_sync(cmd)
    def stage(num: int) -> NvimIO[None]:
        return prefixes.traverse(L(rplugin_stage)(_, num), NvimIO)
    yield NS.lift(wait())
    yield NS.lift(Lists.range(1, 5).traverse(stage, NvimIO))
    yield NS.modify(__.initialization_complete())


@do(NS[Env, None])
def activate_newly_installed() -> Do:
    new = yield NS.inspect_either(_.inactive)
    yield activate_multi(new)
    yield activation_complete()


def add_venv(venv: VenvMeta) -> State[Env, None]:
    return State.modify(__.add_venv(venv))


@do(State[Env, None])
def add_installed(rplugin: Rplugin) -> Do:
    yield State.modify(__.add_installed(rplugin.name))


@do(State[Env, None])
def already_installed(venv_dir: Path, rplugin: Rplugin) -> Do:
    yield add_installed(rplugin)
    if isinstance(rplugin, VenvRplugin):
        yield add_venv(cons_venv(venv_dir, rplugin).meta)


@do(EitherState[Env, None])
def venv_setup_result(result: List[Either[str, Venv]]) -> Do:
    def split(z: Tuple[List[str], List[Venv]], a: Either[str, Venv]) -> Tuple[List[str], List[Venv]]:
        err, vs = z
        return a.cata((lambda e: (err.cat(e), vs)), (lambda v: (err, vs.cat(v))))
    errors, venvs = result.fold_left((Nil, Nil))(split)
    yield transform_data_state(venvs.map(_.meta).traverse(add_venv, State)).to(EitherState)
    error = errors.map(str).join_comma
    ret = Left(f'failed to setup venvs: {error}') if errors else Right(None)
    yield EitherState.lift(ret)


def install_plugins_result(results: List[Either[IOException, SubprocessResult[Venv]]]) -> Maybe[Message]:
    venvs = results.flat_map(__.cata(ReplaceVal(Nil), List))
    errors = results.flat_map(__.cata(List, ReplaceVal(Nil)))
    ribo_log.debug(f'installed plugins: {venvs}')
    if errors:
        ribo_log.debug(f'error installing plugins: {errors}')
    return venvs, errors


@do(Either[str, Subprocess[Venv]])
def install_venv(venv: Venv) -> Do:
    ribo_log.debug(f'installing {venv}')
    bin_path = yield venv.meta.bin_path
    pip_bin = bin_path / 'pip'
    args = List('install', '-U', '--no-cache', venv.req)
    yield Right(Subprocess(pip_bin, args, venv))


@do(Either[str, GatherSubprocs[VenvMeta, Tuple[List[Venv], List[IOException]]]])
def install_plugins(venvs: List[Venv], update: Boolean) -> Do:
    procs = yield venvs.traverse(install_venv, Either)
    yield Right(GatherSubprocs(procs, install_plugins_result, timeout=60))


@do(NS[Env, None])
def add_crm_venv() -> Do:
    handle = yield NS.inspect_f(_.handle_crm)
    if handle:
        plugin = Rplugin.simple('chromatin')
        yield NS.modify(__.set.chromatin_plugin(Just(plugin)))
        venv_dir = yield NS.inspect_f(_.venv_dir)
        yield NS.modify(__.set.chromatin_venv(Just(cons_venv(plugin, venv_dir))))


@do(NS[Env, List[Rplugin]])
def read_conf() -> Do:
    plugin_conf = yield NS.inspect_f(_.rplugins_setting)
    specs = plugin_conf.traverse(Rplugin.from_config, Either)
    yield NS.from_either(specs)


__all__ = ('add_crm_venv', 'read_conf', 'install_plugins', 'add_installed')
