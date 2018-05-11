from kallikrein import Expectation

from amino.test.spec import SpecBase
from amino import do, Do, Map, List
from amino.test.path import pkg_dir

from ribosome.nvim.io.compute import NvimIO
from ribosome.test.klk.matchers.command import command_must_not_exist
from ribosome.nvim.api.command import runtime, nvim_command
from ribosome.nvim.api.option import option_cat
from ribosome.test.integration.embed import plugin_test
from ribosome.test.klk.expectation import await_k
from ribosome.nvim.api.exists import command_once_defined

from integration._support.venv import plug_exists, test_config
from integration._support.flag_cil_test import name1, path1

project = pkg_dir()
vars = Map(
    chromatin_autoreboot=False,
    chromatin_pip_req=str(project),
    chromatin_rplugins=List(dict(name=name1, spec=str(path1))),
)
bootstrap_config = test_config.mod.vars(lambda a: a ** vars).set.autostart(False)


@do(NvimIO[Expectation])
def bootstrap_spec() -> Do:
    yield option_cat('runtimepath', List(str(project)))
    cram_exists_not = yield await_k(command_must_not_exist, 'Cram')
    yield runtime('chromatin.nvim/plugin/bootstrap')
    yield nvim_command('BootstrapChromatin')
    yield command_once_defined('CrmSetupPlugins')
    plugin_exists = yield plug_exists('Flag', timeout=20)
    return cram_exists_not & plugin_exists


class BootstrapSpec(SpecBase):
    '''auto-install chromatin at boot $bootstrap
    '''

    def bootstrap(self) -> Expectation:
        return plugin_test(bootstrap_config, bootstrap_spec)


__all__ = ('BootstrapSpec',)
