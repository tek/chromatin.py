from amino import List

from ribosome import NvimFacade

from chromatin.env import Env
from chromatin.state import ChromatinState


class Chromatin(ChromatinState):

    def __init__(self, vim: NvimFacade, plugins: List[str]) -> None:
        core = 'chromatin.plugins.core'
        ChromatinState.__init__(self, vim, plugins.cons(core))

    @property
    def init(self):
        return Env(vim=self.vim)

__all__ = ('Chromatin',)
