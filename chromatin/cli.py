import sys
import inspect
import traceback


def echo(nvim: 'neovim.api.Nvim', msg: str) -> None:
    safe = msg.replace('"', '\\"')
    nvim.command(f'echo "{safe}"')


def run() -> int:
    try:
        import neovim
        nvim = neovim.attach('stdio')
        try:
            from amino.logging import amino_root_logger, amino_root_file_logging, TEST
            amino_root_file_logging()
            amino_root_logger.debug('starting chromatin, stage amino')
            try:
                from ribosome.nvim import NvimFacade
                from ribosome.logging import nvim_logging
                nvim_facade = NvimFacade(nvim, 'define_handlers').proxy
                nvim_logging(nvim_facade, TEST)
                amino_root_logger.debug('starting chromatin, stage ribosome')
                return stage2(nvim_facade)
            except Exception as e:
                amino_root_logger.caught_exception_error(f'importing ribosome in chromatin bootstrap', e)
                raise
        except Exception as e:
            msg = traceback.format_exc()
            echo(nvim, msg)
            raise
    except Exception:
        msg = traceback.format_exc()
        try:
            import amino
        except Exception as e:
            pass
        else:
            if amino.development:
                print(msg, file=sys.stderr)
        return 1


def stage2(nvim: 'ribosome.NvimFacade') -> int:
    try:
        from amino import Path, Lists
        from ribosome.logging import ribo_log
        from ribosome.rpc import rpc_handlers, define_handlers
        from chromatin.nvim_plugin import ChromatinNvimPlugin
        from chromatin.host import start_host
        ex, bp, ins = Lists.wrap(sys.argv).lift_all(1, 2, 3).get_or_fail(f'invalid arg count for `crm_run`: {sys.argv}')
        python_exe = Path(ex)
        bin_path = Path(bp)
        installed = ins == '1'
        ribo_log.debug(f'starting chromatin, stage 2: {sys.argv}')
        plugin_path = Path(inspect.getfile(ChromatinNvimPlugin))
        channel, pid = start_host(python_exe, bin_path, plugin_path).attempt(nvim).get_or_raise
        ribo_log.debug(f'starting chromatin, host started: {channel}/{pid}')
        handlers = rpc_handlers(ChromatinNvimPlugin)
        define_handlers(channel, handlers, 'chromatin', str(plugin_path)).attempt(nvim).get_or_raise
        ribo_log.debug('starting chromatin, handlers defined')
        if installed:
            ribo_log.info('chromatin initialized. installing plugins...')
        def error(a: str) -> None:
            raise Exception(f'failed to initialize chromatin: {a}')
        nvim.cmd_once_defined('ChromatinStage1').leffect(error)
        return 0
    except Exception as e:
        ribo_log.caught_exception_error('initializing chromatin', e)
        raise


__all__ = ('run',)
