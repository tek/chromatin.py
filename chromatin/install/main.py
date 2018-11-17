from amino.case import Case
from amino.logging import module_log
from amino import List, do, Do

from ribosome.nvim.io.compute import NvimIO
from ribosome.process import Subprocess

from chromatin.model.rplugin import InstallableRpluginMeta, InstallableRplugin, VenvRplugin, HsInstallableRplugin
from chromatin.venv import venv_from_rplugin
from chromatin.install.python import install_venv_rplugin_args
from chromatin.install.haskell import install_hs_rplugin

log = module_log()


class install_rplugin_subproc(Case[InstallableRpluginMeta, NvimIO[Subprocess[str]]], alg=InstallableRpluginMeta):

    def __init__(self, rplugin: InstallableRplugin) -> None:
        self.rplugin = rplugin

    @do(NvimIO[Subprocess[str]])
    def venv(self, venv_rplugin: VenvRplugin) -> Do:
        log.debug(f'installing {venv_rplugin}')
        venv = yield venv_from_rplugin(self.rplugin.rplugin)
        pip_bin = venv.meta.bin_path / 'pip'
        specific_args = install_venv_rplugin_args.match(venv_rplugin.conf)
        extensions = self.rplugin.rplugin.extensions
        args = List('install', '-U', '--no-cache') + specific_args + extensions
        return Subprocess(pip_bin, args, self.rplugin.rplugin.name, timeout=120)

    def hs(self, a: HsInstallableRplugin) -> NvimIO[Subprocess[str]]:
        return install_hs_rplugin(self.rplugin)(a.conf)


__all__ = ('install_rplugin_subproc',)
