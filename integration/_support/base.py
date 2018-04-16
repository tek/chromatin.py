from ribosome.test.integration.klk import AutoPluginIntegrationKlkSpec, VimIntegrationKlkSpec


class DefaultSpec(AutoPluginIntegrationKlkSpec):

    def plugin_name(self) -> str:
        return 'chromatin'

    def plugin_short_name(self) -> str:
        return 'crm'


class ExternalSpec(VimIntegrationKlkSpec):

    def plugin_name(self) -> str:
        return 'chromatin'

    def plugin_short_name(self) -> str:
        return 'crm'


__all__ = ('DefaultSpec', 'ExternalSpec')
