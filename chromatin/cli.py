import sys
import traceback


def echo(nvim: 'neovim.api.Nvim', msg: str) -> None:
    safe = msg.replace('"', '\\"')
    nvim.command(f'echo "{safe}"')


def tmpfile_error(msg: str) -> None:
    try:
        import tempfile
        from pathlib import Path
        (fh, file) = tempfile.mkstemp(prefix='chromatin-bootstrap')
        Path(file).write_text(msg)
    except Exception as e:
        pass


def run() -> int:
    try:
        from amino.logging import amino_root_logger, amino_root_file_logging
        amino_root_file_logging()
        amino_root_logger.debug('starting chromatin, stage amino')
        import neovim
        nvim = neovim.attach('stdio')
        amino_root_logger.debug('starting chromatin, stage nvim')
        try:
            from ribosome.nvim import NvimFacade
            from ribosome.logging import nvim_logging
            nvim_facade = NvimFacade(nvim, 'define_handlers')
            nvim_logging(nvim_facade)
            amino_root_logger.debug('starting chromatin, stage ribosome')
            return stage2(nvim_facade)
        except Exception as e:
            amino_root_logger.caught_exception_error(f'importing ribosome in chromatin bootstrap', e)
            raise
    except Exception:
        msg = traceback.format_exc()
        print(msg, file=sys.stderr)
        return 3


def stage2(nvim: 'ribosome.NvimFacade') -> int:
    try:
        from amino import Path, Lists
        from ribosome.logging import ribo_log
        import chromatin
        from chromatin.host import start_host
        ex, bp, ins = Lists.wrap(sys.argv).lift_all(1, 2, 3).get_or_fail(f'invalid arg count for `crm_run`: {sys.argv}')
        python_exe = Path(ex)
        bin_path = Path(bp)
        installed = ins == '1'
        ribo_log.debug(f'starting chromatin, stage 2: {sys.argv}')
        plugin_path = chromatin.__file__
        channel, pid = start_host(python_exe, bin_path, plugin_path).attempt(nvim).get_or_raise()
        ribo_log.debug(f'starting chromatin, host started: {channel}/{pid}')
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
