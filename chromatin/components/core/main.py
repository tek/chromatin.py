from typing import Generator, TypeVar, Any

from lenses import Lens, lens

from amino.state import State, EitherState, StateT
from amino import __, do, _, Either, Just, List, Right, Boolean, Lists, Maybe, curried, Nothing, Path, Id
from amino.util.string import camelcaseify, camelcase
from amino.boolean import true, false
from amino.do import Do

from ribosome.nvim import NvimIO
from ribosome.process import Result
from ribosome.trans.message_base import Message
from ribosome.trans.messages import RunIOsParallel, Error, SubProcessSync, Quit, Info
from ribosome.dispatch.component import Component
from ribosome.trans.api import trans
from ribosome.request.rpc import RpcHandlerSpec, DefinedHandler
from ribosome.nvim.io import NS

from chromatin.components.core.messages import (AddPlugin, ShowPlugins, SetupPlugins, SetupVenvs, InstallMissing,
                                                AddVenv, IsInstalled, Activated, PostSetup, Installed, UpdatePlugins,
                                                Updated, Reboot, Activate, AlreadyActive, Deactivate,
                                                Deactivated, DefinedHandlers, ActivationComplete,
                                                InitializationComplete)
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
ESG = Generator[STE, Any, None]
ISG = Generator[STI, Any, None]


class PluginFunctions(Logging):

    @do(NS[Env, List[Message]])
    def install_plugins(self, venvs: List[Venv], update: Boolean) -> Do:
        '''run subprocesses in sequence that install packages into their venvs using pip.
        cannot be run in parallel as they seem to deadlock.
        '''
        Done = update.cata(Updated, Installed)
        venv_facade = yield NS.inspect_f(_.venv_facade)
        def trans_result(venv: Venv, result: Result) -> Maybe[Message]:
            return Just((Done(venv) if result.success else Error(result.err)).pub)
        @do(Either[str, SubProcessSync])
        def install_proc(pvenv: PluginVenv) -> Do:
            self.log.debug(f'installing {pvenv}')
            job = yield venv_facade.install(pvenv)
            yield Right(SubProcessSync(job, curried(trans_result)(pvenv.venv)))
        @do(Either[str, List[SubProcessSync]])
        def plugin_venvs(env: Env) -> Do:
            pvenvs = yield venvs.traverse(env.plugin_venv, Either)
            yield pvenvs.traverse(install_proc, Either)
        pvenvs = yield NS.inspect(plugin_venvs)
        yield NS.pure(pvenvs.value_or(Error))

    @do(NS[Env, List[Message]])
    def install_missing(self) -> Do:
        missing = yield NS.inspect_f(_.missing)
        yield self.install_plugins(missing, false)

    @do(NS[Env, List[Message]])
    def update_plugins(self, plugins: List[str]) -> Do:
        venvs = yield EitherState.inspect(__.updateable(plugins))
        yield (
            EitherState.pure(List(Error(resources.no_plugins_match_for_update(plugins))))
            if venvs.empty else
            self.install_plugins(venvs, true)
        )

    @do(NvimIO[Activated])
    def start_host(self, venv: Venv, python_exe: Path, bin_path: Path) -> Do:
        debug = yield NvimIO.delay(__.vars.pb('debug_pythonpath'))
        channel, pid = yield start_host(python_exe, bin_path, venv.plugin_path, debug.true)
        yield NvimIO.pure(List(Activated(ActiveVenv(venv=venv, channel=channel, pid=pid))))

    @do(Either[str, Any])
    # def activate_venv(self, venv: Venv) -> Generator[Either[str, RunNvimIO], Any, None]:
    def activate_venv(self, venv: Venv) -> Do:
        pass
        # python_exe = yield venv.python_executable
        # bin_path = yield venv.bin_path
        # yield Right(RunNvimIO(self.start_host(venv, python_exe, bin_path)))

    @do(ESG)
    def activate_multi(self, venvs: List[Venv]) -> Do:
        active = yield EitherState.inspect(_.active_venvs)
        already_active, inactive = venvs.split(active.contains)
        aa_msgs = already_active / AlreadyActive
        ios = inactive / self.activate_venv / __.value_or(Error)
        yield EitherState.pure((aa_msgs + ios).cat(ActivationComplete()))

    @do(ESG)
    def activate_by_names(self, plugins: List[str]) -> Do:
        getter = _.installed if plugins.empty else __.installed_by_name(plugins)
        venvs = yield EitherState.inspect(getter)
        yield (
            EitherState.pure(List(Error(resources.no_plugins_match_for_activation(plugins))))
            if venvs.empty else
            self.activate_multi(venvs)
        )

    def activate_all(self) -> STE:
        return self.activate_by_names(List())

    @do(State[Env, Any])
    def deactivate_venv(self, venv: ActiveVenv) -> Do:
        def undef(spec: RpcHandlerSpec) -> NvimIO[str]:
            return NvimIO.cmd(spec.undef_cmdline, verbose=True)
        @do(NvimIO[Any])
        def run(handlers: List[RpcHandlerSpec]) -> Do:
            yield NvimIO.cmd(f'{camelcase(venv.name)}Quit')
            yield stop_host(venv.channel)
            yield handlers.traverse(undef, NvimIO)
            yield NvimIO.pure(List(Deactivated(venv)))
        # handlers = yield State.inspect(__.handlers_for(venv.name))
        # specs = (handlers | Nil) / _.spec
        # yield State.pure(RunNvimIO(run(specs)))

    # def deactivate_multi(self, venvs: List[ActiveVenv]) -> State[Env, List[RunNvimIO]]:
    #     return venvs.traverse(self.deactivate_venv, State)

    @do(ISG)
    def deactivate_by_names(self, plugins: List[str]) -> Do:
        getter = _.active if plugins.empty else __.active_by_name(plugins)
        venvs = yield State.inspect(getter)
        yield (
            State.pure(List(Error(resources.no_plugins_match_for_deactivation(plugins))))
            if venvs.empty else
            self.deactivate_multi(venvs)
        )

    @do(ESG)
    def activate_newly_installed(self) -> Do:
        new = yield EitherState.inspect(_.inactive)
        yield self.activate_multi(new)

    @do(NvimIO[List[DefinedHandler]])
    def define_handlers(self, active_venv: ActiveVenv) -> Do:
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

    @do(ESG)
    def add_plugins(self, plugins: List[RpluginSpec]) -> Do:
        yield EitherState.modify(__.add_plugins(plugins))
        init = yield EitherState.inspect(_.autostart)
        yield EitherState.pure(init.m(SetupPlugins()))

    @do(ESG)
    def read_conf(self) -> Do:
        vim = yield EitherState.inspect(_.vim)
        plugins = vim.vars.pl('rplugins').flat_map(__.traverse(RpluginSpec.from_config, Either))
        yield (
            EitherState.pure(Nothing)
            if plugins.exists(_.empty) else
            plugins.map(self.add_plugins).value_or(lambda a: EitherState.pure(Just(Error(a))))
        )

    @do(ESG)
    def add_crm_venv(self) -> Do:
        handle = yield EitherState.inspect(_.handle_crm)
        if handle:
            plugin = RpluginSpec.simple('chromatin')
            yield EitherState.modify(__.set.chromatin_plugin(Just(plugin)))
            venv_facade = yield EitherState.inspect_f(_.venv_facade)
            venv = venv_facade.cons(plugin)
            yield State.modify(__.set.chromatin_venv(Just(venv)))


class Core(Component):

    @property
    def funcs(self) -> PluginFunctions:
        return PluginFunctions()

    @trans.msg.unit(Quit)
    def quit(self) -> None:
        pass

    @trans.msg.one(AddPlugin, trans.st, trans.m)
    @do(State[Env, Maybe[Message]])
    def add_plugin(self, msg: AddPlugin) -> Do:
        init = yield State.inspect(_.autostart)
        spec = msg.spec
        name = msg.options.get('name') | spec
        yield State.modify(__.add_plugin(name, spec))
        yield State.pure(init.m(SetupPlugins().at(.75)))

    @trans.msg.one(ShowPlugins, trans.st)
    @do(State[Env, Message])
    def show_plugins(self) -> Do:
        venv_dir = yield State.inspect(_.venv_dir)
        venv_dir_msg = f'virtualenv dir: {venv_dir.value}'
        yield State.pure(Info(self.data.show_plugins.cons(venv_dir_msg).join_lines))

    @trans.msg.multi(SetupPlugins)
    def setup_plugins(self, msg: SetupPlugins) -> List[Message]:
        return List(SetupVenvs(), InstallMissing().at(.9), PostSetup().at(.95))

    @trans.msg.multi(SetupVenvs, trans.st)
    def setup_venvs(self, msg: SetupVenvs) -> EitherState[Env, List[Message]]:
        return self.funcs.setup_venvs()

    @trans.msg.multi(InstallMissing, trans.st)
    def install_missing(self, msg: InstallMissing) -> EitherState[Env, List[Message]]:
        return self.funcs.install_missing()

    @trans.msg.multi(Installed, trans.st)
    def installed(self, msg: Installed) -> State[Env, List[Message]]:
        venv = msg.venv
        return State.pure(List(IsInstalled(venv), Info(resources.installed_plugin(venv.name))))

    @trans.msg.multi(Updated, trans.st)
    @do(State[Env, List[Message]])
    def updated(self, msg: Updated) -> Do:
        autoreboot = yield State.inspect(_.autoreboot)
        venv = msg.venv
        need_reboot = autoreboot & Boolean(venv.name != 'chromatin')
        reboot = need_reboot.l(Reboot(venv.name))
        yield State.pure(reboot.cons(Info(resources.updated_plugin(venv.name))))

    @trans.msg.multi(PostSetup, trans.st)
    def post_setup(self, msg: PostSetup) -> EitherState[Env, List[Message]]:
        return self.funcs.activate_newly_installed()

    @trans.msg.unit(AddVenv, trans.st)
    def add_venv(self, msg: AddVenv) -> State[Env, None]:
        return State.modify(__.add_venv(msg.venv))

    @trans.msg.multi(Activate, trans.st)
    def activate(self, msg: Activate) -> EitherState[Env, List[Message]]:
        return self.funcs.activate_by_names(msg.plugins)

    @trans.msg.multi(Deactivate, trans.st)
    def deactivate(self, msg: Deactivate) -> State[Env, List[Message]]:
        return self.funcs.deactivate_by_names(msg.plugins)

    @trans.msg.multi(Reboot)
    def reboot(self, msg: Reboot) -> List[Message]:
        plugins = msg.plugins
        return List(Deactivate(*plugins), Activate(*plugins).at(.75).pub)

    @trans.msg.one(Activated, trans.st, trans.nio)
    @do(State[Env, NvimIO[Message]])
    def activated(self, msg: Activated) -> Do:
        self.log.debug(f'activated {msg.venv}')
        active_venv = msg.venv
        venv = active_venv.venv
        @do(NvimIO[DefinedHandlers])
        def io() -> Do:
            handlers = yield self.funcs.define_handlers(active_venv)
            yield self.vim.runtime(f'chromatin/{venv.name}/*')
            yield NvimIO.pure(DefinedHandlers(venv, handlers))
        yield State.modify(__.host_started(active_venv))
        yield State.pure(io())

    @trans.msg.one(ActivationComplete, trans.st, trans.nio)
    @do(State[Env, NvimIO[None]])
    def activation_complete(self, msg: ActivationComplete) -> Do:
        venvs = yield State.inspect(_.uninitialized)
        prefixes = venvs / _.name / camelcase
        def stage(num: int) -> NvimIO[None]:
            return prefixes.traverse(lambda a: NvimIO.cmd_sync(f'{a}Stage{num}'), NvimIO)
        yield State.pure(Lists.range(1, 5).traverse(stage, NvimIO).replace(InitializationComplete()))

    @trans.msg.unit(InitializationComplete, trans.st)
    def initialization_complete(self, msg: InitializationComplete) -> State[Env, None]:
        return State.modify(__.initialization_complete())

    @trans.msg.unit(Deactivated, trans.st)
    def deactivated(self, msg: Deactivated) -> None:
        self.log.debug(f'deactivated {msg.venv}')
        return State.modify(__.deactivate_venv(msg.venv))

    @trans.msg.unit(DefinedHandlers, trans.st)
    def defined_handlers(self, msg: DefinedHandlers) -> State[Env, None]:
        return State.modify(__.add_handlers(msg.venv, msg.handlers))

    @trans.msg.multi(UpdatePlugins, trans.st)
    def update_plugins(self, msg: UpdatePlugins) -> State[Env, List[Message]]:
        return self.funcs.update_plugins(msg.plugins)

    @trans.msg.unit(AlreadyActive)
    def already_active(self) -> None:
        pass

    def state_lens(self, tpe: str, name: str) -> Either[str, Lens]:
        return (
            State.inspect(lambda s: s.plugins.index_where(lambda a: a.name == name) / (lambda i: lens(s).plugins[i]))
            if tpe == 'vim_plugin' else
            State.pure(Nothing)
        )


__all__ = ('Core',)
