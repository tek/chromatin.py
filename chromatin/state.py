from ribosome import Machine, NvimFacade
from ribosome.nvim import HasNvim

from ribosome.machine.state import SubMachine, SubTransitions, UnloopedRootMachine

from chromatin.logging import Logging
from chromatin.env import Env


class ChromatinComponent(SubMachine, HasNvim, Logging):

    def __init__(self, vim: NvimFacade, parent=None, title=None) -> None:
        Machine.__init__(self, parent, title=title)
        HasNvim.__init__(self, vim)


class ChromatinState(UnloopedRootMachine, Logging):
    _data_type = Env

    @property
    def title(self):
        return 'chromatin'


class ChromatinTransitions(SubTransitions, HasNvim, Logging):

    def __init__(self, machine, *a, **kw):
        SubTransitions.__init__(self, machine, *a, **kw)
        HasNvim.__init__(self, machine.vim)

__all__ = ('ChromatinComponent', 'ChromatinState', 'ChromatinTransitions')
