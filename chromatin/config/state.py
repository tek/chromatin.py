from ribosome.data.plugin_state import PluginState

from chromatin.env import Env
from chromatin.config.component import ChromatinComponent

ChromatinState = PluginState[Env, ChromatinComponent]

__all__ = ('ChromatinState',)
