import sys
from typing import Tuple

from amino import do, __, _, Just, Maybe, List, Either, Nil, Boolean, Right, Left, Path, Lists
from amino.do import Do
from amino.state import State, EitherState
from amino.io import IOException
from amino.func import ReplaceVal
from amino.util.string import camelcaseify, camelcase
from amino.dispatch import dispatch_alg

from ribosome.nvim.io import NS
from ribosome.trans.message_base import Message
from ribosome.trans.effect import GatherSubprocs
from ribosome.trans.send_message import transform_data_state
from ribosome.process import SubprocessResult, Subprocess
from ribosome.logging import ribo_log
from ribosome.request.rpc import DefinedHandler, RpcHandlerSpec
from ribosome.nvim import NvimIO

from chromatin import Env
from chromatin.model.venv import Venv, cons_venv
from chromatin.host import start_host, stop_host
from chromatin.util import resources
from chromatin.model.rplugin import Rplugin, ActiveRplugin, DirRplugin, VenvRplugin, SiteRplugin


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


@do(NS[Env, None])
def activated(active_rplugin: ActiveRplugin) -> Do:
    ribo_log.debug(f'activated {active_rplugin}')
    spec = active_rplugin.rplugin
    yield NS.delay(__.runtime(f'chromatin/{spec.name}/*'))
    yield NS.modify(__.host_started(active_rplugin))
    handlers = yield NS.lift(define_handlers(active_rplugin))
    yield NS.modify(__.add_handlers(spec, handlers))


@do(NS[Env, ActiveRplugin])
def start_rplugin_host(rplugin: Rplugin, python_exe: Path, bin_path: Path, plugin_path: Path) -> Do:
    debug = yield NS.inspect_f(_.settings.debug_pythonpath.value_or_default)
    channel, pid = yield NS.lift(start_host(python_exe, bin_path, plugin_path, debug))
    yield NS.pure(ActiveRplugin(rplugin, channel, pid))


class ActivateRpluginIO:

    def dir_rplugin(self, rplugin: DirRplugin) -> NS[Env, ActiveRplugin]:
        python_exe = Path(sys.executable)
        bin_path = python_exe.parent
        plugin_path = Path(rplugin.spec) / '__init__.py'
        return start_rplugin_host(rplugin, python_exe, bin_path, plugin_path)

    @do(NS[Env, ActiveRplugin])
    def venv_rplugin(self, rplugin: VenvRplugin) -> Do:
        venv = yield NS.inspect_f(__.venv(rplugin))
        python_exe = yield NS.from_either(venv.python_executable)
        bin_path = yield NS.from_either(venv.bin_path)
        yield start_rplugin_host(venv.rplugin, python_exe, bin_path, venv.plugin_path)

    # TODO start with module
    def site_rplugin(self, rplugin: SiteRplugin) -> NS[Env, ActiveRplugin]:
        return NS.error('site rplugins not implemented yet')


activate_rplugin_io = dispatch_alg(ActivateRpluginIO(), Rplugin)


@do(NS[Env, None])
def activate_rplugin(package: Rplugin) -> Do:
    active_env = yield activate_rplugin_io(package)
    yield activated(active_env)


@do(NS[Env, None])
def activate_multi(packages: List[Rplugin]) -> Do:
    active = yield NS.inspect(_.active_packages)
    already_active, inactive = packages.split(active.contains)
    yield inactive.traverse(activate_rplugin, NS)


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
def deactivate_venv(venv: ActiveRplugin) -> Do:
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


def deactivate_multi(venvs: List[ActiveRplugin]) -> NS[Env, List[NvimIO[None]]]:
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


@do(Either[str, Subprocess[Venv]])
def install_venv(venv: Venv) -> Do:
    ribo_log.debug(f'installing {venv}')
    bin_path = yield venv.bin_path
    pip_bin = bin_path / 'pip'
    args = List('install', '-U', '--no-cache', venv.req)
    yield Right(Subprocess(pip_bin, args, venv))


# FIXME why not parallel?
@do(NS[Env, GatherSubprocs[Venv, Tuple[List[Venv], List[IOException]]]])
def install_plugins(venvs: List[Venv], update: Boolean) -> Do:
    '''run subprocesses in sequence that install packages into their venvs using pip.
    cannot be run in parallel as they seem to deadlock.
    '''
    @do(Either[str, GatherSubprocs])
    def subprocs(env: Env) -> Do:
        procs = yield venvs.traverse(install_venv, Either)
        yield Right(GatherSubprocs(procs, install_plugins_result, timeout=60))
    pvenvs = yield NS.inspect(subprocs)
    yield NS.from_either(pvenvs)


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
    plugin_conf = yield NS.inspect_f(_.rplugins)
    specs = plugin_conf.traverse(Rplugin.from_config, Either)
    yield NS.from_either(specs)


__all__ = ('add_crm_venv', 'read_conf', 'install_plugins', 'add_installed')
