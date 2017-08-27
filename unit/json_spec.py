from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right

from amino import Path, Right

from ribosome.record import encode_json

from chromatin.venv import Venv
from chromatin.plugin import VimPlugin


class JsonSpec:
    '''
    encode a Venv $venv
    '''

    def venv(self) -> Expectation:
        p = Path('/')
        venv = Venv(dir=p, python_executable=Right(p), bin_path=Right(p), plugin=VimPlugin(spec='spec', name='name'))
        return k(encode_json(venv)).must(be_right)

__all__ = ('JsonSpec',)
