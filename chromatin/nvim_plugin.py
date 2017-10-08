from amino import List, Map

from ribosome import AutoPlugin, msg_command, json_msg_command
from ribosome.settings import Config, PluginSettings

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
)


class ChromatinNvimPlugin(AutoPlugin):

    @json_msg_command(AddPlugin)
    def cram(self) -> None:
        pass

    @msg_command(ShowPlugins)
    def crm_show_plugins(self) -> None:
        pass

    @msg_command(SetupPlugins)
    def crm_setup_plugins(self) -> None:
        pass

    @msg_command(Activate)
    def crm_activate(self) -> None:
        pass

    @msg_command(Deactivate)
    def crm_deactivate(self) -> None:
        pass

    @msg_command(Reboot)
    def crm_reboot(self) -> None:
        pass

    @msg_command(UpdatePlugins)
    def crm_update(self) -> None:
        pass

__all__ = ('ChromatinNvimPlugin', 'config')
