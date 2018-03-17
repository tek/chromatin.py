from ribosome.config.config import Resources

from chromatin import Env, ChromatinSettings
from chromatin.config.component import ChromatinComponent

ChromatinResources = Resources[Env, ChromatinSettings, ChromatinComponent]

__all__ = ('ChromatinResources',)
