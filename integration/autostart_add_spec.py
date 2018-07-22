from kallikrein import Expectation

from amino import do, Do
from amino.test.spec import SpecBase

from ribosome.nvim.io.compute import NvimIO
from ribosome.test.integration.embed import plugin_test

from integration._support.venv import test_config, setup_one_with_venvs, venv_existent, package_installed, plug_exists


@do(NvimIO[Expectation])
def auto_cram_spec() -> Do:
    venvs, venv_plugin = yield setup_one_with_venvs('flagellum')
    yield venv_existent(venvs, timeout=4)(venv_plugin.rplugin)
    yield package_installed(venvs)(venv_plugin.rplugin)
    yield plug_exists('Flag', timeout=30)


class AutostartAfterAddSpec(SpecBase):
    '''automatic initialization when using `Cram` $auto_cram
    '''

    def auto_cram(self) -> Expectation:
        config = test_config.append.vars(('chromatin_autostart', True))
        return plugin_test(config, auto_cram_spec)


__all__ = ('AutostartAfterAddSpec',)
