import os
import neovim

from amino import Path
from amino.logging import amino_root_file_logging

from ribosome import NvimPlugin as NPlug
from ribosome.request import command

logfile = Path(os.environ['RIBOSOME_LOG_FILE'])
amino_root_file_logging(logfile=logfile)
name = 'flagellum'


@neovim.plugin
class NvimPlugin(NPlug, name=name, prefix='flag'):

    def start_plugin(self) -> None:
        pass

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

    @neovim.autocmd('VimEnter')
    def vim_enter(self):
        self.log.info('autocmd works')

__all__ = ('NvimPlugin',)
