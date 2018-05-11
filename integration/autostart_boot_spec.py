from kallikrein import k, Expectation

from amino.test.spec import SpecBase
from amino import List, do, Do

from ribosome.nvim.io.compute import NvimIO

from integration._support.flag_test import name
from integration._support.venv import cached_venvs_test, plug_exists, test_config


@do(NvimIO[Expectation])
def startup_spec() -> Do:
    yield plug_exists('Flag')


class AutostartAtBootSpec(SpecBase):
    '''automatic initialization at vim startup $startup
    '''

    def startup(self) -> Expectation:
        config = test_config.append.vars(('chromatin_autostart', True))
        return cached_venvs_test(List(name), startup_spec, config=config)


__all__ = ('AutostartAtBootSpec',)
