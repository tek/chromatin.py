import shutil

from amino import do, Path, Do, Lists, env, Maybe, Nothing, IO, List

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.io.api import N

from chromatin.settings import interpreter


@do(IO[Path])
def virtualenv_interpreter(venv: str, executable: str) -> Do:
    path_s = yield IO.from_either(env.get('PATH'))
    path = Lists.split(path_s, ':')
    clean_path = path.filter_not(lambda a: a.startswith(venv))
    candidate = yield IO.delay(shutil.which, executable, path=clean_path.mk_string(':'))
    return Path(candidate)


@do(IO[Path])
def find_interpreter(spec: str) -> Do:
    path = Path(spec)
    exists = yield IO.delay(path.exists)
    venv = env.get('VIRTUAL_ENV').get_or_strict('[no venv]')
    yield (
        IO.pure(path)
        if exists else
        virtualenv_interpreter(venv, spec)
    )


def python_interpreter(global_spec: Maybe[str], local_spec: Maybe[str]) -> IO[Path]:
    spec = local_spec.get_or(global_spec.get_or_strict, 'python3.7')
    return find_interpreter(spec)


@do(NvimIO[Path])
def global_interpreter() -> Do:
    global_spec = yield interpreter.value
    yield N.from_io(python_interpreter(global_spec.to_maybe, Nothing))


def join_pythonpath(paths: List[str]) -> str:
    return paths.mk_string(':')


@do(IO[Path])
def which(name: str) -> Do:
    exe = yield IO.delay(shutil.which, name)
    return Path(exe)


def cabal_exe() -> IO[Path]:
    return which('cabal')


def stack_exe() -> IO[Path]:
    return which('stack')


__all__ = ('global_interpreter', 'join_pythonpath', 'stack_exe', 'cabal_exe',)
