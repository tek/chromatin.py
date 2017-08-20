from typing import Any

from ribosome.data import Data
from ribosome.record import dfield, list_field, map_field, field
from ribosome.nvim import NvimFacade, AsyncVimProxy

from amino import List, _, Either

from chromatin.logging import Logging
from chromatin.plugin import VimPlugin
from chromatin.venv import Venv
from chromatin.venvs import VenvFacade


class Env(Data, Logging):
    vim = field((NvimFacade, AsyncVimProxy))
    initialized = dfield(False)
    plugins = list_field(VimPlugin)
    installed = list_field(Venv)
    venvs = map_field()

    def add_plugin(self, name: str, spec: str) -> 'Env':
        return self.append1.plugins(VimPlugin(name=name, spec=spec))

    @property
    def show_plugins(self) -> List[str]:
        def format(plug: VimPlugin) -> str:
            return plug.spec
        return self.plugins.map(format).cons('Configured plugins:')

    def add_venv(self, venv: Venv) -> 'Env':
        return self.modder.venvs(_ + (venv.plugin, venv))

    def add_installed(self, venv: Venv) -> 'Env':
        return self.append1.installed(venv)

    def missing(self, venvs: VenvFacade) -> List[Venv]:
        return self.venvs.v.filter_not(venvs.package_installed)

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.plugins, self.venvs)

    @property
    def venv_facade(self) -> Either[str, VenvFacade]:
        return self.vim.vars.ppath('venv_dir') / VenvFacade

__all__ = ('Env',)
