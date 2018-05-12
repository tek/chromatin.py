from amino import Dat

from ribosome.config.component import Component, ComponentData

from chromatin.env import Env


class ChromatinComponent(Dat['ChromatinComponent']):

    @staticmethod
    def cons() -> 'ChromatinComponent':
        return ChromatinComponent()

    def __init__(
            self,
    ) -> None:
        pass


Comp = Component[ComponentData, ChromatinComponent]

__all__ = ('ChromatinComponent',)
