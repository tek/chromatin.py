from typing import Callable

from kallikrein import Expectation
from kallikrein.expectation import AlgExpectation

from amino.test.spec import SpecBase
from amino import List, do, Do

from ribosome.nvim.api.exists import wait_for_command
from ribosome.nvim.io.compute import NvimIO
from ribosome.test.klk.expectation import await_k
from ribosome.test.klk.matchers.variable import var_must_become
from ribosome.test.klk.matchers.command import command_must_exist

from integration._support.venv import cached_venvs_test, log_entry

names = List('flagellum', 'cilia')


@do(NvimIO[Expectation])
def flag_cil_spec(spec: Callable[[], NvimIO[Expectation]]) -> Do:
    yield wait_for_command('FlagTest')
    yield wait_for_command('CilTest')
    yield await_k(log_entry, 'cilia initialized')
    yield spec()


def flag_cil_test(spec: Callable[[], NvimIO[Expectation]]) -> Expectation:
    return cached_venvs_test(names, lambda: flag_cil_spec(spec))


@do(NvimIO[Expectation])
def stages_spec() -> Do:
    entries = yield names.traverse(lambda a: await_k(log_entry, f'{a} initialized'), NvimIO)
    fvar = yield var_must_become('flag', 2)
    cvar = yield var_must_become('cil', 1)
    return entries.fold(AlgExpectation) & fvar & cvar


class MultiRpluginSpec(SpecBase):
    '''run initialization stages in sequence $stages
    '''

    def stages(self) -> Expectation:
        return flag_cil_test(stages_spec)


class ActivateMiscSpec(SpecBase):

    def proteome(self) -> Expectation:
        return cached_venvs_test(List('proteome'), lambda: await_k(command_must_exist, 'ProAdd'))


__all__ = ('MultiRpluginSpec',)
