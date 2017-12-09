import pkg_resources

from amino import Either, Boolean, Path, Maybe, L, _
from amino.dispatch import dispatch_alg

from chromatin.model.venv import (VenvStatus, VenvExistent, VenvAbsent, cons_venv, VenvPackageStatus,
                                  VenvPackageExistent, VenvPackageAbsent, Venv)
from chromatin.model.rplugin import (DirRplugin, SiteRplugin, VenvRplugin, Rplugin, RpluginStatus, RpluginReady,
                                     RpluginAbsent)


def check_venv(base_dir: Path, plugin: Rplugin) -> VenvStatus:
    dir = base_dir / plugin.name
    return (
        VenvExistent(plugin, cons_venv(dir, plugin))
        if dir.exists() else
        VenvAbsent(plugin)
    )


def venv_package_status(venv: Venv, req: str) -> VenvPackageStatus:
    ws = pkg_resources.WorkingSet([venv.site])
    req = pkg_resources.Requirement(req)
    return Maybe.check(ws.by_key.get(req.key)) / L(VenvPackageExistent)(venv, _) | VenvPackageAbsent(venv)


def venv_package_status_main(venv: Venv) -> VenvPackageStatus:
    return venv_package_status(venv, venv.name)


def venv_package_installed(venv: Venv) -> Boolean:
    return venv_package_status_main(venv).exists


class RpluginFacade:

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.ready = dispatch_alg(self, Rplugin, 'ready_')

    def check(self, plugin: Rplugin) -> RpluginStatus:
        return self.ready(plugin)

    def ready_dir_rplugin(self, rplugin: DirRplugin) -> RpluginStatus:
        return Boolean(Path(rplugin.spec).is_dir()).c(RpluginReady(rplugin), RpluginAbsent(rplugin))

    def ready_site_rplugin(self, rplugin: SiteRplugin) -> RpluginStatus:
        return (
            Either.import_module(rplugin.spec)
            .cata(lambda a: RpluginAbsent(rplugin), lambda a: RpluginReady(rplugin))
        )

    def ready_venv_rplugin(self, rplugin: VenvRplugin) -> RpluginStatus:
        venv_status = check_venv(self.base_dir, rplugin)
        package_status = Boolean(venv_status.exists and venv_package_installed(venv_status.venv))
        ctor = package_status.cata(RpluginReady, RpluginAbsent)
        return ctor(rplugin)


__all__ = ('RpluginFacade',)
