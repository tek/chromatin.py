import typing
from typing import Tuple

from ribosome.nvim import NvimIO
from ribosome.logging import ribo_log
from ribosome.nvim.api import nvim_call_function

from amino import Path, do, __, List
from amino.do import Do


stderr_handler_name = 'ChromatinJobStderr'

stderr_handler_body = '''\
let err = substitute(join(a:data, '\\r'), '"', '\\"', 'g')
python3 import amino
python3 from ribosome.logging import ribosome_envvar_file_logging
python3 ribosome_envvar_file_logging()
execute 'python3 amino.amino_log.error(f"""error in chromatin rpc job on channel ' . a:id . ':\\r' . err . '""")'
'''

def host_cmdline(python_exe: Path, bin_path: Path, plug: Path, debug: bool) -> typing.List[str]:
    debug_option = [] if debug else ['-E']
    args = [str(bin_path / f'ribosome_start_plugin'), str(plug)]
    return [str(python_exe)] + debug_option + args


@do(NvimIO[None])
def define_stderr_handler() -> Do:
    exists = yield NvimIO.delay(__.function_exists(stderr_handler_name))
    if not exists:
        yield NvimIO.delay(__.define_function(stderr_handler_name, List('id', 'data', 'event'), stderr_handler_body))


@do(NvimIO[Tuple[int, int]])
def start_host(python_exe: Path, bin_path: Path, plugin_path: Path, debug: bool=False) -> Do:
    yield define_stderr_handler()
    cmdline = host_cmdline(python_exe, bin_path, plugin_path, debug)
    ribo_log.debug(f'starting host: {cmdline}; debug: {debug}')
    channel = yield NvimIO.call('jobstart', cmdline, dict(rpc=True, on_stderr=stderr_handler_name))
    pid = yield NvimIO.call('jobpid', channel)
    ribo_log.debug(f'host running, channel {channel}, pid {pid}')
    yield NvimIO.pure((channel, pid))


@do(NvimIO[None])
def stop_host(channel: int) -> Do:
    yield nvim_call_function('jobstop', channel)

__all__ = ('start_host', 'stop_host')
