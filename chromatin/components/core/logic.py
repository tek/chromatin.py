import sys
from typing import Tuple

from amino import do, __, _, Just, Maybe, List, Either, Nil, Boolean, Right, Left, Path, Lists, L, IO, Nothing
from amino.do import Do
from amino.state import State, EitherState
from amino.io import IOException
from amino.func import ReplaceVal
from amino.util.string import camelcaseify, camelcase
from amino.dispatch import dispatch_alg, PatMat
from amino.json import decode_json
from amino.lenses.lens import lens

from ribosome.nvim.io import NS
from ribosome.trans.message_base import Message
from ribosome.trans.send_message import transform_data_state
from ribosome.process import SubprocessResult, Subprocess
from ribosome.logging import ribo_log
from ribosome.request.rpc import DefinedHandler, RpcHandlerSpec
from ribosome.nvim import NvimIO
from ribosome.trans.effects import GatherSubprocs
from ribosome.trans.api import trans

from chromatin import Env
from chromatin.model.venv import Venv, cons_venv, VenvMeta, cons_venv_under
from chromatin.host import start_host, stop_host
from chromatin.util import resources
from chromatin.model.rplugin import Rplugin, ActiveRplugin, DirRplugin, VenvRplugin, SiteRplugin, ActiveRpluginMeta
from chromatin.settings import setting
from chromatin.config.resources import ChromatinResources
from chromatin.rplugin import venv_package_installed


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


@do(NS[ChromatinResources, ActiveRplugin])
def start_rplugin_host(rplugin: Rplugin, python_exe: Path, bin_path: Path, plugin_path: Path) -> Do:
    debug = setting(_.debug_pythonpath)
    channel, pid = yield NS.lift(start_host(python_exe, bin_path, plugin_path, debug))
    return ActiveRplugin(rplugin, ActiveRpluginMeta(rplugin.name, channel, pid))


@do(NS[ChromatinResources, Venv])
def venv_from_rplugin(rplugin: VenvRplugin) -> Do:
    venv_dir = yield venv_dir_setting()
    yield NS.from_io(cons_venv_under(venv_dir, rplugin))


class activate_rplugin_io(PatMat, alg=Rplugin):

    def dir_rplugin(self, rplugin: DirRplugin) -> NS[Env, ActiveRplugin]:
        python_exe = Path(sys.executable)
        bin_path = python_exe.parent
        plugin_path = Path(rplugin.spec) / '__init__.py'
        return start_rplugin_host(rplugin, python_exe, bin_path, plugin_path)

    @do(NS[ChromatinResources, ActiveRplugin])
    def venv_rplugin(self, rplugin: VenvRplugin) -> Do:
        venv = yield venv_from_rplugin(rplugin)
        python_exe = yield NS.from_either(venv.meta.python_executable)
        bin_path = yield NS.from_either(venv.meta.bin_path)
        yield start_rplugin_host(venv.rplugin, python_exe, bin_path, venv.plugin_path)

    # TODO start with module
    def site_rplugin(self, rplugin: SiteRplugin) -> NS[ChromatinResources, ActiveRplugin]:
        return NS.error('site rplugins not implemented yet')


@do(NS[ChromatinResources, None])
def activate_rplugin(rplugin: Rplugin) -> Do:
    active_rplugin = yield activate_rplugin_io.match(rplugin)
    yield activated(active_rplugin).zoom(lens.data)


@do(NS[ChromatinResources, List[Rplugin]])
def activate_multi(new_rplugins: List[Rplugin]) -> Do:
    active = yield NS.inspect_either(_.active_rplugins).zoom(lens.data)
    active_rplugins = active / _.rplugin
    already_active, inactive = new_rplugins.split(active_rplugins.contains)
    yield inactive.traverse(activate_rplugin, NS).replace(already_active)


@do(NS[ChromatinResources, List[Rplugin]])
def activate_by_names(plugins: List[str]) -> Do:
    getter = _.ready_rplugins if plugins.empty else __.ready_by_name(plugins)
    rplugins = yield NS.inspect_either(getter).zoom(lens.data)
    yield (
        NS.error(resources.no_plugins_match_for_activation(plugins))
        if rplugins.empty else
        activate_multi(rplugins)
    )


def activate_all() -> NS[ChromatinResources, List[Rplugin]]:
    return activate_by_names(Nil)


@do(NS[Env, None])
def deactivate_rplugin(active_rplugin: ActiveRplugin) -> Do:
    rplugin = active_rplugin.rplugin
    meta = active_rplugin.meta
    def undef(spec: RpcHandlerSpec) -> NvimIO[str]:
        return NvimIO.cmd(spec.undef_cmdline, verbose=True)
    @do(NvimIO[None])
    def run(handlers: List[RpcHandlerSpec]) -> Do:
        yield NvimIO.cmd_sync(f'{camelcase(rplugin.name)}Quit')
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


@do(NS[ChromatinResources, List[Rplugin]])
def reboot_plugins(plugins: List[str]) -> Do:
    yield deactivate_by_names(plugins).zoom(lens.data)
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


@do(NS[ChromatinResources, None])
def activate_newly_installed() -> Do:
    new = yield NS.inspect_either(_.inactive).zoom(lens.data)
    yield activate_multi(new)
    yield activation_complete().zoom(lens.data)


def add_venv(venv: VenvMeta) -> State[Env, None]:
    return State.modify(__.add_venv(venv))


@do(State[Env, None])
def add_installed(rplugin: Rplugin) -> Do:
    yield State.modify(__.add_installed(rplugin.name))


@do(NS[Env, None])
def already_installed(venv_dir: Path, rplugin: Rplugin) -> Do:
    yield add_installed(rplugin).nvim
    if isinstance(rplugin, VenvRplugin):
        venv = yield NS.from_io(cons_venv(venv_dir, rplugin))
        yield add_venv(venv.meta).nvim


@trans.free.result(trans.st)
def install_plugins_result(results: List[Either[IOException, SubprocessResult[Venv]]]
                           ) -> NS[Env, Tuple[List[Venv], List[str]]]:
    venvs = results.flat_map(__.cata(ReplaceVal(Nil), List))
    errors = results.flat_map(__.cata(List, ReplaceVal(Nil)))
    ribo_log.debug(f'installed plugins: {venvs}')
    if errors:
        ribo_log.debug(f'error installing plugins: {errors}')
    return NS.pure((venvs, errors))


@do(Either[str, Subprocess[Venv]])
def install_venv(venv: Venv) -> Do:
    ribo_log.debug(f'installing {venv}')
    bin_path = yield venv.meta.bin_path
    pip_bin = bin_path / 'pip'
    args = List('install', '-U', '--no-cache', venv.req)
    yield Right(Subprocess(pip_bin, args, venv))


@do(Either[str, GatherSubprocs[VenvMeta, Tuple[List[Venv], List[IOException]]]])
def install_plugins(venvs: List[Venv], update: Boolean) -> Do:
    action = 'updating' if update else 'installing'
    ribo_log.debug(f'{action} venvs: {venvs}')
    procs = yield venvs.traverse(install_venv, Either)
    yield Right(GatherSubprocs(procs, install_plugins_result, timeout=60))


def venv_dir_setting() -> NS[ChromatinResources, Path]:
    return setting(_.venv_dir)


@do(NS[ChromatinResources, None])
def add_crm_venv() -> Do:
    handle = yield setting(_.handle_crm)
    if handle:
        plugin = Rplugin.simple('chromatin')
        yield NS.modify(__.set.chromatin_plugin(Just(plugin)))
        venv_dir = yield venv_dir_setting()
        yield NS.modify(__.set.chromatin_venv(Just(cons_venv(plugin, venv_dir))))


@do(NS[Env, List[Rplugin]])
def read_conf() -> Do:
    plugin_conf = yield setting(_.rplugins)
    specs = plugin_conf.traverse(Rplugin.from_config, Either)
    yield NS.from_either(specs)


@do(NS[Env, List[Rplugin]])
def rplugins_with_crm() -> Do:
    rplugins = yield NS.inspect(_.rplugins)
    crm = yield NS.inspect(_.chromatin_plugin)
    return rplugins.cons_m(crm)


@do(NS[Env, Either[str, Rplugin]])
def rplugin_by_name(name: str) -> Do:
    rplugins = yield rplugins_with_crm()
    return rplugins.find(lambda a: a.name == name).to_either(f'no rplugin with name `{name}`')


@do(NS[Env, Venv])
def venv_from_meta(venv_dir: Path, meta: VenvMeta) -> Do:
    rplugin_e = yield rplugin_by_name(meta.name)
    rplugin = yield NS.from_either(rplugin_e)
    yield NS.from_io(cons_venv_under(venv_dir, rplugin))


@do(NS[ChromatinResources, List[Venv]])
def missing_plugins() -> Do:
    venv_dir = yield venv_dir_setting()
    venv_metas = yield NS.inspect(_.venvs.v).zoom(lens.data)
    venvs = yield venv_metas.traverse(L(venv_from_meta)(venv_dir, _), NS).zoom(lens.data)
    package_status = yield NS.from_io(venvs.traverse(venv_package_installed, IO))
    return venvs.zip(package_status).collect(lambda a: Nothing if a[1] else Just(a[0]))


__all__ = ('add_crm_venv', 'read_conf', 'install_plugins', 'add_installed', 'missing_plugins')
