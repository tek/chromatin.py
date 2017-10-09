import os
import neovim

from amino import Path
from amino.logging import amino_root_file_logging, TEST

from ribosome import NvimPlugin as NPlug
from ribosome.request.command import command
from ribosome.request.function import function

logfile = Path(os.environ['RIBOSOME_LOG_FILE'])
amino_root_file_logging(logfile=logfile, level=TEST)
name = 'flagellum'


class NvimPlugin(NPlug, pname=name, prefix='flag'):

    @command(sync=True)
    def flag_test(self) -> None:
        self.log.info(f'{name} working')

    @command(sync=True)
    def flag_arg_test(self, num: int) -> None:
        value = self.vim.vars.p('value') | 'failure'
        self.log.info(f'{value} {num}')

    @command(sync=True)
    def flag_conf_test(self) -> None:
        value = self.vim.vars.p('value') | 'failure'
        self.log.info(value)

    @function()
    def flag_reboot_test(self) -> int:
        return 13

    @neovim.autocmd('VimEnter')
    def vim_enter(self):
        self.log.info('autocmd works')

    def stage_1(self) -> None:
        self.vim.vars.set('flag', 1)

    def stage_2(self) -> None:
        self.vim.vars.set('cil', 1)

    def stage_4(self) -> None:
        self.log.info(f'{name} initialized')

    def quit(self) -> None:
        self.vim.vars.set_p('quit', 1)

__all__ = ('NvimPlugin',)
