import sys
import inspect


def echo(nvim: 'neovim.api.Nvim', msg: str) -> None:
    nvim.command(f'echo "{msg}"')


def run() -> int:
    try:
        import neovim
        nvim = neovim.attach('stdio')
        try:
            from amino.logging import amino_root_logger, amino_root_file_logging, TEST
            amino_root_file_logging()
            try:
                from ribosome.nvim import NvimFacade
                from ribosome.logging import nvim_logging
                nvim = NvimFacade(nvim, 'define_handlers').proxy
                nvim_logging(nvim, TEST)
                return stage2(nvim)
            except Exception as e:
                amino_root_logger(f'failed to import ribosome in chromatin bootstrap: {e}')
                raise
        except Exception as e:
            echo(nvim)
            raise
    except Exception as e:
        print(e, file=sys.stderr)
        return 1


def stage2(nvim: 'ribosome.NvimFacade') -> int:
    try:
        from amino import Path
        from ribosome.logging import ribo_log
        from ribosome.rpc import rpc_handlers, define_handlers
        from chromatin.nvim_plugin import ChromatinNvimPlugin
        from chromatin.host import start_host
        python_exe = Path(sys.argv[1])
        plugin_path = Path(inspect.getfile(ChromatinNvimPlugin))
        channel, pid = start_host(python_exe, plugin_path).attempt(nvim).get_or_raise
        handlers = rpc_handlers(ChromatinNvimPlugin)
        define_handlers(channel, handlers, 'chromatin', str(plugin_path)).attempt(nvim).get_or_raise
        installed = sys.argv[2] == '1' if len(sys.argv) > 2 else False
        if installed:
            ribo_log.info('chromatin initialized. installing plugins...')
        nvim.cmd('ChromatinStage1')
        return 0
    except Exception as e:
        ribo_log.error(e)
        raise

__all__ = ('run',)
