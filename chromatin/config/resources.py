from ribosome.config.resources import Resources

from chromatin.config.component import ChromatinComponent
from chromatin.env import Env

ChromatinResources = Resources[Env, ChromatinComponent]

__all__ = ('ChromatinResources',)
