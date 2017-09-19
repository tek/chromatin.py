import typing
from typing import Tuple

from ribosome.nvim import NvimIO
from ribosome.logging import ribo_log

from amino import Path, do, __, List


stderr_handler_name = 'ChromatinJobStderr'

stderr_handler_body = '''
  echoerr 'error in chromatin rpc job on channel ' . a:id . ': ' . string(a:data)
'''


def host_cmdline(python_exe: Path, bin_path: Path, plug: Path, debug: bool) -> typing.List[str]:
    debug_option = [] if debug else ['-E']
    args = [str(bin_path / f'ribosome_start_plugin'), str(plug)]
    return [str(python_exe)] + debug_option + args


@do
def define_stderr_handler() -> NvimIO[None]:
    exists = yield NvimIO(__.function_exists(stderr_handler_name))
    if not exists:
        yield NvimIO(__.define_function(stderr_handler_name, List('id', 'data', 'event'), stderr_handler_body))


@do
def start_host(python_exe: Path, bin_path: Path, plugin_path: Path, debug: bool=False) -> NvimIO[Tuple[int, int]]:
    yield define_stderr_handler()
    cmdline = host_cmdline(python_exe, bin_path, plugin_path, debug)
    ribo_log.debug(f'starting host: {cmdline}')
    channel = yield NvimIO.call('jobstart', cmdline, dict(rpc=True, on_stderr=stderr_handler_name))
    pid = yield NvimIO.call('jobpid', channel)
    ribo_log.debug(f'host running, channel {channel}, pid {pid}')
    yield NvimIO.pure((channel, pid))


def stop_host(channel: int) -> NvimIO[None]:
    return NvimIO.call('jobstop', channel)

__all__ = ('start_host', 'stop_host')
