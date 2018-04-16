from ribosome.data.plugin_state import PluginState

from chromatin.settings import ChromatinSettings
from chromatin.env import Env
from chromatin.config.component import ChromatinComponent

ChromatinState = PluginState[ChromatinSettings, Env, ChromatinComponent]

__all__ = ('ChromatinState',)
