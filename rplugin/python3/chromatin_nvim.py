import sys

from amino import Path

import neovim

base = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, base)

from chromatin.nvim_plugin import ChromatinNvimPlugin  # noqa


@neovim.plugin
class Plugin(ChromatinNvimPlugin):
    pass

__all__ = ('Plugin',)
