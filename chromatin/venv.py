from types import SimpleNamespace
from typing import Any

from amino import Path, List, Try, Either
from amino.dat import Dat

from chromatin.plugin import RpluginSpec


class Venv(Dat['Venv']):

    def __init__(
            self,
            name: str,
            dir: Path,
            python_executable: Either[str, Path],
            bin_path: Either[str, Path]
    ) -> None:
        self.name = name
        self.dir = dir
        self.python_executable = python_executable
        self.bin_path = bin_path

    @staticmethod
    def from_ns(dir: Path, plugin: RpluginSpec, context: SimpleNamespace) -> 'Venv':
        exe = Try(lambda: context.env_exe) / Path
        bin_path = Try(lambda: context.bin_path) / Path
        return Venv(name=plugin.name, dir=dir, python_executable=exe, bin_path=bin_path)

    def _arg_desc(self) -> List[str]:
        return List(str(self.name), str(self.dir))

    @property
    def site(self) -> Path:
        return self.dir / 'lib' / 'python3.6' / 'site-packages'

    @property
    def plugin_path(self) -> Path:
        return self.site / self.name / '__init__.py'


class PluginVenv(Dat['PluginVenv']):

    def __init__(self, venv: Venv, plugin: RpluginSpec) -> None:
        self.venv = venv
        self.plugin = plugin

    @property
    def req(self) -> str:
        return self.plugin.spec

    @property
    def name(self) -> str:
        return self.plugin.name

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.venv, self.plugin)


class ActiveVenv(Dat['ActiveVenv']):

    def __init__(self, venv: Venv, channel: int, pid: int) -> None:
        self.venv = venv
        self.channel = channel
        self.pid = pid

    @property
    def name(self) -> str:
        return self.venv.name

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.venv, self.channel, self.pid)

__all__ = ('Venv', 'ActiveVenv', 'PluginVenv')
