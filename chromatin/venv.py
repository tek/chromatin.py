from types import SimpleNamespace
from amino import Path, List, Try

from ribosome.record import Record, field, either_field, path_field

from chromatin.plugin import VimPlugin


class Venv(Record):
    dir = path_field()
    python_executable = either_field(Path, factory=Path)
    bin_path = either_field(Path, factory=Path)
    plugin = field(VimPlugin)

    @staticmethod
    def from_ns(dir: Path, plugin: VimPlugin, context: SimpleNamespace) -> 'Venv':
        exe = Try(lambda: context.env_exe) / Path
        bin_path = Try(lambda: context.bin_path) / Path
        return Venv(dir=dir, python_executable=exe, bin_path=bin_path, plugin=plugin)

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

__all__ = ('Venv',)
