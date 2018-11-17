from typing import Tuple, Callable

from amino import do, Just, List, Either, Nil, Boolean, Path, Lists, IO
from amino.do import Do
from amino.state import State
from amino.io import IOException
from amino.func import ReplaceVal
from amino.util.string import camelcaseify, camelcase
from amino.case import Case
from amino.logging import module_log
from amino.list import split_by_status_zipped, split_either_list

from ribosome.nvim.io.state import NS
from ribosome.process import SubprocessResult, Subprocess
from ribosome.nvim.io.compute import NvimIO
from ribosome.compute.api import prog
from ribosome.compute.output import (GatherSubprocesses, GatherIOResult, GatherItem, GatherResult,
                                     GatherSubprocessResult, GatherIO, GatherSubprocess, Gather)
from ribosome.nvim.io.api import N
from ribosome.nvim.api.command import runtime, nvim_command
from ribosome.nvim.api.exists import command_exists, wait_until_function_produces, wait_for_function
from ribosome.nvim.api.function import nvim_call_json
from ribosome.rpc.define import ActiveRpcTrigger, undef_command
from ribosome.compute.ribosome_api import Ribo
from ribosome.components.internal.prog import RpcTrigger
from ribosome import ribo_log

from chromatin.host import stop_host
from chromatin.util import resources
from chromatin.model.rplugin import (Rplugin, ActiveRplugin, DirRplugin, DistRplugin, SiteRplugin, InstallableRplugin,
                                     InstallableRpluginMeta, DistVenvRplugin, DirVenvRplugin, StackageRplugin,
                                     HsDirRplugin, VenvRplugin, HsInstallableRplugin, HsRpluginMeta, VenvRpluginMeta,
                                     HsStackageRplugin, HsStackDirRplugin, HackageRplugin, HsHackageRplugin)
from chromatin.env import Env
from chromatin.components.core.trans.tpe import CrmRibosome
from chromatin.settings import handle_crm, venv_dir, rplugins
from chromatin.util.interpreter import join_pythonpath
from chromatin.venv import cons_venv, venv_plugin_path, venv_package_installed, venv_from_rplugin
from chromatin.model.venv import Venv
from chromatin.components.core.rplugin import installable_rplugin_from_name, installable_rplugins_from_names
from chromatin.install.main import install_rplugin_subproc
from chromatin.activate.haskell import activate_stack_plugin, activate_cabal_plugin, cabal_rplugin_executable
from chromatin.activate.host import start_rplugin_host, start_python_rplugin_host

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
    yield NS.modify(lambda a: a.host_started(active_rplugin.meta))


class activate_rplugin_io(Case[Rplugin, NvimIO[ActiveRplugin]], alg=Rplugin):

    @do(NvimIO[ActiveRplugin])
    def dir_rplugin(self, rplugin: DirRplugin) -> Do:
        venv = yield venv_from_rplugin(rplugin)
        python_exe = venv.meta.python_executable
        bin_path = venv.meta.bin_path
        plugin_path = Path(rplugin.spec) / rplugin.name / '__init__.py'
        yield start_python_rplugin_host(rplugin, python_exe, bin_path, plugin_path, List(rplugin.spec))

    @do(NvimIO[ActiveRplugin])
    def dist_rplugin(self, rplugin: DistRplugin) -> Do:
        venv = yield venv_from_rplugin(rplugin)
        plugin_path_e = yield N.from_io(venv_plugin_path(venv))
        plugin_path = yield N.e(plugin_path_e)
        python_exe = venv.meta.python_executable
        bin_path = venv.meta.bin_path
        yield start_python_rplugin_host(rplugin, python_exe, bin_path, plugin_path, Nil)

    # TODO start all plugins by passing the module path to ribosome_start_plugin instead of __init__.py
    def site_rplugin(self, rplugin: SiteRplugin) -> NvimIO[ActiveRplugin]:
        return N.error('site rplugins not implemented yet')

    def hackage(self, rplugin: HackageRplugin) -> NvimIO[ActiveRplugin]:
        return activate_cabal_plugin(rplugin, Path.home())

    def stackage(self, rplugin: StackageRplugin) -> NvimIO[ActiveRplugin]:
        return activate_stack_plugin(rplugin, Path.home())

    def hs_dir_rplugin(self, rplugin: HsDirRplugin) -> NvimIO[ActiveRplugin]:
        return activate_stack_plugin(rplugin, rplugin.spec)


@do(NS[CrmRibosome, None])
def activate_rplugin(rplugin: Rplugin) -> Do:
    active_rplugin = yield NS.lift(activate_rplugin_io.match(rplugin))
    yield Ribo.zoom_main(activated(active_rplugin))


@do(NS[CrmRibosome, List[Rplugin]])
def activate_multi(new_rplugins: List[Rplugin]) -> Do:
    active = yield Ribo.zoom_main(NS.inspect_either(lambda a: a.active_rplugins))
    active_rplugins = active.map(lambda a: a.rplugin)
    already_active, inactive = new_rplugins.split(active_rplugins.contains)
    yield inactive.traverse(activate_rplugin, NS).replace(already_active)


@do(NS[CrmRibosome, List[Rplugin]])
def activate_by_names(plugins: List[str]) -> Do:
    getter = (lambda a: a.ready_rplugins) if plugins.empty else (lambda a: a.ready_by_name(plugins))
    rplugins = yield Ribo.zoom_main(NS.inspect_either(getter))
    yield (
        NS.error(resources.no_plugins_match_for_activation(plugins))
        if rplugins.empty else
        activate_multi(rplugins)
    )


def activate_all() -> NS[CrmRibosome, List[Rplugin]]:
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
    yield NS.modify(lambda a: a.deactivate_rplugin(meta))
    yield NS.lift(stop_rplugin(rplugin.name, meta.channel, triggers))
    log.debug(f'deactivated {active_rplugin}')
    yield NS.pure(None)


def deactivate_multi(rplugins: List[ActiveRplugin]) -> NS[Env, None]:
    return rplugins.traverse(deactivate_rplugin, NS).replace(None)


@do(NS[Env, None])
def deactivate_by_names(plugins: List[str]) -> Do:
    getter = (lambda a: a.active_rplugins) if plugins.empty else (lambda a: a.active_rplugins_by_name(plugins))
    rplugins = yield NS.inspect_either(getter)
    yield (
        NS.error(resources.no_plugins_match_for_deactivation(plugins))
        if rplugins.empty else
        deactivate_multi(rplugins)
    )


@do(NS[CrmRibosome, List[Rplugin]])
def reboot_plugins(plugins: List[str]) -> Do:
    yield Ribo.zoom_main(deactivate_by_names(plugins))
    yield activate_by_names(plugins)


@do(NvimIO[None])
def rplugin_stage(prefix: str, num: int) -> Do:
    cmd = f'{prefix}Stage{num}'
    exists = yield command_exists(cmd)
    if exists:
        yield nvim_command(cmd)


def init_stage(prefixes: List[str]) -> Callable[[int], NvimIO[None]]:
    def init_stage(num: int) -> NvimIO[None]:
        return prefixes.traverse(lambda a: rplugin_stage(a, num), NvimIO)
    return init_stage


@do(NvimIO[None])
def await_poll(prefix: str) -> Do:
    yield wait_for_function(f'{prefix}Poll', 10)
    yield wait_until_function_produces(True, f'{prefix}Poll')


@do(NvimIO[List[str]])
def initialize_plugins(rplugins: List[ActiveRplugin]) -> Do:
    prefixes = rplugins.map(lambda a: camelcase(a.name))
    yield prefixes.traverse(await_poll, NvimIO)
    yield Lists.range(1, 6).traverse(init_stage(prefixes), NvimIO)
    return Nil


# TODO don't fail if one plugin doesn't start
@do(NS[Env, None])
def activation_complete() -> Do:
    rplugins = yield NS.inspect_either(lambda a: a.uninitialized_rplugins)
    tracked = rplugins.filter(lambda a: a.rplugin.track)
    failed = yield NS.lift(initialize_plugins(tracked))
    yield NS.modify(lambda a: a.initialization_complete(failed))


@do(NS[CrmRibosome, None])
def activate_newly_installed() -> Do:
    new = yield Ribo.zoom_main(NS.inspect_either(lambda a: a.inactive))
    yield activate_multi(new)
    yield Ribo.zoom_main(activation_complete())


def add_venv(name: str) -> State[Env, None]:
    return State.modify(lambda s: s if name in s.venvs else s.append1.venvs(name))


@do(State[Env, None])
def add_installed(rplugin: Rplugin) -> Do:
    yield State.modify(lambda s: s.copy(ready=s.ready.cat(rplugin).distinct))


@do(NS[Env, None])
def already_installed(venv_dir: Path, venv_rplugin: InstallableRplugin) -> Do:
    yield add_installed(venv_rplugin.rplugin).nvim
    venv = cons_venv(venv_dir, venv_rplugin.rplugin.name)
    yield add_venv(venv.meta).nvim


@prog.subproc.gather
@do(NS[Env, GatherSubprocesses[Venv]])
def install_plugins_procs(names: List[str], update: Boolean) -> Do:
    action = 'updating' if update else 'installing'
    log.debug(f'{action} rplugins: {names}')
    rplugins = yield installable_rplugins_from_names(names)
    procs = yield NS.lift(rplugins.traverse(lambda a: install_rplugin_subproc(a)(a.meta), NvimIO))
    return GatherSubprocesses(procs, timeout=600)


@prog
def install_plugins_result(results: List[Either[IOException, SubprocessResult[str]]]
                           ) -> NS[Env, Tuple[List[SubprocessResult[str]], List[str]]]:
    venvs = results.flat_map(lambda a: a.cata(ReplaceVal(Nil), List))
    errors = results.flat_map(lambda a: a.cata(List, ReplaceVal(Nil)))
    log.debug(f'installed plugins: {venvs}')
    if errors:
        log.debug(f'error installing plugins: {errors}')
    return NS.pure((venvs, errors))


@prog.do(Tuple[List[SubprocessResult[str]], List[str]])
def install_plugins(names: List[str], update: Boolean) -> Do:
    result = yield install_plugins_procs(names, update)
    yield install_plugins_result(result)


@do(NS[CrmRibosome, None])
def add_crm_venv() -> Do:
    handle = yield Ribo.setting(handle_crm)
    if handle:
        log.debug('adding chromatin venv')
        plugin = Rplugin.simple('chromatin')
        yield Ribo.modify_main(lambda a: a.set.chromatin_rplugin(Just(plugin)))
        yield Ribo.modify_main(lambda a: a.set.chromatin_venv(Just('chromatin')))


@do(NS[Env, List[Rplugin]])
def read_conf() -> Do:
    plugin_conf = yield Ribo.setting(rplugins)
    specs = plugin_conf.traverse(Rplugin.from_config, Either)
    yield NS.from_either(specs)


class venv_rplugin_healthy(
        Case[VenvRpluginMeta, NS[CrmRibosome, GatherItem[Tuple[str, bool]]]],
        alg=VenvRpluginMeta,
):

    def __init__(self, rplugin: Rplugin) -> None:
        self.rplugin = rplugin

    @do(NS[CrmRibosome, GatherItem[Tuple[str, bool]]])
    def dist(self, rplugin: DistVenvRplugin) -> Do:
        venv = yield NS.lift(venv_from_rplugin(self.rplugin))
        return GatherIO(venv_package_installed(venv).map(lambda status: (self.rplugin.name, status)))

    @do(NS[CrmRibosome, GatherItem[Tuple[str, bool]]])
    def dir(self, rplugin: DirVenvRplugin) -> Do:
        venv = yield NS.lift(venv_from_rplugin(self.rplugin))
        args = List('-c', f'import {self.rplugin.name}')
        path = join_pythonpath(self.rplugin.pythonpath.cons(rplugin.dir))
        return GatherSubprocess(
            Subprocess(str(venv.meta.python_executable), args, self.rplugin.name, timeout=1, env=dict(PYTHONPATH=path))
        )


class hs_rplugin_healthy(
        Case[HsRpluginMeta, NS[CrmRibosome, GatherItem[Tuple[str, bool]]]],
        alg=HsRpluginMeta,
):

    def __init__(self, rplugin: Rplugin) -> None:
        self.rplugin = rplugin

    def hackage(self, a: HsHackageRplugin) -> NS[CrmRibosome, GatherItem[Tuple[str, bool]]]:
        exe = cabal_rplugin_executable(self.rplugin)
        return NS.pure(GatherIO(IO.pure((self.rplugin.name, exe.is_file()))))

    def stackage(self, a: HsStackageRplugin) -> NS[CrmRibosome, GatherItem[Tuple[str, bool]]]:
        return NS.pure(GatherIO(IO.pure((self.rplugin.name, False))))

    def dir(self, a: HsStackDirRplugin) -> NS[CrmRibosome, GatherItem[Tuple[str, bool]]]:
        return NS.pure(GatherIO(IO.pure((self.rplugin.name, False))))



class rplugin_healthy(
        Case[InstallableRpluginMeta, NS[CrmRibosome, GatherItem[Tuple[str, bool]]]],
        alg=InstallableRpluginMeta,
):

    def __init__(self, rplugin: Rplugin) -> None:
        self.rplugin = rplugin

    def venv(self, meta: VenvRplugin) -> NS[CrmRibosome, GatherItem[Tuple[str, bool]]]:
        return venv_rplugin_healthy(self.rplugin)(meta)

    def hs(self, meta: HsInstallableRplugin) -> NS[CrmRibosome, GatherItem[Tuple[str, bool]]]:
        return hs_rplugin_healthy(self.rplugin)(meta)


class healthcheck_result(
        Case[GatherResult[Tuple[InstallableRplugin, bool]], Tuple[InstallableRplugin, bool]],
        alg=GatherResult,
):

    def io(self, a: GatherIOResult[Tuple[InstallableRplugin, bool]]) -> Tuple[InstallableRplugin, bool]:
        return a.result

    def subprocess(self, a: GatherSubprocessResult[Tuple[InstallableRplugin, bool]]) -> Tuple[InstallableRplugin, bool]:
        return a.result.data, a.result.retval == 0


@prog.gather
@do(NS[CrmRibosome, List[Either[IOException, GatherIOResult[Tuple[InstallableRplugin, bool]]]]])
def health_statuses() -> Do:
    dir = yield Ribo.setting(venv_dir)
    all_venvs = yield Ribo.inspect_main(lambda a: a.venvs)
    log.debug(f'running health check on venvs: {all_venvs.join_comma}')
    installable = yield Ribo.zoom_main(all_venvs.traverse(lambda a: installable_rplugin_from_name(dir, a), NS))
    gather_items = yield installable.traverse(lambda a: rplugin_healthy(a.rplugin)(a.meta), NS)
    return Gather(gather_items, 5)


@prog.do(Tuple[List[str], List[str]])
def split_plugins_by_install_status() -> Do:
    output = yield health_statuses()
    fatal, success = split_either_list(output)
    if fatal:
        ribo_log.error(f'failed to run healthcheck for plugins: {fatal.join_comma}')
    statuses = success.map(healthcheck_result.match)
    present, absent = split_by_status_zipped(statuses)
    return present, absent


def store_errors(errors: List[str]) -> Callable[[Env], Env]:
    return lambda e: e.append.errors(errors)


__all__ = ('add_crm_venv', 'read_conf', 'install_plugins', 'add_installed', 'split_plugins_by_install_status',
           'store_errors',)
