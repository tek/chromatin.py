from amino import List

from ribosome.config.config import Config
from ribosome.rpc.api import rpc
from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS

name = 'path_spec'


@prog
def test() -> NS[None, int]:
    import extra_path
    return NS.pure(13)


config = Config.cons(
    name,
    prefix='path_spec',
    rpc=List(
        rpc.write(test),
    ),
)

__all__ = ('config',)
