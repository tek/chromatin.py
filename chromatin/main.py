from amino import List, Just

from ribosome import NvimFacade
from ribosome.machine.state import UnloopedRootMachine

from chromatin.env import Env
from chromatin.logging import Logging
from chromatin.plugin import RpluginSpec


class Chromatin(UnloopedRootMachine, Logging):
    _data_type = Env

    def __init__(self, vim: NvimFacade, plugins: List[str]) -> None:
        core = 'chromatin.plugins.core'
        UnloopedRootMachine.__init__(self, vim, plugins.cons(core))

    @property
    def init(self) -> Env:
        return Env(vim_facade=Just(self.vim), plugins=List(RpluginSpec(name=self.title, spec=self.title)))

    @property
    def title(self) -> str:
        return 'chromatin'

__all__ = ('Chromatin',)
