from typing import Any

import sys
import traceback
import logging

def echo(nvim: Any, msg: str) -> None:
    safe = msg.replace('"', '\\"')
    nvim.command(f'echo "{safe}"')


def tmpfile_error(msg: str) -> None:
    try:
        import tempfile
        from pathlib import Path
        (fh, file) = tempfile.mkstemp(prefix='chromatin-bootstrap')
        Path(file).write_text(str(msg))
    except Exception as e:
        pass


def run() -> int:
    try:
        from amino.logging import amino_root_logger, amino_root_file_logging
        amino_root_file_logging()
        amino_root_logger.debug('starting chromatin, stage amino')
        try:
            from ribosome.rpc.start import start_external
            from ribosome.rpc.uv.uv import cons_uv_stdio
            from ribosome.logging import nvim_logging
            uv, rpc_comm = cons_uv_stdio()
            nvim_api = start_external('define_handlers', rpc_comm).attempt.get_or_raise()
            nvim_logging(nvim_api)
            amino_root_logger.debug('starting chromatin, stage ribosome')
            return stage2(nvim_api)
        except Exception as e:
            amino_root_logger.caught_exception_error(f'importing ribosome in chromatin bootstrap', e)
            raise
    except Exception:
        try:
            msg = traceback.format_exc()
            print(msg, file=sys.stderr)
            tmpfile_error(msg)
        except Exception:
            pass
        return 3


def stage2(nvim: Any) -> int:
    try:
        from amino import Path, Lists, do, Do
        from ribosome.logging import ribo_log
        from ribosome.nvim.io.compute import NvimIO
        from ribosome.nvim.io.data import NSuccess
        from ribosome.nvim.api.exists import wait_for_command
        import chromatin
        from chromatin.host import start_host
        ex, bp, ins = Lists.wrap(sys.argv).lift_all(1, 2, 3).get_or_fail(f'invalid arg count for `crm_run`: {sys.argv}')
        python_exe = Path(ex)
        bin_path = Path(bp)
        installed = ins == '1'
        ribo_log.debug(f'starting chromatin, stage 2: {sys.argv}')
        plugin_path = chromatin.__file__
        def error(a: str) -> None:
            raise Exception(f'failed to initialize chromatin: {a}')
        @do(NvimIO[int])
        def run() -> Do:
            channel, pid = yield start_host(python_exe, bin_path, plugin_path)
            ribo_log.debug(f'starting chromatin, host started: {channel}/{pid}')
            yield wait_for_command('ChromatinPoll')
            if installed:
                ribo_log.info('chromatin initialized. installing plugins...')
        result = run().run_a(nvim)
        return 0 if isinstance(result, NSuccess) else error(result)
    except Exception as e:
        ribo_log.caught_exception_error('initializing chromatin', e)
        raise e


__all__ = ('run',)
