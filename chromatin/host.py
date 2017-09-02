import typing
from typing import Tuple

from ribosome.nvim import NvimIO

from amino import Path, do


def host_cmdline(python_exe: Path, plug: Path) -> typing.List[str]:
    return [str(python_exe), '-c', 'import neovim; neovim.start_host()', str(plug)]


@do
def start_host(python_exe: Path, plugin_path: Path) -> NvimIO[Tuple[int, int]]:
    cmdline = host_cmdline(python_exe, plugin_path)
    channel = yield NvimIO.call('jobstart', cmdline, dict(rpc=True))
    pid = yield NvimIO.call('jobpid', channel)
    yield NvimIO.pure((channel, pid))


def stop_host(channel: int) -> NvimIO[None]:
    return NvimIO.call('jobstop', channel)

__all__ = ('start_host', 'stop_host')
