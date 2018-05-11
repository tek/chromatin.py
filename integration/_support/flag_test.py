from typing import Callable

from amino import do, List, Do

from ribosome.nvim.api.exists import wait_for_command

from kallikrein import Expectation
from ribosome.nvim.io.compute import NvimIO
from ribosome.test.klk.expectation import await_k

from integration._support.venv import log_entry, cached_venvs_test

name = 'flagellum'


@do(NvimIO[Expectation])
def flag_spec(spec: Callable[[], NvimIO[Expectation]]) -> Do:
    yield wait_for_command('FlagTest')
    yield await_k(log_entry, 'flagellum initialized')
    yield spec()


def flag_test(spec: Callable[[], NvimIO[Expectation]]) -> Expectation:
    return cached_venvs_test(List(name), lambda: flag_spec(spec))


__all__ = ('flag_spec', 'flag_test',)
