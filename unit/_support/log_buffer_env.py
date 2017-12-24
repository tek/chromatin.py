from ribosome.trans.action import LogMessage
from ribosome.config import Config, PluginSettings
from ribosome.request.rpc import DefinedHandler

from amino import List, Nil, Nothing, Map, Maybe

from chromatin import Env
from chromatin.model.rplugin import Rplugin, ActiveRpluginMeta
from chromatin.model.venv import VenvMeta


class LogBufferEnv(Env):

    @staticmethod
    def cons(config: Config[PluginSettings, 'LogBufferEnv']) -> 'LogBufferEnv':
        return LogBufferEnv(config, Nil, Nothing, Nothing, Map(), Nil, Nil, Nil, Map(), log_buffer=Nil)

    def __init__(
            self,
            config: Config,
            rplugins: List[Rplugin],
            chromatin_plugin: Maybe[Rplugin],
            chromatin_venv: Maybe[VenvMeta],
            venvs: Map[str, VenvMeta],
            ready: List[str],
            active: List[ActiveRpluginMeta],
            uninitialized: List[ActiveRpluginMeta],
            handlers: Map[str, List[DefinedHandler]],
            log_buffer: List[LogMessage]=Nil,
    ) -> None:
        self.config = config
        self.rplugins = rplugins
        self.chromatin_plugin = chromatin_plugin
        self.chromatin_venv = chromatin_venv
        self.venvs = venvs
        self.ready = ready
        self.active = active
        self.uninitialized = uninitialized
        self.handlers = handlers
        self.log_buffer = log_buffer


__all__ = ('LogBufferEnv',)
