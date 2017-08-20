from types import SimpleNamespace

from amino import Path, List, Try, Either
from amino.util.string import ToStr

from chromatin.plugin import VimPlugin


class Venv(ToStr):

    def __init__(self, dir: Path, ns: SimpleNamespace, plugin: VimPlugin) -> None:
        self.dir = dir
        self.ns = ns
        self.plugin = plugin

    def _arg_desc(self) -> List[str]:
        return List(str(self.dir), str(self.plugin))

    @property
    def req(self) -> str:
        return self.plugin.spec

    @property
    def name(self) -> str:
        return self.plugin.name

    @property
    def site(self) -> Path:
        return self.dir / 'lib' / 'python3.6' / 'site-packages'

    @property
    def plugin_path(self) -> Path:
        return self.site / self.name / 'nvim_plugin.py'

    @property
    def python_executable(self) -> Either[str, Path]:
        return Try(lambda: self.ns.env_exe) / Path

__all__ = ('Venv',)
