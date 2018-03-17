from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right

from amino import Path, Right, _, List
from amino.json import dump_json, decode_json

from chromatin.model.rplugin import cons_rplugin
from chromatin.model.venv import Venv, VenvMeta
from chromatin import Env


class JsonSpec:
    '''
    encode a Venv $venv
    encode Env $env
    '''

    def venv(self) -> Expectation:
        p = Path('/')
        rplugin = cons_rplugin('spec', 'name')
        venv = Venv(rplugin, VenvMeta(rplugin.name, p, Right(p), Right(p)))
        return k(dump_json(venv)).must(be_right)

    def env(self) -> Expectation:
        ready = List('one')
        env = Env.cons(ready=ready)
        json = dump_json(env)
        restored = json // decode_json / _.ready
        return k(restored).must(be_right(ready))

__all__ = ('JsonSpec',)
