from ribosome.request.rpc import DefinedHandler
from ribosome.compute.output import Echo

from amino import List, Nil, Nothing, Map, Maybe

from chromatin.model.rplugin import Rplugin, ActiveRpluginMeta
from chromatin.model.venv import VenvMeta
from chromatin.env import Env


class LogBufferEnv(Env):

    @staticmethod
    def cons() -> 'LogBufferEnv':
        return LogBufferEnv(Nil, Nothing, Nothing, Map(), Nil, Nil, Nil, Map(), log_buffer=Nil)

    def __init__(
            self,
            rplugins: List[Rplugin],
            chromatin_rplugin: Maybe[Rplugin],
            chromatin_venv: Maybe[VenvMeta],
            venvs: Map[str, VenvMeta],
            ready: List[str],
            active: List[ActiveRpluginMeta],
            uninitialized: List[ActiveRpluginMeta],
            handlers: Map[str, List[DefinedHandler]],
            log_buffer: List[Echo]=Nil,
    ) -> None:
        self.rplugins = rplugins
        self.chromatin_rplugin = chromatin_rplugin
        self.chromatin_venv = chromatin_venv
        self.venvs = venvs
        self.ready = ready
        self.active = active
        self.uninitialized = uninitialized
        self.handlers = handlers
        self.log_buffer = log_buffer


__all__ = ('LogBufferEnv',)
