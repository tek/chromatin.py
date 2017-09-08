import os
import neovim
import time

from amino import Path
from amino.logging import amino_root_file_logging

from ribosome import NvimPlugin as NPlug
from ribosome.nvim import NvimFacade
from ribosome.request import command

logfile = Path(os.environ['RIBOSOME_LOG_FILE'])
amino_root_file_logging(logfile=logfile)
name = 'cilia'


@neovim.plugin
class NvimPlugin(NPlug, name=name, prefix='cil'):

    def __init__(self, vim: neovim.api.Nvim) -> None:
        super().__init__(NvimFacade(vim, name))

    @command(sync=True)
    def cil_test(self) -> None:
        self.log.info(f'{name} working')

    def stage_1(self) -> None:
        time.sleep(1)
        self.vim.vars.set('cil', 2)

    def stage_2(self) -> None:
        self.vim.vars.set('flag', 2)

    def stage_4(self) -> None:
        self.log.info(f'{name} initialized')

__all__ = ('NvimPlugin',)
