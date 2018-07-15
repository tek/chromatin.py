import abc
import shutil
import venv
import sys
import pkg_resources
from types import SimpleNamespace

from amino import Path, IO, do, Boolean, Either, Try, Maybe
from amino.boolean import true, false
from amino.do import Do
from amino.dat import ADT, Dat
from amino.logging import module_log

from ribosome.process import Subprocess


from chromatin.model.rplugin import Rplugin, VenvRplugin
from chromatin.util.interpreter import rplugin_interpreter

log = module_log()
py_exe = f'python{sys.version_info.major}.{sys.version_info.minor}'


class VenvMeta(Dat['VenvMeta']):

    @staticmethod
    def from_ns(rplugin: str, dir: Path, context: SimpleNamespace) -> 'Venv':
        exe = Try(lambda: context.env_exe) / Path
        bin_path = Try(lambda: context.bin_path) / Path
        return VenvMeta(rplugin, dir, exe, bin_path)

    def __init__(
            self,
            rplugin: str,
            dir: Path,
            python_executable: Either[str, Path],
            bin_path: Either[str, Path],
    ) -> None:
        self.rplugin = rplugin
        self.dir = dir
        self.python_executable = python_executable
        self.bin_path = bin_path

    @property
    def name(self) -> str:
        return self.rplugin


class Venv(Dat['Venv']):

    def __init__(self, rplugin: VenvRplugin, meta: VenvMeta) -> None:
        self.rplugin = rplugin
        self.meta = meta

    @property
    def dir(self) -> Path:
        return self.meta.dir

    @property
    def site(self) -> Path:
        return self.dir / 'lib' / py_exe / 'site-packages'

    @property
    def plugin_path(self) -> Path:
        return self.site / self.name / '__init__.py'

    @property
    def name(self) -> str:
        return self.rplugin.name

    @property
    def req(self) -> str:
        return self.rplugin.spec


# TODO remove
class ActiveVenv(Dat['ActiveVenv']):

    def __init__(self, venv: Venv, channel: int, pid: int) -> None:
        self.venv = venv
        self.channel = channel
        self.pid = pid

    @property
    def name(self) -> str:
        return self.venv.name


class VenvStatus(ADT['VenvStatus']):

    @abc.abstractproperty
    def exists(self) -> Boolean:
        ...


class VenvExistent(VenvStatus):

    def __init__(self, plugin: Rplugin, venv: Venv) -> None:
        self.plugin = plugin
        self.venv = venv

    @property
    def exists(self) -> Boolean:
        return true


class VenvAbsent(VenvStatus):

    def __init__(self, plugin: Rplugin) -> None:
        self.plugin = plugin

    @property
    def exists(self) -> Boolean:
        return false


@do(IO[Venv])
def build(global_interpreter: Path, dir: Path, rplugin: VenvRplugin) -> Do:
    interpreter = yield rplugin_interpreter(global_interpreter, rplugin)
    retval, out, err = yield Subprocess.popen(str(interpreter), '-m', 'venv', str(dir), '--upgrade', timeout=30)
    success = retval == 0
    yield (
        IO.delay(cons_venv, dir, rplugin)
        if success else
        IO.failed(f'creating venv for {rplugin}: {err.join_lines}')
    )


@do(IO[Venv])
def cons_venv(dir: Path, rplugin: VenvRplugin) -> Do:
    builder = yield IO.delay(venv.EnvBuilder, system_site_packages=False, with_pip=True)
    context = yield IO.delay(builder.ensure_directories, str(dir))
    return Venv(rplugin, VenvMeta.from_ns(rplugin.name, dir, context))


def cons_venv_under(base_dir: Path, rplugin: VenvRplugin) -> IO[Venv]:
    return cons_venv(base_dir / rplugin.name, rplugin)


@do(IO[None])
def remove_dir(dir: Path) -> Do:
    exists = yield IO.delay(dir.exists)
    yield IO.delay(shutil.rmtree, dir) if exists else IO.pure(None)


@do(IO[Venv])
def bootstrap(global_interpreter: Maybe[Path], base_dir: Path, rplugin: VenvRplugin) -> Do:
    venv_dir = base_dir / rplugin.name
    log.debug(f'bootstrapping {rplugin} in {venv_dir}')
    yield remove_dir(venv_dir)
    yield build(global_interpreter, venv_dir, rplugin)


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

__all__ = ('VenvStatus', 'VenvExistent', 'VenvAbsent', 'VenvPackageAbsent', 'VenvPackageExistent', 'VenvPackageStatus',
           'Venv', 'ActiveVenv', 'cons_venv_under')
