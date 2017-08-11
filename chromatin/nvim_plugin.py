from amino import List

import neovim

from ribosome import NvimStatePlugin
from ribosome.request import msg_command
from ribosome.nvim import NvimFacade

from chromatin.main import Chromatin
from chromatin.plugins.core.messages import AddPlugin, ShowPlugins, StageI


class ChromatinNvimPlugin(NvimStatePlugin, name='chromatin', prefix='crm'):

    def __init__(self, vim: neovim.api.Nvim) -> None:
        super().__init__(NvimFacade(vim, 'chromatin'))
        self.chromatin: Chromatin = None

    @property
    def _default_plugins(self) -> List[str]:
        return List()

    def start_plugin(self) -> None:
        self.log.test('--')
        plugins = self.vim.vars.pl('plugins') | self._default_plugins
        self.chromatin = Chromatin(self.vim.proxy, plugins)
        self.chromatin.start()
        self.chromatin.wait_for_running()
        self.chromatin.send_sync(StageI())

    @property
    def state(self) -> Chromatin:
        if self.chromatin is None:
            self.start_plugin()
        return self.chromatin

    @msg_command(AddPlugin)
    def cram(self) -> None:
        pass

    @msg_command(ShowPlugins)
    def crm_show_plugins(self) -> None:
        pass

__all__ = ('ChromatinNvimPlugin',)
