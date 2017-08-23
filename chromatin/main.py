from amino import List

from ribosome import NvimFacade
from ribosome.machine.state import UnloopedRootMachine

from chromatin.env import Env
from chromatin.logging import Logging


class Chromatin(UnloopedRootMachine, Logging):
    _data_type = Env

    def __init__(self, vim: NvimFacade, plugins: List[str]) -> None:
        core = 'chromatin.plugins.core'
        UnloopedRootMachine.__init__(self, vim, plugins.cons(core))

    @property
    def init(self):
        return Env(vim=self.vim)
    @property
    def title(self):
        return 'chromatin'


__all__ = ('Chromatin',)
