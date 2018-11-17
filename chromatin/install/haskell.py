from amino.case import Case
from amino import List, do, Do

from ribosome.nvim.io.compute import NvimIO
from ribosome.process import Subprocess
from ribosome.nvim.io.api import N

from chromatin.model.rplugin import (HsRpluginMeta, InstallableRplugin, HsStackageRplugin, HsStackDirRplugin,
                                     HsHackageRplugin)
from chromatin.util.interpreter import stack_exe, cabal_exe


class install_hs_rplugin(Case[HsRpluginMeta, NvimIO[Subprocess[str]]], alg=HsRpluginMeta):

    def __init__(self, rplugin: InstallableRplugin) -> None:
        self.rplugin = rplugin

    @do(NvimIO[Subprocess[str]])
    def hackage(self, a: HsHackageRplugin) -> Do:
        cabal = yield N.from_io(cabal_exe())
        return Subprocess(cabal, List('install', a.dep), self.rplugin.rplugin.name, 600, env=None)

    @do(NvimIO[Subprocess[str]])
    def stackage(self, a: HsStackageRplugin) -> Do:
        stack = yield N.from_io(stack_exe())
        return Subprocess(stack, List('install', a.dep), self.rplugin.rplugin.name, 600, env=None)

    @do(NvimIO[Subprocess[str]])
    def dir(self, a: HsStackDirRplugin) -> Do:
        stack = yield N.from_io(stack_exe())
        return Subprocess(stack, List('install'), self.rplugin.rplugin.name, 600, cwd=a.dir, env=None)


__all__ = ('install_hs_rplugin',)
