from amino import List, Map

from ribosome.config import Config
from ribosome.request.handler.handler import RequestHandler
from ribosome.request.handler.prefix import Plain, Full

from chromatin.env import Env
from chromatin.settings import CrmSettings
from chromatin.components.core.main import Core
from chromatin.components.core.trans.install import update_plugins
from chromatin.components.core.trans.setup import stage_1

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
        RequestHandler.trans_cmd(update_plugins)(name='update'),
    )
)

__all__ = ('config',)
