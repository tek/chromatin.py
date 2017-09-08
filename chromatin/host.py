import typing
from typing import Tuple

from ribosome.nvim import NvimIO

from amino import Path, do, __, List


stderr_handler_name = 'ChromatinJobStderr'

stderr_handler_body = '''
  echoerr 'error in chromatin rpc job on channel ' . a:id . ': ' . string(a:data)
'''


def host_cmdline(python_exe: Path, plug: Path, debug: bool) -> typing.List[str]:
    debug_option = '' if debug else 'E'
    return [
        str(python_exe),
        f'-{debug_option}c',
        f'from ribosome.host import start_file; start_file({str(plug)!r})'
    ]


@do
def define_stderr_handler() -> NvimIO[None]:
    exists = yield NvimIO(__.function_exists(stderr_handler_name))
    if not exists:
        yield NvimIO(__.define_function(stderr_handler_name, List('id', 'data', 'event'), stderr_handler_body))


# TODO read from plugin json config
@do
def start_host(python_exe: Path, plugin_path: Path, debug: bool=False) -> NvimIO[Tuple[int, int]]:
    yield define_stderr_handler()
    cmdline = host_cmdline(python_exe, plugin_path, debug)
    channel = yield NvimIO.call('jobstart', cmdline, dict(rpc=True, on_stderr=stderr_handler_name))
    pid = yield NvimIO.call('jobpid', channel)
    yield NvimIO.pure((channel, pid))


def stop_host(channel: int) -> NvimIO[None]:
    return NvimIO.call('jobstop', channel)

__all__ = ('start_host', 'stop_host')
