from typing import Generator, TypeVar, Any

from lenses import Lens, lens

from amino.state import State, EitherState, StateT
from amino import __, do, _, Either, Just, List, Right, Boolean, Lists, Maybe, curried, Nothing, Path, Id
from amino.util.string import camelcaseify, camelcase
from amino.do import Do

from ribosome.nvim import NvimIO
from ribosome.trans.message_base import Message
from ribosome.trans.messages import Info
from ribosome.dispatch.component import Component
from ribosome.trans.api import trans

from chromatin.env import Env
from chromatin.util import resources

A = TypeVar('A')
STE = StateT[Either, Env, A]
STI = StateT[Id, Env, A]
ESG = Generator[STE, Any, None]
ISG = Generator[STI, Any, None]


class Core(Component):
    pass

    # @trans.msg.one(AddPlugin, trans.st, trans.m)
    # @do(State[Env, Maybe[Message]])
    # def add_plugin(self, msg: AddPlugin) -> Do:
    #     init = yield State.inspect(_.autostart)
    #     spec = msg.spec
    #     name = msg.options.get('name') | spec
    #     yield State.modify(__.add_plugin(name, spec))
    #     yield State.pure(init.m(SetupPlugins().at(.75)))

    # @trans.msg.one(ShowPlugins, trans.st)
    # @do(State[Env, Message])
    # def show_plugins(self) -> Do:
    #     venv_dir = yield State.inspect(_.venv_dir)
    #     venv_dir_msg = f'virtualenv dir: {venv_dir.value}'
    #     yield State.pure(Info(self.data.show_plugins.cons(venv_dir_msg).join_lines))

    # @trans.msg.multi(InstallMissing, trans.st)
    # def install_missing(self, msg: InstallMissing) -> EitherState[Env, List[Message]]:
    #     return self.funcs.install_missing()

    # @trans.msg.multi(Installed, trans.st)
    # def installed(self, msg: Installed) -> State[Env, List[Message]]:
    #     venv = msg.venv
    #     return State.pure(List(IsInstalled(venv), Info(resources.installed_plugin(venv.name))))

    # @trans.msg.multi(Updated, trans.st)
    # @do(State[Env, List[Message]])
    # def updated(self, msg: Updated) -> Do:
    #     autoreboot = yield State.inspect(_.autoreboot)
    #     venv = msg.venv
    #     need_reboot = autoreboot & Boolean(venv.name != 'chromatin')
    #     reboot = need_reboot.l(Reboot(venv.name))
    #     yield State.pure(reboot.cons(Info(resources.updated_plugin(venv.name))))

    # @trans.msg.multi(PostSetup, trans.st)
    # def post_setup(self, msg: PostSetup) -> EitherState[Env, List[Message]]:
    #     return self.funcs.activate_newly_installed()

    # @trans.msg.unit(AddVenv, trans.st)
    # def add_venv(self, msg: AddVenv) -> State[Env, None]:
    #     return State.modify(__.add_venv(msg.venv))

    # @trans.msg.multi(Activate, trans.st)
    # def activate(self, msg: Activate) -> EitherState[Env, List[Message]]:
    #     return self.funcs.activate_by_names(msg.plugins)

    # @trans.msg.multi(Deactivate, trans.st)
    # def deactivate(self, msg: Deactivate) -> State[Env, List[Message]]:
    #     return self.funcs.deactivate_by_names(msg.plugins)

    # @trans.msg.multi(Reboot)
    # def reboot(self, msg: Reboot) -> List[Message]:
    #     plugins = msg.plugins
    #     return List(Deactivate(*plugins), Activate(*plugins).at(.75).pub)

    # @trans.msg.one(Activated, trans.st, trans.nio)
    # @do(State[Env, NvimIO[Message]])
    # def activated(self, msg: Activated) -> Do:
    #     self.log.debug(f'activated {msg.venv}')
    #     active_venv = msg.venv
    #     venv = active_venv.venv
    #     @do(NvimIO[DefinedHandlers])
    #     def io() -> Do:
    #         handlers = yield self.funcs.define_handlers(active_venv)
    #         yield self.vim.runtime(f'chromatin/{venv.name}/*')
    #         yield NvimIO.pure(DefinedHandlers(venv, handlers))
    #     yield State.modify(__.host_started(active_venv))
    #     yield State.pure(io())

    # @trans.msg.one(ActivationComplete, trans.st, trans.nio)
    # @do(State[Env, NvimIO[None]])
    # def activation_complete(self, msg: ActivationComplete) -> Do:
    #     venvs = yield State.inspect(_.uninitialized)
    #     prefixes = venvs / _.name / camelcase
    #     def stage(num: int) -> NvimIO[None]:
    #         return prefixes.traverse(lambda a: NvimIO.cmd_sync(f'{a}Stage{num}'), NvimIO)
    #     yield State.pure(Lists.range(1, 5).traverse(stage, NvimIO).replace(InitializationComplete()))

    # @trans.msg.unit(InitializationComplete, trans.st)
    # def initialization_complete(self, msg: InitializationComplete) -> State[Env, None]:
    #     return State.modify(__.initialization_complete())

    # @trans.msg.unit(Deactivated, trans.st)
    # def deactivated(self, msg: Deactivated) -> None:
    #     return State.modify(__.deactivate_venv(msg.venv))

    # @trans.msg.unit(DefinedHandlers, trans.st)
    # def defined_handlers(self, msg: DefinedHandlers) -> State[Env, None]:
    #     return State.modify(__.add_handlers(msg.venv, msg.handlers))

    # @trans.msg.multi(UpdatePlugins, trans.st)
    # def update_plugins(self, msg: UpdatePlugins) -> State[Env, List[Message]]:
    #     return self.funcs.update_plugins(msg.plugins)

    # @trans.msg.unit(AlreadyActive)
    # def already_active(self) -> None:
    #     pass

    # def state_lens(self, tpe: str, name: str) -> Either[str, Lens]:
    #     return (
    #         State.inspect(lambda s: s.plugins.index_where(lambda a: a.name == name) / (lambda i: lens(s).plugins[i]))
    #         if tpe == 'vim_plugin' else
    #         State.pure(Nothing)
    #     )


__all__ = ('Core',)
