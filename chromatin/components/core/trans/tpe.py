from ribosome.compute.ribosome import Ribosome
from ribosome.config.basic_config import NoData

from chromatin.config.component import ChromatinComponent
from chromatin.env import Env

CrmRibosome = Ribosome[Env, ChromatinComponent, NoData]

__all__ = ('CrmRibosome',)
