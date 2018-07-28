from amino import List

from ribosome.rpc.api import rpc
from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.config.component import Component


@prog
def ext_test() -> NS[None, int]:
    return NS.pure(23)


ext = Component.cons(
    'ext',
    rpc=List(
        rpc.read(ext_test),
    ),
)

__all__ = ('ext',)
