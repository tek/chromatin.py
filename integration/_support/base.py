from amino import Right, Either

from ribosome.test.integration.klk import ExternalIntegrationKlkSpec, PluginIntegrationKlkSpec

from chromatin.logging import Logging
from chromatin.nvim_plugin import ChromatinNvimPlugin


class IntegrationCommon:

    @property
    def _prefix(self) -> str:
        return 'chromatin'

    @property
    def plugin_class(self) -> Either[str, type]:
        return Right(ChromatinNvimPlugin)


class ChromatinIntegrationSpec(IntegrationCommon, ExternalIntegrationKlkSpec):

    def _start_plugin(self) -> None:
        self.plugin.start_plugin()
        self._wait(.05)
        self._wait_for(lambda: self.vim.vars.p('started').present)


class ChromatinPluginIntegrationSpec(IntegrationCommon, PluginIntegrationKlkSpec, Logging):

    def _start_plugin(self) -> None:
        self._debug = True
        self.vim.cmd_sync('ChromatinStart')
        self._pvar_becomes('started', True)

__all__ = ('ChromatinIntegrationSpec', 'ChromatinPluginIntegrationSpec')
