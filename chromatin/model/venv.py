import abc
import shutil
import sys
import pkg_resources

from amino import Path, IO, do, Boolean, Maybe, Lists, Either
from amino.boolean import true, false
from amino.do import Do
from amino.dat import ADT, Dat
from amino.logging import module_log

from ribosome.process import Subprocess


from chromatin.model.rplugin import Rplugin
from chromatin.util.interpreter import python_interpreter

class VenvMeta(Dat['VenvMeta']):

    def __init__(
            self,
            rplugin: str,
            dir: Path,
            python_executable: Path,
            bin_path: Path,
    ) -> None:
        self.rplugin = rplugin
        self.dir = dir
        self.python_executable = python_executable
        self.bin_path = bin_path

    @property
    def name(self) -> str:
        return self.rplugin


class Venv(Dat['Venv']):

    def __init__(self, name: str, meta: VenvMeta) -> None:
        self.name = name
        self.meta = meta


class VenvStatus(ADT['VenvStatus']):

    @abc.abstractproperty
    def exists(self) -> Boolean:
        ...


class VenvPresent(VenvStatus):

    def __init__(self, plugin: Rplugin, venv: Venv) -> None:
        self.plugin = plugin
        self.venv = venv

    @property
    def exists(self) -> Boolean:
        return true


class VenvAbsent(VenvStatus):

    def __init__(self, rplugin: Rplugin) -> None:
        self.rplugin = rplugin

    @property
    def exists(self) -> Boolean:
        return false


class VenvPackageStatus(ADT['VenvPackageStatus']):

    @abc.abstractproperty
    def exists(self) -> Boolean:
        ...


class VenvPackageExistent(VenvPackageStatus):

    def __init__(self, venv: Venv, dist: pkg_resources.Distribution) -> None:
        self.venv = venv
        self.dist = dist

    @property
    def exists(self) -> Boolean:
        return true


class VenvPackageAbsent(VenvPackageStatus):

    def __init__(self, venv: Venv) -> None:
        self.venv = venv

    @property
    def exists(self) -> Boolean:
        return false

__all__ = ('VenvStatus', 'VenvPresent', 'VenvAbsent', 'VenvPackageAbsent', 'VenvPackageExistent', 'VenvPackageStatus',
           'Venv', 'venv_plugin_path',)
