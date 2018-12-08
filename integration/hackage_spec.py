from kallikrein import Expectation, k, pending

from integration._support.venv import test_config

from amino import do, Do
from amino.test.spec import SpecBase
from ribosome.nvim.api.exists import wait_for_function
from ribosome.nvim.api.variable import variable_set_prefixed
from ribosome.nvim.io.state import NS
from ribosome.test.prog import request
from ribosome.test.integration.external import external_state_test

from chromatin.config.state import ChromatinState


@do(NS[ChromatinState, Expectation])
def hackage_spec() -> Do:
    yield NS.lift(variable_set_prefixed('autostart', True))
    yield request('cram', f'hackage:proteome', name='proteome')
    yield NS.lift(wait_for_function('ProAdd', timeout=1))
    return k(1) == 1


class HackageSpec(SpecBase):
    '''
    haskell hackage plugin $hackage
    '''

    def hackage(self) -> Expectation:
        return external_state_test(test_config, hackage_spec)


__all__ = ('HackageSpec',)
