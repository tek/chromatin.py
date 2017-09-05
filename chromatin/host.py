import typing
from typing import Tuple

from ribosome.nvim import NvimIO

from amino import Path, do


def host_cmdline(python_exe: Path, plug: Path, debug: bool) -> typing.List[str]:
    debug_option = '' if debug else 'E'
    return [str(python_exe), f'-{debug_option}c', 'import neovim; neovim.start_host()', str(plug)]


@do
def start_host(python_exe: Path, plugin_path: Path, debug: bool=False) -> NvimIO[Tuple[int, int]]:
    cmdline = host_cmdline(python_exe, plugin_path, debug)
    channel = yield NvimIO.call('jobstart', cmdline, dict(rpc=True, on_stderr='ChromatinJobStderr'))
    pid = yield NvimIO.call('jobpid', channel)
    yield NvimIO.pure((channel, pid))


def stop_host(channel: int) -> NvimIO[None]:
    return NvimIO.call('jobstop', channel)

__all__ = ('start_host', 'stop_host')
