import sys
import inspect

import neovim

from amino.logging import TEST
from amino import Path

from ribosome.logging import nvim_logging, ribo_log
from ribosome.nvim import NvimFacade
from ribosome.rpc import rpc_handlers, define_handlers

from chromatin.nvim_plugin import ChromatinNvimPlugin
from chromatin.host import start_host


def run() -> None:
    try:
        installed = sys.argv[2] == '1'
        nvim_native = neovim.attach('stdio')
        nvim = NvimFacade(nvim_native, 'define_handlers').proxy
        nvim_logging(nvim, TEST)
        python_exe = Path(sys.argv[1])
        plugin_path = Path(inspect.getfile(ChromatinNvimPlugin))
        channel, pid = start_host(python_exe, plugin_path, True).attempt(nvim).get_or_raise
        handlers = rpc_handlers(ChromatinNvimPlugin)
        define_handlers(channel, handlers, 'chromatin', str(plugin_path)).attempt(nvim).get_or_raise
        ribo_log.info('defined')
        if installed:
            ribo_log.info('chromatin initialized. installing plugins...')
        nvim.cmd('ChromatinStage1')
        return 0
    except Exception as e:
        ribo_log.error(e)
        return 1

__all__ = ('run',)
