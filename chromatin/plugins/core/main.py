from typing import Generator, TypeVar, Any

from lenses import Lens, lens

from amino.state import State, EitherState, StateT
from amino import __, do, _, Either, L, Just, List, Right, Boolean, Lists, Maybe, curried, Nothing, Path, Id
from amino.util.string import camelcaseify, camelcase
from amino.boolean import true, false
from amino.list import Nil

from ribosome.machine import Message
from ribosome.machine.base import io, RunIOsParallel, SubProcessSync
from ribosome.machine.transition import Error
from ribosome.machine import trans
from ribosome.nvim import NvimIO
from ribosome.machine.messages import Info, RunNvimIO
from ribosome.rpc import define_handler, RpcHandlerSpec, DefinedHandler, define_handlers
from ribosome.process import Result

from chromatin.state import ChromatinTransitions, ChromatinComponent
from chromatin.plugins.core.messages import (AddPlugin, ShowPlugins, Start, SetupPlugins, SetupVenvs, InstallMissing,
                                             AddVenv, IsInstalled, Activated, PostSetup, Installed, UpdatePlugins,
                                             Updated, Reboot, Activate, AlreadyActive, ReadConf, Deactivate,
                                             Deactivated, DefinedHandlers, ActivationComplete, InitializationComplete)
from chromatin.venvs import VenvExistent
from chromatin.env import Env
from chromatin.venv import Venv, ActiveVenv, PluginVenv
from chromatin.logging import Logging
from chromatin.host import start_host, stop_host
from chromatin.util import resources
from chromatin.plugin import RpluginSpec

A = TypeVar('A')
STE = StateT[Either, Env, A]
STI = StateT[Id, Env, A]
ESL = Generator[STE, Any, None]
ISL = Generator[STI, Any, None]


class PluginFunctions(Logging):

    @do
    def setup_venvs(self) -> ESL:
        '''check whether a venv exists for each plugin in the self.env.
        for those that don't, create self.venvs in `g:chromatin_venv_dir`.
        '''
        venv_facade = yield EitherState.inspect_f(_.venv_facade)
        plugins = yield EitherState.inspect(_.plugins)
        jobs = plugins / venv_facade.check
        existent, absent = jobs.split_type(VenvExistent)
        ios = absent / _.plugin / venv_facade.bootstrap / __.map(AddVenv).map(_.pub)
        yield EitherState.pure(existent.map(_.venv).map(IsInstalled).cat(RunIOsParallel(ios)))

    @do
    def install_plugins(self, venvs: List[Venv], update: Boolean) -> ESL:
        '''run subprocesses in sequence that install packages into their venvs using pip.
        cannot be run in parallel as they seem to deadlock.
        '''
        Done = update.cata(Updated, Installed)
        venv_facade = yield EitherState.inspect_f(_.venv_facade)
        def trans_result(venv: Venv, result: Result) -> Maybe[Message]:
            return Just((Done(venv) if result.success else Error(result.err)).pub)
        @do
        def install_proc(pvenv: PluginVenv) -> Generator[Either[str, SubProcessSync], Any, None]:
            job = yield venv_facade.install(pvenv)
            yield Right(SubProcessSync(job, curried(trans_result)(pvenv.venv)))
        pvenvs = yield EitherState.inspect_f(lambda env: venvs.traverse(env.plugin_venv, Right))
        yield EitherState.lift(pvenvs.traverse(install_proc, Either))

    @do
    def install_missing(self) -> ESL:
        missing = yield EitherState.inspect_f(_.missing)
        yield self.install_plugins(missing, false)

    @do
    def update_plugins(self, plugins: List[str]) -> ESL:
        getter = _.installed if plugins.empty else __.installed_by_name(plugins)
        venvs = yield EitherState.inspect(getter)
        yield (
            EitherState.pure(List(Error(resources.no_plugins_match_for_update(plugins))))
            if venvs.empty else
            self.install_plugins(venvs, true)
        )

    @do
    def start_host(self, venv: Venv, python_exe: Path) -> Generator[NvimIO[Activated], Any, None]:
        channel, pid = yield start_host(python_exe, venv.plugin_path)
        yield NvimIO.pure(List(Activated(ActiveVenv(venv=venv, channel=channel, pid=pid))))

    @do
    def activate_venv(self, venv: Venv) -> Generator[Either[str, NvimIO[Activated]], Any, None]:
        python_exe = yield venv.python_executable
        yield Right(RunNvimIO(self.start_host(venv, python_exe)))

    @do
    def activate_multi(self, venvs: List[Venv]) -> ESL:
        active = yield EitherState.inspect(_.active_venvs)
        already_active, inactive = venvs.split(active.contains)
        aa_msgs = already_active / AlreadyActive
        ios = inactive / self.activate_venv / __.value_or(Error)
        yield EitherState.pure((aa_msgs + ios).cat(ActivationComplete()))

    @do
    def activate_by_names(self, plugins: List[str]) -> ESL:
        getter = _.installed if plugins.empty else __.installed_by_name(plugins)
        venvs = yield EitherState.inspect(getter)
        yield (
            EitherState.pure(List(Error(resources.no_plugins_match_for_activation(plugins))))
            if venvs.empty else
            self.activate_multi(venvs)
        )

    def activate_all(self) -> STE:
        return self.activate_by_names(List())

    def deactivate_venv(self, venv: ActiveVenv) -> State[Env, RunNvimIO]:
        def undef(spec: RpcHandlerSpec) -> NvimIO[str]:
            return NvimIO.cmd(spec.undef_cmdline, verbose=True)
        @do
        def run(env: Env) -> Generator[NvimIO[Any], Any, None]:
            handlers = (env.handlers_for(venv.name) | Nil) / _.spec
            yield stop_host(venv.channel)
            yield handlers.traverse(undef, NvimIO)
            yield NvimIO.pure(List(Deactivated(venv)))
        return State.inspect(run) / RunNvimIO

    def deactivate_multi(self, venvs: List[ActiveVenv]) -> State[Env, List[RunNvimIO]]:
        return venvs.traverse(self.deactivate_venv, State)

    @do
    def deactivate_by_names(self, plugins: List[str]) -> ISL:
        getter = _.active if plugins.empty else __.active_by_name(plugins)
        venvs = yield State.inspect(getter)
        yield (
            State.pure(List(Error(resources.no_plugins_match_for_deactivation(plugins))))
            if venvs.empty else
            self.deactivate_multi(venvs)
        )

    @do
    def activate_newly_installed(self) -> ESL:
        new = yield EitherState.inspect(_.inactive)
        yield self.activate_multi(new)

    @do
    def define_handlers(self, active_venv: ActiveVenv) -> Generator[NvimIO[List[DefinedHandler]], Any, None]:
        venv = active_venv.venv
        name = venv.name
        channel = active_venv.channel
        cname = camelcaseify(name)
        rpc_handlers_fun = f'{cname}RpcHandlers'
        handlers_spec = RpcHandlerSpec.fun(1, rpc_handlers_fun, dict())
        handler_rpc = yield define_handler(channel, handlers_spec, name, venv.plugin_path)
        result = yield NvimIO.call_once_defined(rpc_handlers_fun, timeout=3)
        handler_specs = Lists.wrap(result).flat_map(RpcHandlerSpec.decode)
        handlers = yield define_handlers(channel, handler_specs, name, venv.plugin_path)
        yield NvimIO.pure(handlers.cons(handler_rpc))

    @do
    def add_plugins(self, plugins: List[RpluginSpec]) -> ESL:
        yield EitherState.modify(__.add_plugins(plugins))
        init = yield EitherState.inspect(_.want_init)
        yield EitherState.pure(init.m(SetupPlugins()))

    @do
    def read_conf(self) -> ESL:
        vim = yield EitherState.inspect(_.vim)
        plugins = vim.vars.pl('rplugins').flat_map(__.traverse(RpluginSpec.from_config, Either))
        yield (
            EitherState.pure(Nothing)
            if plugins.exists(_.empty) else
            plugins.map(self.add_plugins).value_or(lambda a: EitherState.pure(Just(Error(a))))
        )


class CoreTransitions(ChromatinTransitions):

    @property
    def funcs(self) -> PluginFunctions:
        return PluginFunctions()

    @trans.multi(Start)
    def stage_i(self) -> List[Message]:
        return List(io(__.vars.set_p('started', True)), io(__.vars.ensure_p('rplugins', [])), ReadConf().at(0.6).pub)

    @trans.one(ReadConf, trans.est, trans.m)
    def read_conf(self) -> EitherState[Env, Maybe[Message]]:
        return self.funcs.read_conf()

    @trans.one(AddPlugin, trans.st, trans.m)
    @do
    def add_plugin(self) -> State[Env, Maybe[Message]]:
        init = yield State.inspect(_.want_init)
        spec = self.msg.spec
        name = self.msg.options.get('name') | spec
        yield State.modify(__.add_plugin(name, spec))
        yield State.pure(init.m(SetupPlugins().at(.75)))

    @trans.one(ShowPlugins, trans.st)
    @do
    def show_plugins(self) -> State[Env, Message]:
        venv_dir = yield State.inspect(_.venv_dir)
        venv_dir_msg = f'virtualenv dir: {venv_dir.value}'
        yield State.pure(Info(self.data.show_plugins.cons(venv_dir_msg).join_lines))

    @trans.multi(SetupPlugins)
    def setup_plugins(self) -> List[Message]:
        return List(SetupVenvs(), InstallMissing().at(.9).pub, PostSetup().at(.95).pub)

    @trans.multi(SetupVenvs, trans.est)
    def setup_venvs(self) -> EitherState[Env, List[Message]]:
        return self.funcs.setup_venvs()

    @trans.multi(InstallMissing, trans.est)
    def install_missing(self) -> EitherState[Env, List[Message]]:
        return self.funcs.install_missing()

    @trans.multi(Installed, trans.st)
    def installed(self) -> State[Env, List[Message]]:
        venv = self.msg.venv
        return State.pure(List(IsInstalled(venv), Info(resources.installed_plugin(venv.name))))

    @trans.multi(Updated, trans.st)
    @do
    def updated(self) -> State[Env, List[Message]]:
        autoreboot = yield State.inspect(_.autoreboot)
        venv = self.msg.venv
        reboot = autoreboot.l(Reboot(venv.name))
        yield State.pure(reboot.cons(Info(resources.updated_plugin(venv.name))))

    @trans.unit(IsInstalled, trans.st)
    def is_installed(self) -> State[Env, None]:
        return State.modify(__.add_installed(self.msg.venv))

    @trans.multi(PostSetup, trans.est)
    def post_setup(self) -> EitherState[Env, List[Message]]:
        return self.funcs.activate_newly_installed()

    @trans.unit(AddVenv, trans.st)
    def add_venv(self) -> State[Env, None]:
        return State.modify(__.add_venv(self.msg.venv))

    @trans.multi(Activate, trans.est)
    def activate(self) -> EitherState[Env, List[Message]]:
        return self.funcs.activate_by_names(self.msg.plugins)

    @trans.multi(Deactivate, trans.st)
    def deactivate(self) -> State[Env, List[Message]]:
        return self.funcs.deactivate_by_names(self.msg.plugins)

    @trans.multi(Reboot)
    def reboot(self) -> List[Message]:
        plugins = self.msg.plugins
        return List(Deactivate(*plugins), Activate(*plugins).at(.75).pub)

    @trans.one(Activated, trans.st, trans.nio)
    @do
    def activated(self) -> State[Env, NvimIO[Message]]:
        self.log.debug(f'activated {self.msg.venv}')
        active_venv = self.msg.venv
        venv = active_venv.venv
        @do
        def io() -> NvimIO[DefinedHandlers]:
            handlers = yield self.funcs.define_handlers(active_venv)
            yield self.vim.runtime(f'chromatin/{venv.name}/*')
            yield NvimIO.pure(DefinedHandlers(venv, handlers))
        yield State.modify(__.host_started(active_venv))
        yield State.pure(io())

    @trans.one(ActivationComplete, trans.st, trans.nio)
    @do
    def activation_complete(self) -> State[Env, NvimIO[None]]:
        venvs = yield State.inspect(_.uninitialized)
        prefixes = venvs / _.name / camelcase
        def stage(num: int) -> NvimIO[None]:
            return prefixes.traverse(lambda a: NvimIO.cmd_sync(f'{a}Stage{num}'), NvimIO)
        yield State.pure(Lists.range(1, 5).traverse(stage, NvimIO).replace(InitializationComplete()))

    @trans.unit(InitializationComplete, trans.st)
    def initialization_complete(self) -> State[Env, None]:
        return State.modify(__.initialization_complete())

    @trans.unit(Deactivated, trans.st)
    def deactivated(self) -> None:
        self.log.debug(f'deactivated {self.msg.venv}')
        return State.modify(__.deactivate_venv(self.msg.venv))

    @trans.unit(DefinedHandlers, trans.st)
    def defined_handlers(self) -> State[Env, None]:
        return State.modify(__.add_handlers(self.msg.venv, self.msg.handlers))

    @trans.multi(UpdatePlugins, trans.est)
    def update_plugins(self) -> State[Env, List[Message]]:
        return self.funcs.update_plugins(self.msg.plugins)

    @trans.unit(AlreadyActive)
    def already_active(self) -> None:
        pass

    def state_lens(self, tpe: str, name: str) -> Either[str, Lens]:
        return (
            State.inspect(lambda s: s.plugins.index_where(lambda a: a.name == name) / (lambda i: lens(s).plugins[i]))
            if tpe == 'vim_plugin' else
            State.pure(Nothing)
        )


class Plugin(ChromatinComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
