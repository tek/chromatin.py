from amino import do, Do, Either, List, Path

from ribosome.nvim.io.state import NS

from chromatin.model.venv import Venv, VenvMeta
from chromatin.env import Env
from chromatin.model.rplugin import Rplugin, VenvRplugin
from chromatin.venv import cons_venv_under
from chromatin.settings import venv_dir
from chromatin.rplugin import cons_venv_rplugin


@do(NS[Env, List[Rplugin]])
def rplugins_with_crm() -> Do:
    rplugins = yield NS.inspect(lambda a: a.rplugins)
    crm = yield NS.inspect(lambda a: a.chromatin_rplugin)
    return rplugins.cons_m(crm)


@do(NS[Env, Either[str, Rplugin]])
def rplugin_by_name(name: str) -> Do:
    rplugins = yield rplugins_with_crm()
    return rplugins.find(lambda a: a.name == name).to_either(f'no rplugin with name `{name}`')


@do(NS[Env, Venv])
def venv_from_meta(venv_dir: Path, meta: VenvMeta) -> Do:
    rplugin_e = yield rplugin_by_name(meta.name)
    rplugin = yield NS.from_either(rplugin_e)
    return cons_venv_under(venv_dir, rplugin.name)


@do(NS[Env, VenvRplugin])
def venv_rplugin_from_name(dir: Path, name: str) -> Do:
    rplugin_e = yield rplugin_by_name(name)
    rplugin = yield NS.e(rplugin_e)
    yield NS.m(cons_venv_rplugin.match(rplugin), 'invalid rplugin registered as venv: {rplugin}')


@do(NS[Env, List[VenvRplugin]])
def venv_rplugins_from_names(names: List[str]) -> Do:
    dir = yield NS.lift(venv_dir.value)
    yield names.traverse(lambda a: venv_rplugin_from_name(dir, a), NS)


__all__ = ('rplugin_by_name', 'venv_from_meta', 'venv_rplugin_from_name', 'venv_rplugins_from_names',)
