import shutil

from amino import Either, Boolean, Path, Maybe, L, _, do, IO, Do, Just, Nothing
from amino.boolean import false
from amino.case import Case
from amino.logging import module_log

from ribosome.process import Subprocess

from chromatin.model.venv import (VenvStatus, VenvPresent, VenvAbsent, VenvPackageStatus, VenvPackageExistent,
                                  VenvPackageAbsent, Venv)
from chromatin.model.rplugin import (DirRplugin, SiteRplugin, DistRplugin, Rplugin, VenvRplugin, DistVenvRplugin,
                                     DirVenvRplugin)
from chromatin.venv import cons_venv
from chromatin.util.interpreter import python_interpreter

log = module_log()


def venv_present(dir: Path, plugin: Rplugin) -> VenvStatus:
    venv = cons_venv(dir, plugin.name)
    return VenvPresent(plugin, venv)


@do(IO[VenvStatus])
def check_venv(base_dir: Path, plugin: Rplugin) -> Do:
    dir = base_dir / plugin.name
    pip = dir / 'bin' / 'pip'
    exists = yield IO.delay(pip.exists)
    return (
        venv_present(dir, plugin)
        if exists else
        VenvAbsent(plugin)
    )


@do(IO[Boolean])
def venv_exists(base_dir: Path, plugin: Rplugin) -> Do:
    status = yield check_venv(base_dir, plugin)
    return isinstance(status, VenvPresent)


def venv_rplugin_status(base_dir: Path, venv_rplugin: VenvRplugin) -> IO[VenvStatus]:
    return check_venv(base_dir, venv_rplugin.rplugin)


class cons_venv_rplugin(Case[Rplugin, Maybe[VenvRplugin]], alg=Rplugin):

    def dist(self, a: DistRplugin) -> Maybe[VenvRplugin]:
        return Just(VenvRplugin(DistVenvRplugin(a.spec), a))

    def dir(self, a: DirRplugin) -> Maybe[VenvRplugin]:
        return Just(VenvRplugin(DirVenvRplugin(Path(a.spec)), a))

    def site(self, a: SiteRplugin) -> Maybe[VenvRplugin]:
        return Nothing


@do(IO[None])
def remove_dir(dir: Path) -> Do:
    exists = yield IO.delay(dir.exists)
    yield IO.delay(shutil.rmtree, dir) if exists else IO.pure(None)


def create_dir(dir: Path) -> IO[None]:
    return IO.delay(dir.mkdir, parents=True, exist_ok=True)


@do(IO[Venv])
def build_venv(global_interpreter: Maybe[str], dir: Path, rplugin_interpreter: Maybe[str], name: str) -> Do:
    interpreter = yield python_interpreter(global_interpreter, rplugin_interpreter)
    retval, out, err = yield Subprocess.popen(str(interpreter), '-m', 'venv', str(dir), '--upgrade', timeout=30)
    success = retval == 0
    yield (
        IO.pure(cons_venv(dir, name))
        if success else
        IO.failed(f'creating venv for `{name}`: {err.join_lines}')
    )


@do(IO[str])
def bootstrap_venv(global_interpreter: Maybe[Path], base_dir: Path, rplugin: Rplugin) -> Do:
    venv_dir = base_dir / rplugin.name
    log.debug(f'bootstrapping {rplugin} in {venv_dir}')
    yield remove_dir(venv_dir)
    yield create_dir(venv_dir)
    yield build_venv(global_interpreter, venv_dir, rplugin.interpreter, rplugin.name)
    return rplugin.name


__all__ = ('check_venv', 'venv_exists', 'venv_package_installed', 'venv_status_check', 'rplugin_ready',
           'venv_rplugin_status', 'cons_venv_rplugin',)
