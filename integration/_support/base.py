from ribosome.test.integration.klk import AutoPluginIntegrationKlkSpec

from chromatin.logging import Logging


class IntegrationCommon:

    @property
    def _prefix(self) -> str:
        return 'chromatin'


class ChromatinPluginIntegrationSpec(IntegrationCommon, AutoPluginIntegrationKlkSpec, Logging):

    def _start_plugin(self) -> None:
        if self.autostart_plugin:
            return
            self.vim.cmd_once_defined('ChromatinStage1')
            self.pvar_becomes('started', True)


class DefaultSpec(ChromatinPluginIntegrationSpec):

    def config_name(self) -> str:
        return 'config'

    def module(self) -> str:
        return 'chromatin'

    @property
    def plugin_prefix(self) -> str:
        return 'Crm'

__all__ = ('ChromatinPluginIntegrationSpec', 'DefaultSpec')
