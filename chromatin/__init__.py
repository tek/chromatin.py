from amino import List

from ribosome.request.handler.handler import RequestHandler
from ribosome.request.handler.prefix import Plain, Full
from ribosome.config.config import Config

from chromatin.env import Env
from chromatin.settings import ChromatinSettings
from chromatin.components.core.trans.install import update_plugins, activate, deactivate, reboot
from chromatin.components.core.trans.setup import stage_1, setup_plugins, show_plugins, add_plugin

config: Config = Config.cons(
    name='chromatin',
    prefix='crm',
    state_ctor=Env.cons,
    settings=ChromatinSettings(),
    request_handlers=List(
        RequestHandler.trans_cmd(stage_1)(prefix=Full()),
        RequestHandler.trans_cmd(add_plugin)(name='cram', prefix=Plain()),
        RequestHandler.trans_cmd(setup_plugins)(),
        RequestHandler.trans_cmd(show_plugins)(),
        RequestHandler.trans_cmd(activate)(),
        RequestHandler.trans_cmd(deactivate)(),
        RequestHandler.trans_cmd(reboot)(),
        RequestHandler.trans_cmd(update_plugins)(name='update'),
    )
)

__all__ = ('config',)
