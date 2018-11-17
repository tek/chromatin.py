import typing
from typing import Tuple

from amino import Path, do, List, Nil
from amino.do import Do
from amino.logging import module_log

from ribosome.nvim.io.compute import NvimIO
from ribosome.logging import ribo_log
from ribosome.nvim.api.function import nvim_call_function, nvim_call_tpe
from ribosome.nvim.io.api import N
from ribosome.rpc.error import define_rpc_stderr_handler

log = module_log()
stderr_handler_prefix = 'Chromatin'


def python_host_cmdline(
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
        cmdline: str,
        debug: bool=False,
) -> Do:
    ribo_log.debug(f'starting host: {cmdline}; debug: {debug}')
    stderr_handler_name = yield define_rpc_stderr_handler(stderr_handler_prefix)
    channel = yield nvim_call_tpe(int, 'jobstart', cmdline, dict(rpc=True, on_stderr=stderr_handler_name))
    pid = yield nvim_call_tpe(int, 'jobpid', channel)
    ribo_log.debug(f'host running, channel {channel}, pid {pid}')
    yield N.pure((channel, pid))


@do(NvimIO[Tuple[int, int]])
def start_python_host(
        python_exe: Path,
        bin_path: Path,
        plugin_path: Path,
        debug: bool=False,
        pythonpath: List[str]=Nil,
) -> Do:
    cmdline = python_host_cmdline(python_exe, bin_path, plugin_path, debug, pythonpath)
    yield start_host(cmdline, debug)


@do(NvimIO[None])
def stop_host(channel: int) -> Do:
    yield nvim_call_function('jobstop', channel)


__all__ = ('start_python_host', 'stop_host', 'start_host',)
