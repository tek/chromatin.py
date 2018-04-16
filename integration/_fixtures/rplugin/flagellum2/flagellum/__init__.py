from amino import List, do, Do

from ribosome.config.config import Config
from ribosome.request.handler.handler import RequestHandler
from ribosome.request.handler.prefix import Full, Plain
from ribosome import ribo_log
from ribosome.compute.api import prog
from ribosome.nvim.api.variable import variable_set, variable_prefixed_str
from ribosome.nvim.io.state import NS

name = 'flagellum'


@prog
def stage_1() -> NS[None, None]:
    return NS.lift(variable_set('flag', 1))


@prog
def test() -> NS[None, None]:
    return NS.simple(ribo_log.info, f'{name} working')


@prog
def reboot_test() -> NS[None, None]:
    return NS.pure(17)


@prog
@do(NS[None, None])
def arg_test(num: int) -> Do:
    value_e = yield NS.lift(variable_prefixed_str('value'))
    value = value_e | 'failure'
    ribo_log.info(f'{value} {num}')


@prog
@do(NS[None, None])
def conf_test() -> Do:
    value_e = yield NS.lift(variable_prefixed_str('value'))
    value = value_e | 'failure'
    ribo_log.info(value)


@prog
def vim_enter() -> NS[None, None]:
    return NS.simple(ribo_log.info, 'autocmd works')


@prog
def stage_2() -> NS[None, None]:
    return NS.lift(variable_set('cil', 1))


@prog
def stage_4() -> NS[None, None]:
    return NS.simple(ribo_log.info, f'{name} initialized')


@prog
def quit() -> NS[None, None]:
    return NS.lift(variable_set('quit', 1))


config = Config.cons(
    name,
    prefix='flag',
    request_handlers=List(
        RequestHandler.trans_cmd(stage_1)(prefix=Full()),
        RequestHandler.trans_cmd(stage_2)(prefix=Full()),
        RequestHandler.trans_cmd(stage_4)(prefix=Full()),
        RequestHandler.trans_cmd(quit)(prefix=Full()),
        RequestHandler.trans_cmd(test)(),
        RequestHandler.trans_cmd(arg_test)(),
        RequestHandler.trans_cmd(conf_test)(),
        RequestHandler.trans_function(reboot_test)(sync=True),
        RequestHandler.trans_autocmd(vim_enter)(prefix=Plain()),
    ),
)

__all__ = ('config',)
