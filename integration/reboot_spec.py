from kallikrein import Expectation, k
from kallikrein.matchers.maybe import be_just

from amino.test.path import fixture_path
from amino import _, do, Do
from amino.json import dump_json
from amino.test.spec import SpecBase

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.exists import call_once_defined, wait_for_function_undef
from ribosome.nvim.api.command import nvim_command
from ribosome.nvim.io.api import N
from ribosome.test.klk.expectation import await_k
from ribosome.nvim.api.function import nvim_call_json
from ribosome.test.klk.matchers.prog import seen_program

from integration._support.flag_test import flag_test, name

reboot_test = 'FlagRebootTest'
path = fixture_path('rplugin', 'flagellum2')
update_query = dict(patch=dict(query=f'rplugins(name={name})', data=dict(spec=str(path))))


@do(NvimIO[Expectation])
def check_path() -> Do:
    state = yield nvim_call_json(f'ChromatinState')
    return k(state.rplugins.head.map(_.spec)).must(be_just(str(path)))


@do(NvimIO[Expectation])
def reboot_spec() -> Do:
    before = yield call_once_defined(reboot_test)
    json = yield N.e(dump_json(update_query))
    yield nvim_command(f'CrmUpdateState {json}')
    yield seen_program('update_state')
    updated_path = yield await_k(check_path)
    yield nvim_command('CrmUpdate')
    yield nvim_command('CrmReboot')
    yield wait_for_function_undef(reboot_test)
    after = yield call_once_defined(reboot_test)
    return updated_path & (k(before) == 13) & (k(after) == 17)


class RebootSpec(SpecBase):
    '''deactivate and reactivate a plugin $reboot
    '''

    def reboot(self) -> Expectation:
        return flag_test(reboot_spec)


__all__ = ('RebootSpec',)
