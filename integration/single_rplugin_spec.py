from kallikrein import Expectation, k
from kallikrein.matchers.comparison import not_equal, greater
from kallikrein.matcher import Matcher
from kallikrein.matchers.typed import have_type

from amino import List, do, Do
from amino.test.spec import SpecBase
from amino.util.string import camelcase

from ribosome.nvim.api.command import nvim_command, doautocmd, nvim_sync_command
from ribosome.nvim.api.function import nvim_call_tpe, nvim_call_json
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.io.api import N
from ribosome.test.klk.expectation import await_k
from ribosome.test.klk.matchers.variable import var_must_become
from ribosome.nvim.api.rpc import plugin_name
from ribosome.test.klk.matchers.command import command_must_not_exist
from ribosome.nvim.io.data import NError

from chromatin.util import resources

from integration._support.venv import log_entry
from integration._support.flag_test import flag_test, name


@do(NvimIO[Expectation])
def cmd_parameter_spec() -> Do:
    yield nvim_command('FlagArgTest', 1)
    yield await_k(log_entry, 'success 1')


@do(NvimIO[Expectation])
def autocmd_spec() -> Do:
    yield doautocmd('VimEnter')
    yield await_k(log_entry, 'autocmd works')


@do(NvimIO[Expectation])
def config_spec() -> Do:
    yield nvim_command('FlagConfTest')
    x1 = yield var_must_become('flagellum_value', 'success')
    x2 = yield await_k(log_entry, 'success')
    return x1 & x2


@do(NvimIO[Expectation])
def update_spec() -> Do:
    yield nvim_sync_command('CrmUpdate')
    yield await_k(log_entry, resources.updated_plugin(name), timeout=10)


@do(NvimIO[Expectation])
def twice_spec() -> Do:
    yield nvim_sync_command('CrmActivate')
    yield await_k(log_entry, resources.already_active(List(name)))


@do(NvimIO[int])
def flag_channel_id() -> Do:
    name = yield plugin_name()
    state = yield nvim_call_json(f'{camelcase(name)}State')
    active = yield N.m(state.active.head, 'no active rplugins')
    return active.channel


@do(NvimIO[Expectation])
def flag_channel_id_becomes(matcher: Matcher[int], timeout: float=1., interval: float=.25) -> Do:
    id = yield flag_channel_id()
    return k(id).must(matcher)


@do(NvimIO[Expectation])
def flag_jobpid_becomes(matcher: Matcher[int], timeout: float=1., interval: float=.25) -> Do:
    id = yield flag_channel_id()
    pid = yield nvim_call_tpe(int, 'jobpid', id)
    return k(pid).must(matcher)


@do(NvimIO[Expectation])
def deactivate_spec() -> Do:
    yield await_k(flag_channel_id_becomes, not_equal(-1))
    channel = yield flag_channel_id()
    yield await_k(flag_jobpid_becomes, greater(0))
    yield nvim_command('CrmDeactivate')
    command_nonexistent = yield await_k(command_must_not_exist, 'FlagTest', timeout=10)
    quit_var = yield var_must_become('flagellum_quit', 1)
    pid = yield N.safe(nvim_call_tpe(int, 'jobpid', channel))
    return (
        command_nonexistent &
        k(pid).must(have_type(NError)) &
        quit_var
    )


class SingleRpluginSpec(SpecBase):
    '''activate and deactivate plugin hosts
    test command with a parameter $cmd_parameter
    execute autocommand $autocmd
    load plugin config from `rtp/chromatin/flagellum` after activation $config
    update a plugin $update
    don't start two hosts if `SetupPlugins` runs again $twice
    deactivate a plugin $deactivate
    '''

    def cmd_parameter(self) -> Expectation:
        return flag_test(cmd_parameter_spec)

    def autocmd(self) -> Expectation:
        return flag_test(autocmd_spec)

    def config(self) -> Expectation:
        return flag_test(config_spec)

    def update(self) -> Expectation:
        return flag_test(update_spec)

    def twice(self) -> Expectation:
        return flag_test(twice_spec)

    def deactivate(self) -> Expectation:
        return flag_test(deactivate_spec)


__all__ = ('SingleRpluginSpec',)
