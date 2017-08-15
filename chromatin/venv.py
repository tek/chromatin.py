from types import SimpleNamespace

from amino import Path, List
from amino.util.string import ToStr

from chromatin.plugin import VimPlugin


class Venv(ToStr):

    def __init__(self, dir: Path, ns: SimpleNamespace, plugin: VimPlugin) -> None:
        self.dir = dir
        self.ns = ns
        self.plugin = plugin

    @property
    def _arg_desc(self) -> List[str]:
        return List(str(self.dir), str(self.plugin))

    @property
    def req(self) -> str:
        return self.plugin.spec

__all__ = ('Venv',)
