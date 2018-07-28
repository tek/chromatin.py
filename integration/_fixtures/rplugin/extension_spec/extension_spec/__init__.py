from amino import List

from ribosome.config.config import Config
from ribosome.rpc.api import rpc
from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS

name = 'extension_spec'


@prog
def test() -> NS[None, int]:
    return NS.pure(13)


config = Config.cons(
    name,
    prefix='x',
    rpc=List(
        rpc.read(test),
    ),
)

__all__ = ('config',)
