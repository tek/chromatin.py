from ribosome.test.integration.klk import AutoPluginIntegrationKlkSpec


class DefaultSpec(AutoPluginIntegrationKlkSpec):

    def config_name(self) -> str:
        return 'config'

    def plugin_name(self) -> str:
        return 'chromatin'

    def plugin_prefix(self) -> str:
        return 'crm'


__all__ = ('DefaultSpec',)
