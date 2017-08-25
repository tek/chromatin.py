import typing

from ribosome.nvim import NvimFacade

from chromatin.venv import Venv
from chromatin.logging import Logging

from amino import Either, Path, do


def host_cmdline(python_exe: Path, plug: Path) -> typing.List[str]:
    return [str(python_exe), '-c', 'import neovim; neovim.start_host()', str(plug)]


class PluginHost(Logging):

    def __init__(self, vim: NvimFacade) -> None:
        self.vim = vim

    @do
    def start(self, venv: Venv) -> Either[str, int]:
        exe = yield venv.python_executable
        cmdline = host_cmdline(exe, venv.plugin_path)
        yield self.vim.call('jobstart', cmdline, dict(rpc=True))

__all__ = ('PluginHost',)
