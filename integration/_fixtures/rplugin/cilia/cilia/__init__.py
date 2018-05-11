from amino import List
from amino.boolean import true

from ribosome.config.config import Config
from ribosome.rpc.api import rpc
from ribosome import ribo_log
from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.nvim.api.variable import variable_set
from ribosome.rpc.data.prefix_style import Full

name = 'cilia'


@prog
def stage_1() -> NS[None, None]:
    return NS.lift(variable_set('cil', 2))


@prog
def test() -> NS[None, None]:
    return NS.simple(ribo_log.info, f'{name} working')


@prog
def stage_2() -> NS[None, None]:
    return NS.lift(variable_set('flag', 2))


@prog
def stage_4() -> NS[None, None]:
    return NS.simple(ribo_log.info, f'{name} initialized')


config = Config.cons(
    name,
    prefix='cil',
    rpc=List(
        rpc.write(stage_1).conf(prefix=Full(), sync=true),
        rpc.write(stage_2).conf(prefix=Full(), sync=true),
        rpc.write(stage_4).conf(prefix=Full(), sync=true),
        rpc.write(test),
    ),
)

__all__ = ('config',)
