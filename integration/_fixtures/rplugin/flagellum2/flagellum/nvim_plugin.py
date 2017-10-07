import os
import neovim

from amino import Path
from amino.logging import amino_root_file_logging, TEST

from ribosome import NvimPlugin as NPlug, command, function

logfile = Path(os.environ['RIBOSOME_LOG_FILE'])
amino_root_file_logging(logfile=logfile, level=TEST)
name = 'flagellum'


@neovim.plugin
class NvimPlugin(NPlug, pname=name, prefix='flag'):

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

    @function()
    def flag_reboot_test(self) -> int:
        return 17

    @neovim.autocmd('VimEnter')
    def vim_enter(self):
        self.log.info('autocmd works')

__all__ = ('NvimPlugin',)
