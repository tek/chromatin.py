import os
import neovim
import time

from amino import Path
from amino.logging import amino_root_file_logging, TEST

from ribosome import AutoPlugin
from ribosome.request.command import command
from ribosome.settings import Config

logfile = Path(os.environ['RIBOSOME_LOG_FILE'])
amino_root_file_logging(logfile=logfile, level=TEST)
name = 'cilia'

config = Config(name=name, prefix='cil')


@neovim.plugin
class NvimPlugin(AutoPlugin):

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
