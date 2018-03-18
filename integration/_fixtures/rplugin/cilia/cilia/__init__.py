from amino import List, __
from amino.boolean import true

from ribosome.config.config import Config
from ribosome.request.handler.handler import RequestHandler
from ribosome.request.handler.prefix import Full
from ribosome.trans.api import trans
from ribosome.nvim import NvimIO
from ribosome import ribo_log

name = 'cilia'


@trans.free.unit(trans.nio)
def stage_1() -> NvimIO[None]:
    return NvimIO.delay(__.vars.set('cil', 2))


@trans.free.unit()
def test() -> None:
    ribo_log.info(f'{name} working')


@trans.free.unit(trans.nio)
def stage_2() -> NvimIO[None]:
    return NvimIO.delay(__.vars.set('flag', 2))


@trans.free.unit()
def stage_4() -> None:
    ribo_log.info(f'{name} initialized')


config = Config.cons(
    name,
    prefix='cil',
    request_handlers=List(
        RequestHandler.trans_cmd(stage_1)(prefix=Full(), sync=true),
        RequestHandler.trans_cmd(stage_2)(prefix=Full(), sync=true),
        RequestHandler.trans_cmd(stage_4)(prefix=Full(), sync=true),
        RequestHandler.trans_cmd(test)(),
    ),
)

__all__ = ('config',)
