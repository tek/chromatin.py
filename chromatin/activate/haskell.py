from amino import Path, do, Do

from ribosome.nvim.io.api import N
from ribosome.process import Subprocess
from ribosome.nvim.io.compute import NvimIO

from chromatin.util.interpreter import stack_exe
from chromatin.model.rplugin import ActiveRplugin, Rplugin
from chromatin.activate.host import start_rplugin_host
from chromatin.host import start_host


@do(NvimIO[ActiveRplugin])
def activate_stack_plugin(rplugin: Rplugin, dir: Path) -> Do:
    stack = yield N.from_io(stack_exe())
    code, out, err = yield N.from_io(Subprocess.popen(stack, 'path', '--local-bin', cwd=dir, env=None))
    bin_path = yield N.m(out.head, lambda: f'error running `stack path --local-bin: {err.join_lines}`')
    exe = Path(bin_path) / rplugin.name
    yield start_rplugin_host(rplugin, lambda debug: start_host(str(exe), debug))


def cabal_rplugin_executable(rplugin: Rplugin) -> Path:
    return Path.home() / '.cabal' / 'bin' / rplugin.name


@do(NvimIO[ActiveRplugin])
def activate_cabal_plugin(rplugin: Rplugin, dir: Path) -> Do:
    exe = cabal_rplugin_executable(rplugin)
    yield start_rplugin_host(rplugin, lambda debug: start_host(str(exe), debug))


__all__ = ('activate_stack_plugin', 'activate_cabal_plugin', 'cabal_rplugin_executable',)
