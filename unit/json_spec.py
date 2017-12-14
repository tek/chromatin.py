from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right

from amino import Path, Right, _
from amino.json import dump_json, decode_json

from ribosome.config import Config

from chromatin.model.rplugin import cons_rplugin
from chromatin.model.venv import Venv
from chromatin import Env


class JsonSpec:
    '''
    encode a Venv $venv
    encode Env $env
    '''

    def venv(self) -> Expectation:
        p = Path('/')
        plugin = cons_rplugin('spec', 'name')
        venv = Venv(plugin, p, Right(p), Right(p))
        return k(dump_json(venv)).must(be_right)

    def env(self) -> Expectation:
        config = Config.cons('spec')
        env = Env.cons(config)
        json = dump_json(env)
        restored = json // decode_json / _.config.name
        return k(restored).must(be_right(env.config.name))

__all__ = ('JsonSpec',)
