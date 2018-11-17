from kallikrein import Expectation, k

from integration._support.venv import log_entry, test_config

from amino import do, Do
from amino.test import fixture_path
from amino.test.spec import SpecBase
from ribosome.nvim.api.exists import wait_for_command, wait_for_function
from ribosome.test.klk.expectation import await_k
from ribosome.nvim.api.variable import variable_set_prefixed
from ribosome.nvim.io.state import NS
from ribosome.test.prog import request
from ribosome.test.integration.external import external_state_test

from chromatin.config.state import ChromatinState


@do(NS[ChromatinState, Expectation])
def dir_venv_spec() -> Do:
    flag_dir = fixture_path('rplugin', 'flagellum')
    yield NS.lift(variable_set_prefixed('autostart', True))
    yield request('cram', f'dir:{flag_dir}', name='flagellum')
    yield NS.lift(wait_for_command('FlagTest', timeout=1))
    yield NS.lift(await_k(log_entry, 'flagellum initialized'))


@do(NS[ChromatinState, Expectation])
def hs_dir_spec() -> Do:
    flag_dir = fixture_path('rplugin', 'flagellum.hs')
    yield NS.lift(variable_set_prefixed('autostart', True))
    yield request('cram', f'hs_dir:{flag_dir}', name='flagellum')
    yield NS.lift(wait_for_function('FlagTest', timeout=1))
    return k(1) == 1


class DirRpluginSpec(SpecBase):
    '''
    run an rplugin from a directory $dir_venv
    haskell stack dir plugin $hs
    '''

    def dir_venv(self) -> Expectation:
        return external_state_test(test_config, dir_venv_spec)

    def hs(self) -> Expectation:
        return external_state_test(test_config, hs_dir_spec)


__all__ = ('DirRpluginSpec',)
