from ribosome.data import Data
from ribosome.record import dfield, list_field

from chromatin.logging import Logging
from chromatin.plugin import VimPlugin


class Env(Data, Logging):
    initialized = dfield(False)
    plugins = list_field(VimPlugin)

    def add_plugin(self, spec: str) -> 'Env':
        return self.append1.plugins(VimPlugin(name=spec))

__all__ = ('Env',)
