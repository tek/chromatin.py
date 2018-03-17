from amino import Dat

from ribosome.dispatch.component import Component, ComponentData

from chromatin.env import Env


class ChromatinComponent(Dat['ChromatinComponent']):

    @staticmethod
    def cons() -> 'ChromatinComponent':
        return ChromatinComponent()

    def __init__(
            self,
    ) -> None:
        pass


Comp = Component[Env, ComponentData, ChromatinComponent]

__all__ = ('ChromatinComponent',)
