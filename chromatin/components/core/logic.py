import sys
from typing import Tuple

from amino import do, __, _, Just, List, Either, Nil, Boolean, Right, Path, Lists, L, IO, Nothing
from amino.do import Do
from amino.state import State
from amino.io import IOException
from amino.func import ReplaceVal
from amino.util.string import camelcaseify, camelcase
from amino.lenses.lens import lens
from amino.case import Case
from amino.logging import module_log

from ribosome.nvim.io.state import NS
from ribosome.process import SubprocessResult, Subprocess
from ribosome.nvim.io.compute import NvimIO
from ribosome.compute.api import prog
from ribosome.compute.output import GatherSubprocesses
from ribosome.nvim.io.api import N
from ribosome.nvim.api.command import runtime, nvim_command, nvim_command_output, nvim_sync_command
from ribosome.nvim.api.exists import wait_for_command, command_exists, wait_until_function_produces
from ribosome.nvim.api.function import nvim_call_json
from ribosome.rpc.define import ActiveRpcTrigger, undef_command
from ribosome.compute.ribosome_api import Ribo
from ribosome.components.internal.prog import RpcTrigger
from ribosome.nvim.api.variable import var_becomes

from chromatin.model.venv import Venv, cons_venv, VenvMeta, cons_venv_under
from chromatin.host import start_host, stop_host
from chromatin.util import resources
from chromatin.model.rplugin import Rplugin, ActiveRplugin, DirRplugin, VenvRplugin, SiteRplugin, ActiveRpluginMeta
from chromatin.config.resources import ChromatinResources
from chromatin.rplugin import venv_package_installed
from chromatin.env import Env
from chromatin.components.core.trans.tpe import CrmRibosome
from chromatin.settings import handle_crm, venv_dir, rplugins, debug_pythonpath

log = module_log()


@do(NvimIO[List[ActiveRpcTrigger]])
def define_handlers(active_rplugin: ActiveRplugin) -> Do:
    channel = active_rplugin.channel
    cname = camelcaseify(active_rplugin.name)
    rpc_handlers_fun = f'{cname}RpcHandlers'
    result = yield N.call_once_defined(rpc_handlers_fun, timeout=3)
    handlers = (
        Lists.wrap(result)
        .flat_map(RpcHandlerSpec.decode)
        .map(lambda spec: ActiveRpcTrigger(spec=spec, channel=channel))
    )
    yield N.pure(handlers)


# FIXME handlers cannot be obtained while the plugin is initializing, as the RpcHandlers function will be reported as
# 'in use' when it is being polled during definition
# fetch handlers when using them, i.e. during shutdown
@do(NS[Env, None])
def activated(active_rplugin: ActiveRplugin) -> Do:
    log.debug(f'activated {active_rplugin}')
    spec = active_rplugin.rplugin
    yield NS.lift(runtime(f'chromatin/{spec.name}/*'))
    yield NS.modify(__.host_started(active_rplugin.meta))


@do(NvimIO[ActiveRplugin])
def start_rplugin_host(rplugin: Rplugin, python_exe: Path, bin_path: Path, plugin_path: Path) -> Do:
    debug_global = yield debug_pythonpath.value
    debug = debug_global.get_or_strict(rplugin.debug)
    channel, pid = yield start_host(python_exe, bin_path, plugin_path, debug, rplugin.pythonpath)
    return ActiveRplugin(rplugin, ActiveRpluginMeta(rplugin.name, channel, pid))


@do(NvimIO[Venv])
def venv_from_rplugin(rplugin: VenvRplugin) -> Do:
    dir = yield venv_dir.value_or_default()
    yield N.from_io(cons_venv_under(dir, rplugin))


class activate_rplugin_io(Case[Rplugin, NvimIO[ActiveRplugin]], alg=Rplugin):

    def dir_rplugin(self, rplugin: DirRplugin) -> NvimIO[ActiveRplugin]:
        python_exe = Path(sys.executable)
        bin_path = python_exe.parent
        plugin_path = Path(rplugin.spec) / '__init__.py'
        return start_rplugin_host(rplugin, python_exe, bin_path, plugin_path)

    @do(NvimIO[ActiveRplugin])
    def venv_rplugin(self, rplugin: VenvRplugin) -> Do:
        venv = yield venv_from_rplugin(rplugin)
        python_exe = yield N.from_either(venv.meta.python_executable)
        bin_path = yield N.from_either(venv.meta.bin_path)
        yield start_rplugin_host(venv.rplugin, python_exe, bin_path, venv.plugin_path)

    # TODO start with module
    def site_rplugin(self, rplugin: SiteRplugin) -> NvimIO[ActiveRplugin]:
        return N.error('site rplugins not implemented yet')


@do(NS[ChromatinResources, None])
def activate_rplugin(rplugin: Rplugin) -> Do:
    active_rplugin = yield NS.lift(activate_rplugin_io.match(rplugin))
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


@do(NvimIO[None])
def undef_trigger(trigger: RpcTrigger) -> Do:
    method = undef_command.match(trigger.method)
    yield method.map(lambda a: nvim_command(a, trigger.name)).get_or_strict(N.unit)


@do(NvimIO[None])
def stop_rplugin(name: str, channel: int, triggers: List[RpcTrigger]) -> Do:
    yield nvim_command(f'{camelcase(name)}Quit')
    yield triggers.traverse(undef_trigger, NvimIO)
    yield nvim_command('autocmd!', name)
    yield stop_host(channel)


@do(NS[Env, None])
def deactivate_rplugin(active_rplugin: ActiveRplugin) -> Do:
    rplugin = active_rplugin.rplugin
    meta = active_rplugin.meta
    cname = camelcaseify(rplugin.name)
    rpc_triggers_fun = f'{cname}RpcTriggers'
    triggers = yield NS.lift(nvim_call_json(rpc_triggers_fun))
    yield NS.modify(__.deactivate_rplugin(meta))
    yield NS.lift(stop_rplugin(rplugin.name, meta.channel, triggers))
    log.debug(f'deactivated {active_rplugin}')
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


# TODO don't fail if one plugin doesn't start
@do(NS[Env, None])
def activation_complete() -> Do:
    rplugins = yield NS.inspect_either(_.uninitialized_rplugins)
    prefixes = rplugins / _.name / camelcase
    def wait() -> NvimIO[None]:
        return prefixes.traverse(lambda p: wait_until_function_produces(True, f'{p}Poll'), NvimIO)
    @do(NvimIO[None])
    def rplugin_stage(prefix: str, num: int) -> Do:
        cmd = f'{prefix}Stage{num}'
        exists = yield command_exists(cmd)
        if exists:
            yield nvim_command(cmd)
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


@do(Either[str, Subprocess[Venv]])
def install_venv(venv: Venv) -> Do:
    log.debug(f'installing {venv}')
    bin_path = yield venv.meta.bin_path
    pip_bin = bin_path / 'pip'
    args = List('install', '-U', '--no-cache', venv.req)
    yield Right(Subprocess(pip_bin, args, venv, timeout=60))


@prog.subproc.gather
@do(NS[Env, GatherSubprocesses[Venv]])
def install_plugins_procs(venvs: List[Venv], update: Boolean) -> Do:
    action = 'updating' if update else 'installing'
    log.debug(f'{action} venvs: {venvs}')
    procs = yield NS.from_either(venvs.traverse(install_venv, Either))
    return GatherSubprocesses(procs, timeout=60)


@prog
def install_plugins_result(results: List[Either[IOException, SubprocessResult[Venv]]]
                           ) -> NS[Env, Tuple[List[Venv], List[str]]]:
    venvs = results.flat_map(__.cata(ReplaceVal(Nil), List))
    errors = results.flat_map(__.cata(List, ReplaceVal(Nil)))
    log.debug(f'installed plugins: {venvs}')
    if errors:
        log.debug(f'error installing plugins: {errors}')
    return NS.pure((venvs, errors))


@prog.do(None)
def install_plugins(venvs: List[Venv], update: Boolean) -> Do:
    result = yield install_plugins_procs(venvs, update)
    yield install_plugins_result(result)


@do(NS[CrmRibosome, None])
def add_crm_venv() -> Do:
    handle = yield Ribo.setting(handle_crm)
    if handle:
        log.debug('adding chromatin venv')
        plugin = Rplugin.simple('chromatin')
        yield Ribo.modify_main(__.set.chromatin_rplugin(Just(plugin)))
        dir = yield Ribo.setting(venv_dir)
        venv = yield NS.from_io(cons_venv(dir, plugin))
        yield Ribo.modify_main(__.set.chromatin_venv(Just(venv)))


@do(NS[Env, List[Rplugin]])
def read_conf() -> Do:
    plugin_conf = yield Ribo.setting(rplugins)
    specs = plugin_conf.traverse(Rplugin.from_config, Either)
    yield NS.from_either(specs)


@do(NS[Env, List[Rplugin]])
def rplugins_with_crm() -> Do:
    rplugins = yield NS.inspect(_.rplugins)
    crm = yield NS.inspect(_.chromatin_rplugin)
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


@prog
@do(NS[CrmRibosome, List[Venv]])
def missing_plugins() -> Do:
    dir = yield Ribo.setting(venv_dir)
    venv_metas = yield Ribo.inspect_main(_.venvs.v)
    venvs = yield Ribo.zoom_main(venv_metas.traverse(L(venv_from_meta)(dir, _), NS))
    package_status = yield NS.from_io(venvs.traverse(venv_package_installed, IO))
    return venvs.zip(package_status).collect(lambda a: Nothing if a[1] else Just(a[0]))


__all__ = ('add_crm_venv', 'read_conf', 'install_plugins', 'add_installed', 'missing_plugins')
