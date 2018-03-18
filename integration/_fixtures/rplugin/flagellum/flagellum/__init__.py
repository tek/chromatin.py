from amino import List, __, do, Do
from amino.boolean import true

from ribosome.config.config import Config
from ribosome.request.handler.handler import RequestHandler
from ribosome.request.handler.prefix import Full, Plain
from ribosome.trans.api import trans
from ribosome.nvim import NvimIO
from ribosome import ribo_log

name = 'flagellum'


@trans.free.unit(trans.nio)
def stage_1() -> NvimIO[None]:
    return NvimIO.delay(__.vars.set('flag', 1))


@trans.free.unit()
def test() -> None:
    ribo_log.info(f'{name} working')


@trans.free.result()
def reboot_test() -> int:
    return 13


@trans.free.unit(trans.nio)
@do(NvimIO[None])
def arg_test(num: int) -> Do:
    value = yield NvimIO.delay(lambda v: v.vars.p('value') | 'failure')
    ribo_log.info(f'{value} {num}')
    yield NvimIO.pure(None)


@trans.free.unit(trans.nio)
@do(NvimIO[None])
def conf_test() -> Do:
    value = yield NvimIO.delay(lambda v: v.vars.p('value') | 'failure')
    ribo_log.info(value)
    yield NvimIO.pure(None)


@trans.free.unit()
def vim_enter() -> None:
    ribo_log.info('autocmd works')


@trans.free.unit(trans.nio)
def stage_2() -> NvimIO[None]:
    return NvimIO.delay(__.vars.set('cil', 1))


@trans.free.unit()
def stage_4() -> None:
    ribo_log.info(f'{name} initialized')


@trans.free.unit(trans.nio)
@do(NvimIO[None])
def quit() -> Do:
    yield NvimIO.delay(__.vars.set_p('quit', 1))


config = Config.cons(
    name,
    prefix='flag',
    request_handlers=List(
        RequestHandler.trans_cmd(stage_1)(prefix=Full(), sync=true),
        RequestHandler.trans_cmd(stage_2)(prefix=Full(), sync=true),
        RequestHandler.trans_cmd(stage_4)(prefix=Full(), sync=true),
        RequestHandler.trans_cmd(quit)(prefix=Full(), sync=true),
        RequestHandler.trans_cmd(test)(),
        RequestHandler.trans_cmd(arg_test)(),
        RequestHandler.trans_cmd(conf_test)(),
        RequestHandler.trans_function(reboot_test)(sync=True),
        RequestHandler.trans_autocmd(vim_enter)(prefix=Plain()),
    ),
)

__all__ = ('config',)
