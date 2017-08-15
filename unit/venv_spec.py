import asyncio

from kallikrein import k, Expectation

from amino.test import temp_dir
from amino.test.spec import SpecBase

import ribosome
from ribosome import ProcessExecutor

from chromatin.venvs import Venvs, package_state
from chromatin.plugin import VimPlugin


class VenvSpec(SpecBase):
    '''virtualenv management
    install a package $install_package
    '''

    def install_package(self) -> Expectation:
        ribosome.in_vim = False
        dir = temp_dir('venv', 'root')
        venvs = Venvs(dir)
        plugin = VimPlugin(spec='amino')
        venv = venvs.bootstrap(plugin).attempt.value
        j = venvs.install(venv)
        x = ProcessExecutor()
        f = x.run(j)
        s = asyncio.get_event_loop().run_until_complete(f)
        print(s.out)
        return k(1) == 1

__all__ = ('VenvSpec',)
