import neovim

from ribosome.logging import Logging
from ribosome import NvimStatePlugin
from ribosome.nvim import NvimFacade
from ribosome.request import command


class NvimPlugin(Logging, NvimStatePlugin, name='flagellum', prefix='flag'):

    def __init__(self, vim: neovim.api.Nvim) -> None:
        super().__init__(NvimFacade(vim, 'flagellum'))

    @property
    def state(self) -> None:
        return None

    def start_plugin(self) -> None:
        pass

    @command(sync=True)
    def flag_test(self) -> None:
        self.log.info('plugin working')

__all__ = ('NvimPlugin',)
