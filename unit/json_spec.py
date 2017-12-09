from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right

from amino import Path, Right
from amino.json import dump_json

from chromatin.model.rplugin import cons_rplugin
from chromatin.model.venv import Venv


class JsonSpec:
    '''encode a Venv $venv
    '''

    def venv(self) -> Expectation:
        p = Path('/')
        plugin = cons_rplugin('spec', 'name')
        venv = Venv(plugin, p, Right(p), Right(p))
        return k(dump_json(venv)).must(be_right)

__all__ = ('JsonSpec',)
