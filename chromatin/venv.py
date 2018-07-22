import pkg_resources

from amino import Path, IO, do, Boolean, Maybe, Lists, Either
from amino.boolean import false
from amino.do import Do
from amino.logging import module_log
from amino.case import Case

from chromatin.util.interpreter import python_interpreter
from chromatin.model.venv import (Venv, VenvMeta, VenvPackageExistent, VenvPackageAbsent, VenvPackageStatus, VenvStatus,
                                  VenvPresent, VenvAbsent)

log = module_log()


@do(IO[Either[str, Path]])
def venv_site(venv: Venv) -> Do:
    lib_dir = venv.meta.dir / 'lib'
    libs = yield IO.delay(lib_dir.glob, 'python3.?')
    lib = Lists.wrap(libs).head.to_either(f'no python dirs in {lib_dir}')
    return lib.map(lambda a: a / 'site-packages')


@do(IO[Either[str, Path]])
def venv_plugin_path(venv: Venv) -> Do:
    site = yield venv_site(venv)
    return site.map(lambda a: a / venv.name / '__init__.py')


def cons_venv(dir: Path, name: str) -> Venv:
    bin_path = dir / 'bin'
    executable = bin_path / 'python'
    return Venv(name, VenvMeta(name, dir, executable, bin_path))


def cons_venv_under(base_dir: Path, name: str) -> Venv:
    return cons_venv(base_dir / name, name)


@do(IO[VenvPackageStatus])
def venv_package_status_site(venv: Venv, site: Path, req_spec: str) -> Do:
    ws = yield IO.delay(pkg_resources.WorkingSet, [site])
    req = yield IO.delay(pkg_resources.Requirement, req_spec)
    return Maybe.check(ws.by_key.get(req.key)).cata_strict(
        lambda a: VenvPackageExistent(venv, a),
        VenvPackageAbsent(venv),
    )


@do(IO[VenvPackageStatus])
def venv_package_status(venv: Venv, req: str) -> Do:
    site_e = yield venv_site(venv)
    yield site_e.cata(lambda a: IO.pure(VenvPackageAbsent(venv)), lambda a: venv_package_status_site(venv, a, req))


@do(IO[Boolean])
def venv_package_installed(venv: Venv) -> Do:
    status = yield venv_package_status(venv, venv.name)
    return status.exists


class venv_status_check(Case[VenvStatus, IO[Boolean]], alg=VenvStatus):

    def venv_present(self, status: VenvPresent) -> IO[Boolean]:
        return venv_package_installed(status.venv)

    def venv_absent(self, status: VenvAbsent) -> IO[Boolean]:
        return IO.pure(false)


__all__ = ('venv_site', 'venv_plugin_path', 'cons_venv', 'cons_venv_under', 'venv_package_status_site',
           'venv_package_status', 'venv_package_installed', 'venv_status_check',)
