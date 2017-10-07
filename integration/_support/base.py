from amino import Right, Either

from ribosome.test.integration.klk import AutoPluginIntegrationKlkSpec

from chromatin.logging import Logging
from chromatin.nvim_plugin import ChromatinNvimPlugin


class IntegrationCommon:

    @property
    def _prefix(self) -> str:
        return 'chromatin'

    @property
    def plugin_class(self) -> Either[str, type]:
        return Right(ChromatinNvimPlugin)


class ChromatinPluginIntegrationSpec(IntegrationCommon, AutoPluginIntegrationKlkSpec, Logging):

    def _start_plugin(self) -> None:
        if self.autostart_plugin:
            self.vim.cmd_once_defined('ChromatinStage1')
            self.pvar_becomes('started', True)


class DefaultSpec(ChromatinPluginIntegrationSpec):

    def config_name(self) -> str:
        return 'config'

    def module(self) -> str:
        return 'chromatin.nvim_plugin'

    @property
    def plugin_prefix(self) -> str:
        return 'Crm'

__all__ = ('ChromatinPluginIntegrationSpec', 'DefaultSpec')
