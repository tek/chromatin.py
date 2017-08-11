from kallikrein import k, Expectation

from integration._support.base import ChromatinPluginIntegrationSpec


class AddSpec(ChromatinPluginIntegrationSpec):
    '''
    test $test
    '''

    def test(self) -> Expectation:
        print(self.content)
        return k(1) == 1

__all__ = ('AddSpec',)
