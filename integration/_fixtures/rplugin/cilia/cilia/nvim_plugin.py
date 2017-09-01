import os
import neovim
import inspect
import time

from amino import Path, List, Map, __, Maybe
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

    def start_plugin(self) -> None:
        pass

    @command(sync=True)
    def cil_test(self) -> None:
        self.log.info(f'{name} working')

    def setup_handlers(self):
        rp_path = __file__
        rp_handlers = self.handlers
        self.vim.call(
            'remote#host#RegisterPlugin',
            name,
            str(rp_path),
            rp_handlers,
        )

    @property
    def handlers(self):
        return List.wrap(inspect.getmembers(NvimPlugin)).flat_map2(self._auto_handler)

    def _auto_handler(self, method_name, fun):
        fix = lambda v: int(v) if isinstance(v, bool) else v
        m = Maybe(getattr(fun, '_nvim_rpc_spec', None))
        return m / Map / __.valmap(fix)

    def stage_1(self) -> None:
        time.sleep(1)
        self.vim.vars.set('cil', 2)

    def stage_2(self) -> None:
        self.vim.vars.set('flag', 2)

    def stage_4(self) -> None:
        self.log.info(f'{name} initialized')

__all__ = ('NvimPlugin',)
