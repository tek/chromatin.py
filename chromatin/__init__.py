from amino import List, Map

from ribosome.config import Config
from ribosome.request.handler.handler import RequestHandler
from ribosome.request.handler.prefix import Plain, Full

from chromatin.components.core.messages import (AddPlugin, ShowPlugins, SetupPlugins, UpdatePlugins, Activate,
                                                Deactivate, Reboot)
from chromatin.env import Env
from chromatin.settings import CrmSettings
from chromatin.components.core.trans import stage_1
from chromatin.components.core.main import Core

config: Config = Config.cons(
    name='chromatin',
    prefix='crm',
    state_ctor=Env.cons,
    components=Map(core=Core),
    settings=CrmSettings(),
    # core_components=List('core'),
    request_handlers=List(
        RequestHandler.trans_cmd(stage_1)(prefix=Full()),
        # RequestHandler.json_msg_cmd(AddPlugin)(name='cram', prefix=Plain()),
        # RequestHandler.msg_cmd(SetupPlugins)(),
        # RequestHandler.msg_cmd(ShowPlugins)(),
        # RequestHandler.msg_cmd(Activate)(),
        # RequestHandler.msg_cmd(Deactivate)(),
        # RequestHandler.msg_cmd(Reboot)(),
        # RequestHandler.msg_cmd(UpdatePlugins)(name='update'),
    )
)

__all__ = ('config',)
