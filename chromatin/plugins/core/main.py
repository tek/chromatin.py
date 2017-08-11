from chromatin.state import ChromatinTransitions, ChromatinComponent
from chromatin.plugins.core.messages import AddPlugin, ShowPlugins, StageI

from amino.state import EvalState
from amino import __, Maybe

from ribosome.machine import may_handle, Message, handle
from ribosome.machine.base import io


class CoreTransitions(ChromatinTransitions):

    @handle(StageI)
    def stage_i(self) -> Maybe[Message]:
        self.log.test('stage_i')
        return io(__.vars.set_p('started', True))

    @may_handle(AddPlugin)
    def add_plugin(self) -> Message:
        return EvalState.modify(lambda s: s.add_plugin(self.msg.spec))

    @may_handle(ShowPlugins)
    def show_plugins(self) -> Message:
        self.log.error('----------')
        self.log.info(self.data.plugins)


class Plugin(ChromatinComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
