from amino import List, Just

from ribosome.rpc.api import rpc
from ribosome.config.config import Config
from ribosome.rpc.data.prefix_style import Plain, Full

from chromatin.env import Env
from chromatin.components.core.trans.install import update_plugins, activate, deactivate, reboot
from chromatin.components.core.trans.setup import init, setup_plugins, show_plugins, add_plugin

chromatin_config: Config = Config.cons(
    name='chromatin',
    prefix='crm',
    state_ctor=Env.cons,
    rpc=List(
        rpc.write(init).conf(prefix=Full()),
        rpc.write(add_plugin).conf(name=Just('cram'), prefix=Plain(), json=True),
        rpc.write(setup_plugins),
        rpc.write(show_plugins),
        rpc.write(activate),
        rpc.write(deactivate),
        rpc.write(reboot),
        rpc.write(update_plugins).conf(name=Just('update')),
    ),
    init=init,
)

__all__ = ('config',)
