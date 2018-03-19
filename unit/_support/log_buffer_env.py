from ribosome.trans.action import LogMessage
from ribosome.request.rpc import DefinedHandler
from ribosome.config.config import Config
from ribosome.config.settings import Settings

from amino import List, Nil, Nothing, Map, Maybe

from chromatin import Env
from chromatin.model.rplugin import Rplugin, ActiveRpluginMeta
from chromatin.model.venv import VenvMeta


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
            log_buffer: List[LogMessage]=Nil,
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
