from kallikrein import Expectation, k

from amino import do, Do, List
from amino.test import fixture_path
from amino.test.spec import SpecBase
from ribosome.nvim.api.exists import call_once_defined
from ribosome.nvim.api.variable import variable_set_prefixed, variable_set
from ribosome.nvim.io.state import NS
from ribosome.test.prog import request
from ribosome.test.integration.external import external_state_test

from chromatin.config.state import ChromatinState

from integration._support.venv import test_config

name = 'extension_spec'
ext_name = 'extension_spec_ext'


@do(NS[ChromatinState, Expectation])
def extension_spec() -> Do:
    dir = fixture_path('rplugin', name)
    extension_path = fixture_path('rplugin', ext_name)
    yield NS.lift(variable_set_prefixed('autostart', True))
    yield NS.lift(variable_set(f'{name}_components', List(f'{ext_name}.ext')))
    yield request('cram', f'dir:{dir}', name='extension_spec', extensions=[extension_path])
    result1 = yield NS.lift(call_once_defined('XTest', timeout=1))
    result2 = yield NS.lift(call_once_defined('XExtTest', timeout=1))
    return (k(result1) == 13) & (k(result2) == 23)


class ExtensionSpec(SpecBase):
    '''
    install an extension $extension
    '''

    def extension(self) -> Expectation:
        return external_state_test(test_config, extension_spec)


__all__ = ('ExtensionSpec',)
