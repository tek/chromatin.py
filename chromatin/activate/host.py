from typing import Callable, Tuple

from amino import do, Do, Path, List

from ribosome.nvim.io.compute import NvimIO

from chromatin.model.rplugin import ActiveRplugin, Rplugin, ActiveRpluginMeta
from chromatin.settings import debug_pythonpath
from chromatin.host import start_python_host


@do(NvimIO[ActiveRplugin])
def start_rplugin_host(rplugin: Rplugin, start: Callable[[bool], NvimIO[Tuple[int, int]]]) -> Do:
    debug_global = yield debug_pythonpath.value
    debug = debug_global.get_or_strict(rplugin.debug)
    channel, pid = yield start(debug)
    return ActiveRplugin(rplugin, ActiveRpluginMeta(rplugin.name, channel, pid))


@do(NvimIO[ActiveRplugin])
def start_python_rplugin_host(
        rplugin: Rplugin,
        python_exe: Path,
        bin_path: Path,
        plugin_path: Path,
        pythonpath: List[str],
) -> Do:
    yield start_rplugin_host(
        rplugin,
        lambda debug: start_python_host(python_exe, bin_path, plugin_path, debug, pythonpath + rplugin.pythonpath),
    )

__all__ = ('start_rplugin_host', 'start_python_rplugin_host',)
