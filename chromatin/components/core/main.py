from lenses import Lens, lens

from ribosome.dispatch.component import Component

from amino.state import State
from amino import Nothing

from chromatin.env import Env


class Core(Component):
    pass

    def state_lens(self, tpe: str, name: str) -> State[Env, Lens]:
        return (
            State.inspect(lambda s: s.plugins.index_where(lambda a: a.name == name) / (lambda i: lens(s).plugins[i]))
            if tpe == 'vim_plugin' else
            State.pure(Nothing)
        )


__all__ = ('Core',)
