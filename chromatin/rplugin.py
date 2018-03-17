import pkg_resources

from amino import Either, Boolean, Path, Maybe, L, _, do, IO, Do
from amino.dispatch import dispatch_alg, PatMat
from amino.boolean import false

from chromatin.model.venv import (VenvStatus, VenvExistent, VenvAbsent, cons_venv, VenvPackageStatus,
                                  VenvPackageExistent, VenvPackageAbsent, Venv)
from chromatin.model.rplugin import (DirRplugin, SiteRplugin, VenvRplugin, Rplugin, RpluginStatus, RpluginReady,
                                     RpluginAbsent)


@do(IO[VenvStatus])
def venv_existent(dir: Path, plugin: Rplugin) -> Do:
    venv = yield cons_venv(dir, plugin)
    return VenvExistent(plugin, venv)


@do(IO[VenvStatus])
def check_venv(base_dir: Path, plugin: Rplugin) -> Do:
    dir = base_dir / plugin.name
    exists = yield IO.delay(dir.exists)
    yield (
        venv_existent(dir, plugin)
        if exists else
        IO.pure(VenvAbsent(plugin))
    )


@do(IO[VenvPackageStatus])
def venv_package_status(venv: Venv, req: str) -> Do:
    ws = yield IO.delay(pkg_resources.WorkingSet, [venv.site])
    req = yield IO.delay(pkg_resources.Requirement, req)
    return Maybe.check(ws.by_key.get(req.key)) / L(VenvPackageExistent)(venv, _) | VenvPackageAbsent(venv)


def venv_package_status_main(venv: Venv) -> IO[VenvPackageStatus]:
    return venv_package_status(venv, venv.name)


@do(IO[Boolean])
def venv_package_installed(venv: Venv) -> Do:
    status = yield venv_package_status_main(venv)
    return status.exists


class venv_status_check(PatMat, alg=VenvStatus):

    def venv_existent(self, status: VenvExistent) -> IO[Boolean]:
        return venv_package_installed(status.venv)

    def venv_absent(self, status: VenvAbsent) -> IO[Boolean]:
        return IO.pure(false)


class rplugin_installed(PatMat[Rplugin, IO[RpluginStatus]], alg=Rplugin):

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    @do(IO[RpluginStatus])
    def dir_rplugin(self, rplugin: DirRplugin) -> Do:
        is_dir = yield IO.delay(Path(rplugin.spec).is_dir)
        return RpluginReady(rplugin) if is_dir else RpluginAbsent(rplugin)

    def site_rplugin(self, rplugin: SiteRplugin) -> IO[RpluginStatus]:
        return IO.pure(
            RpluginReady(rplugin)
            if Either.import_module(rplugin.spec).present
            else RpluginAbsent(rplugin)
        )

    @do(IO[RpluginStatus])
    def venv_rplugin(self, rplugin: VenvRplugin) -> Do:
        venv_status = yield check_venv(self.base_dir, rplugin)
        exists = yield venv_status_check.match(venv_status)
        ctor = exists.cata(RpluginReady, RpluginAbsent)
        return ctor(rplugin)


__all__ = ('RpluginFacade',)
