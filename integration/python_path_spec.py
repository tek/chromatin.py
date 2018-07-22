from kallikrein import Expectation, k

from integration._support.venv import test_config

from amino import do, Do
from amino.test import fixture_path
from amino.test.spec import SpecBase
from ribosome.nvim.api.exists import call_once_defined
from ribosome.nvim.api.variable import variable_set_prefixed
from ribosome.nvim.io.state import NS
from ribosome.test.prog import request
from ribosome.test.integration.external import external_state_test

from chromatin.config.state import ChromatinState


@do(NS[ChromatinState, Expectation])
def python_path_spec() -> Do:
    dir = fixture_path('rplugin', 'path_spec')
    extra_path_pkg = fixture_path('rplugin', 'extra_path_pkg')
    yield NS.lift(variable_set_prefixed('autostart', True))
    yield request('cram', f'dir:{dir}', name='path_spec', pythonpath=[extra_path_pkg])
    result = yield NS.lift(call_once_defined('PathSpecTest', timeout=10))
    return k(result) == 13


class PythonPathSpec(SpecBase):
    '''
    amend the default python path $python_path
    '''

    def python_path(self) -> Expectation:
        return external_state_test(test_config, python_path_spec)


__all__ = ('PythonPathSpec',)
