from ribosome.config.resources import Resources

from chromatin.config.component import ChromatinComponent
from chromatin.env import Env
from chromatin.settings import ChromatinSettings

ChromatinResources = Resources[Env, ChromatinSettings, ChromatinComponent]

__all__ = ('ChromatinResources',)
