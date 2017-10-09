from amino import List, Map

from ribosome.settings import Config, PluginSettings, RequestHandler, Plain

from chromatin.plugins.core.messages import (AddPlugin, ShowPlugins, SetupPlugins, UpdatePlugins, Activate, Deactivate,
                                             Reboot)
from chromatin.env import Env
from chromatin.plugins.core.main import Core

config: Config = Config(
    name='chromatin',
    prefix='crm',
    state_type=Env,
    components=Map(core=Core),
    settings=PluginSettings('chromatin'),
    core_components=List('core'),
    request_handlers=List(
        RequestHandler.json_msg_cmd(AddPlugin)(name='cram', prefix=Plain()),
        RequestHandler.msg_cmd(SetupPlugins)(),
        RequestHandler.msg_cmd(ShowPlugins)(),
        RequestHandler.msg_cmd(Activate)(),
        RequestHandler.msg_cmd(Deactivate)(),
        RequestHandler.msg_cmd(Reboot)(),
        RequestHandler.msg_cmd(UpdatePlugins)(name='update'),
    )
)

__all__ = ('config',)
