from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right

from amino import Path, Right

from ribosome.record import encode_json

from chromatin.venv import Venv
from chromatin.model.plugin import RpluginSpec


class JsonSpec:
    '''encode a Venv $venv
    '''

    def venv(self) -> Expectation:
        p = Path('/')
        plugin = RpluginSpec(spec='spec', name='name')
        venv = Venv(name=plugin.name, dir=p, python_executable=Right(p), bin_path=Right(p))
        return k(encode_json(venv)).must(be_right)

__all__ = ('JsonSpec',)
