from amino import do, __
from amino.do import Do

from ribosome.nvim.io import NS
from ribosome.trans.api import trans
from ribosome.trans.message_base import Message

from chromatin.components.core.logic import add_crm_venv, read_conf, add_plugins
from chromatin import Env


@trans.free.unit(trans.st, trans.gather_ios, trans.st, trans.m)
@do(NS[Env, Message])
def stage_1() -> Do:
    yield add_crm_venv()
    yield NS.delay(__.vars.set_p('started', True))
    yield NS.delay(__.vars.ensure_p('rplugins', []))
    plugins = yield read_conf()
    yield add_plugins(plugins)


__all__ = ('stage_1',)
