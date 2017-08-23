from ribosome import NvimFacade
from ribosome.nvim import HasNvim
from ribosome.machine.state import SubMachine, SubTransitions
from ribosome.machine.base import MachineBase

from chromatin.logging import Logging


class ChromatinComponent(SubMachine, HasNvim, Logging):

    def __init__(self, vim: NvimFacade, parent=None, title=None) -> None:
        MachineBase.__init__(self, parent, title=title)
        HasNvim.__init__(self, vim)


class ChromatinTransitions(SubTransitions, HasNvim, Logging):

    def __init__(self, machine, *a, **kw):
        SubTransitions.__init__(self, machine, *a, **kw)
        HasNvim.__init__(self, machine.vim)

__all__ = ('ChromatinComponent', 'ChromatinTransitions')
