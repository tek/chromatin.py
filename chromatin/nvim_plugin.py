import time
import threading

import neovim

from amino import List

from ribosome import NvimStatePlugin
from ribosome.request import msg_command, json_msg_command
from ribosome.nvim import NvimFacade

from chromatin.main import Chromatin
from chromatin.plugins.core.messages import (AddPlugin, ShowPlugins, Start, SetupPlugins, UpdatePlugins, Activate,
                                             Deactivate, Reboot)


class ChromatinNvimPlugin(NvimStatePlugin, name='chromatin', prefix='crm'):

    def __init__(self, vim: neovim.api.Nvim) -> None:
        super().__init__(NvimFacade(vim, 'chromatin'))
        self.initialized = False
        self.chromatin: Chromatin = None

    @property
    def _default_plugins(self) -> List[str]:
        return List()

    def stage_1(self) -> None:
        plugins = self.vim.vars.pl('plugins') | self._default_plugins
        self.chromatin = Chromatin(self.vim.proxy, plugins)
        self.chromatin.start()
        self.chromatin.wait_for_running()
        self.chromatin.send_sync(Start())

    def state(self) -> Chromatin:
        if self.chromatin is None and not self.initialized:
            self.initialized = True
            self.stage_1()
        self.wait_for_startup()
        return self.chromatin

    def wait_for_startup(self) -> bool:
        start = time.time()
        while self.chromatin is None and time.time() - start < 5:
            time.sleep(.1)
        if self.chromatin is not None:
            self.chromatin.wait_for_running()
            time.sleep(.1)
        return self.chromatin is not None

    @json_msg_command(AddPlugin)
    def cram(self) -> None:
        pass

    @msg_command(ShowPlugins)
    def crm_show_plugins(self) -> None:
        pass

    @msg_command(SetupPlugins)
    def crm_setup_plugins(self) -> None:
        pass

    @msg_command(Activate)
    def crm_activate(self) -> None:
        pass

    @msg_command(Deactivate)
    def crm_deactivate(self) -> None:
        pass

    @msg_command(Reboot)
    def crm_reboot(self) -> None:
        pass

    @msg_command(UpdatePlugins)
    def crm_update(self) -> None:
        pass

    @neovim.autocmd('VimEnter')
    def vim_enter(self):
        threading.Thread(target=self.state).start()

__all__ = ('ChromatinNvimPlugin',)
