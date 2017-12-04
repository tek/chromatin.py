import abc
import shutil
import venv
import sys
import pkg_resources

from amino import Path, IO, do, Maybe, _, L, List, Boolean, Either, Right, env
from amino.util.string import ToStr
from amino.boolean import true, false
from amino.do import Do

from ribosome.process import Subprocess

from chromatin.plugin import RpluginSpec
from chromatin.logging import Logging
from chromatin.venv import Venv, PluginVenv


class VenvState(ToStr):

    def __init__(self, plugin: RpluginSpec) -> None:
        self.plugin = plugin

    def _arg_desc(self) -> List[str]:
        return List(str(self.plugin))


class VenvExistent(VenvState):

    def __init__(self, plugin, venv) -> None:
        super().__init__(plugin)
        self.venv = venv


class VenvAbsent(VenvState):
    pass


@do(IO[None])
def remove_dir(dir: Path) -> Do:
    exists = yield IO.delay(dir.exists)
    yield IO.delay(shutil.rmtree, dir) if exists else IO.pure(None)


@do(IO[Venv])
def build(dir: Path, plugin: RpluginSpec) -> Do:
    exe = 'python3' if 'VIRTUAL_ENV' in env else sys.executable
    retval, out, err = yield Subprocess.popen(exe, '-m', 'venv', str(dir), '--upgrade', timeout=30)
    success = retval == 0
    yield (
        IO.delay(cons_venv, dir, plugin)
        if success else
        IO.failed(f'creating venv for {plugin}: {err.join_lines}')
    )


def cons_venv(dir: Path, plugin: RpluginSpec) -> Venv:
    builder = venv.EnvBuilder(system_site_packages=False, with_pip=True)
    context = builder.ensure_directories(str(dir))
    return Venv.from_ns(dir, plugin, context)


class PackageState(ToStr):

    def __init__(self, venv: Venv) -> None:
        self.venv = venv

    @abc.abstractproperty
    def exists(self) -> Boolean:
        ...


class PackageExistent(PackageState):

    def __init__(self, venv: Venv, dist: pkg_resources.Distribution) -> None:
        self.venv = venv
        self.dist = dist

    def _arg_desc(self) -> List[str]:
        return List(str(self.venv), str(self.dist))

    @property
    def exists(self) -> Boolean:
        return true


class PackageAbsent(PackageState):

    def _arg_desc(self) -> List[str]:
        return List()

    @property
    def exists(self) -> Boolean:
        return false


def package_state(venv: Venv, req: str) -> PackageState:
    ws = pkg_resources.WorkingSet([venv.site])
    req = pkg_resources.Requirement(req)
    return Maybe.check(ws.by_key.get(req.key)) / L(PackageExistent)(venv, _) | PackageAbsent(venv)


def package_state_main(venv: Venv) -> PackageState:
    return package_state(venv, venv.name)


class VenvFacade(Logging):

    def __init__(self, dir: Path) -> None:
        self.dir = dir

    def check(self, plugin: RpluginSpec) -> VenvState:
        dir = self.dir / plugin.name
        return (
            VenvExistent(plugin, self.cons(plugin))
            if dir.exists() else
            VenvAbsent(plugin)
        )

    @do(IO[Venv])
    def bootstrap(self, plugin: RpluginSpec) -> Do:
        venv_dir = self.dir / plugin.name
        self.log.debug(f'bootstrapping {plugin} in {venv_dir}')
        yield remove_dir(venv_dir)
        yield build(venv_dir, plugin)

    def cons(self, plugin: RpluginSpec) -> Venv:
        dir = self.dir / plugin.name
        return cons_venv(dir, plugin)

    def package_state(self, venv: Venv) -> PackageState:
        return package_state_main(venv)

    def package_installed(self, venv: Venv) -> Boolean:
        return self.package_state(venv).exists

    @do(Either[str, Subprocess[Venv]])
    def install(self, pvenv: PluginVenv) -> Do:
        venv = pvenv.venv
        self.log.debug(f'installing {venv}')
        bin_path = yield venv.bin_path
        pip_bin = bin_path / 'pip'
        args = List('install', '-U', '--no-cache', pvenv.req)
        yield Right(Subprocess(pip_bin, args, venv))

__all__ = ('VenvFacade', 'VenvState', 'VenvExistent', 'VenvAbsent')
