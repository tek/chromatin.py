import typing
from typing import Tuple

from amino import Path, do, __, List, Nil
from amino.do import Do
from amino.logging import module_log

from ribosome.nvim.io.compute import NvimIO
from ribosome.logging import ribo_log
from ribosome.nvim.api.function import nvim_call_function, nvim_call_tpe, define_function
from ribosome.nvim.io.api import N
from ribosome.nvim.api.exists import function_exists

log = module_log()
stderr_handler_name = 'ChromatinRpcJobStderr'


def host_cmdline(
        python_exe: Path,
        bin_path: Path,
        plug: Path,
        debug: bool,
        pythonpath: List[str],
) -> typing.List[str]:
    debug_option = [] if debug else ['-E']
    ppath = pythonpath.mk_string(':')
    pre = [] if pythonpath.empty else ['env', f'RIBOSOME_PYTHONPATH={ppath}']
    args = [str(bin_path / f'ribosome_start_plugin'), str(plug)]
    return pre + [str(python_exe)] + debug_option + args


@do(NvimIO[Tuple[int, int]])
def start_host(
        python_exe: Path,
        bin_path: Path,
        plugin_path: Path,
        debug: bool=False,
        pythonpath: List[str]=Nil,
) -> Do:
    cmdline = host_cmdline(python_exe, bin_path, plugin_path, debug, pythonpath)
    ribo_log.debug(f'starting host: {cmdline}; debug: {debug}')
    channel = yield nvim_call_tpe(int, 'jobstart', cmdline, dict(rpc=True, on_stderr=stderr_handler_name))
    pid = yield nvim_call_tpe(int, 'jobpid', channel)
    ribo_log.debug(f'host running, channel {channel}, pid {pid}')
    yield N.pure((channel, pid))


@do(NvimIO[None])
def stop_host(channel: int) -> Do:
    yield nvim_call_function('jobstop', channel)


__all__ = ('start_host', 'stop_host')
