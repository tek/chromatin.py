from ribosome.nvim import NvimFacade

from chromatin.venv import Venv
from chromatin.logging import Logging

from amino import Either, Path, do

host_start_function_name = 'CrmStartHost'

host_start_function_code = f'''
    function! {host_start_function_name}(args, host)
        let channel_id = jobstart(a:args, {{'rpc': v:true}})
        if rpcrequest(channel_id, 'poll') ==# 'ok'
            return channel_id
        else
            throw 'could not load host ' . a:host.name
        endif
    endfunction
'''

require_function_name = 'remote#host#Require'


def start_host_cmd(name: str, python_exe: Path, plug: Path) -> str:
    cmdline = [str(python_exe), '-c', 'import neovim; neovim.start_host()', str(plug)]
    return f'''call remote#host#Register('{name}', '*', function('{host_start_function_name}', [{cmdline!r}]))'''


class PluginHost(Logging):

    def __init__(self, vim: NvimFacade) -> None:
        self.vim = vim

    @do
    def start(self, venv: Venv) -> Either[str, str]:
        if not self.vim.function_exists(host_start_function_name):
            yield self.vim.execute(host_start_function_code)
        exe = yield venv.python_executable
        yield self.vim.cmd_sync(start_host_cmd(venv.name, exe, venv.plugin_path))

    def require(self, venv: Venv) -> Either[str, str]:
        return self.vim.call(require_function_name, venv.name)


__all__ = ('PluginHost',)
