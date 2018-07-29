from __future__ import annotations
from typing import Tuple

from amino import do, __, List, _, Boolean, L, Either, Nil, Right, Left, IO, Maybe, Dat, Just, Nothing, Path
from amino.do import Do
from amino.state import State, EitherState
from amino.lenses.lens import lens
from amino.logging import module_log
from amino.case import Case
from ribosome.nvim.io.state import NS
from ribosome import ribo_log
from ribosome.compute.api import prog
from ribosome.compute.output import Echo, GatherIOs
from ribosome.compute.ribosome_api import Ribo

from chromatin.components.core.logic import add_crm_venv, read_conf, activate_newly_installed, add_venv
from chromatin.model.rplugin import (Rplugin, cons_rplugin, ConfigRplugin, VenvRplugin, DistVenvRplugin, DirVenvRplugin,
                                     DirRplugin, SiteRplugin)
from chromatin.components.core.trans.install import install_rplugins
from chromatin.model.rplugin import DistRplugin
from chromatin.model.venv import Venv, VenvStatus, VenvPresent, VenvAbsent
from chromatin.util import resources
from chromatin.settings import venv_dir, autostart, interpreter
from chromatin.config.resources import ChromatinResources
from chromatin.env import Env
from chromatin.components.core.trans.tpe import CrmRibosome
from chromatin.rplugin import venv_rplugin_status, cons_venv_rplugin, bootstrap_venv

log = module_log()


@prog
@do(NS[CrmRibosome, List[Rplugin]])
def initialize() -> Do:
    yield add_crm_venv()
    yield Ribo.zoom_main(read_conf())


@prog
@do(NS[Env, None])
def bootstrap_result(result: List[Either[str, str]]) -> Do:
    def split(z: Tuple[List[str], List[Venv]], a: Either[str, Venv]) -> Tuple[List[str], List[Venv]]:
        err, vs = z
        return a.cata((lambda e: (err.cat(e), vs)), (lambda v: (err, vs.cat(v))))
    errors, venvs = result.fold_left((Nil, Nil))(split)
    ribo_log.debug(f'bootstrapped venvs: {venvs}')
    yield venvs.traverse(add_venv, State).nvim
    error = errors.map(str).join_comma
    ret = Left(f'failed to setup venvs: {error}') if errors else Right(None)
    yield NS.e(ret)


class rplugin_bootstrap_compute(Case[VenvStatus, IO[str]], alg=VenvStatus):

    def __init__(self, global_interpreter: Maybe[Path], dir: Path) -> None:
        self.global_interpreter = global_interpreter
        self.dir = dir

    def present(self, status: VenvPresent) -> IO[str]:
        return IO.pure(status.venv.name)

    def absent(self, status: VenvAbsent) -> IO[str]:
        return bootstrap_venv(self.global_interpreter, self.dir, status.rplugin)



@do(NS[CrmRibosome, List[VenvRplugin]])
def venv_rplugins() -> Do:
    plugins = yield Ribo.inspect_main(_.rplugins)
    return plugins.flat_map(cons_venv_rplugin.match)


@prog.io.gather
@do(NS[CrmRibosome, GatherIOs[List[Either[str, Maybe[Venv]]]]])
def bootstrap_rplugins_io() -> Do:
    vr = yield venv_rplugins()
    dir = yield Ribo.setting(venv_dir)
    global_interpreter = yield Ribo.setting_raw(interpreter)
    status = yield NS.from_io(vr.traverse(lambda a: venv_rplugin_status(dir, a), IO))
    ios = status.map(rplugin_bootstrap_compute(global_interpreter.to_maybe, dir))
    yield NS.pure(GatherIOs(ios, timeout=30))


@prog.do(None)
def bootstrap_rplugins() -> Do:
    '''check whether a venv exists for each venv or dir plugin in the env.
    for those that don't have one, create venvs in `g:chromatin_venv_dir`.
    '''
    result = yield bootstrap_rplugins_io()
    yield bootstrap_result(result)


@prog
@do(NS[CrmRibosome, None])
def post_setup() -> Do:
    yield activate_newly_installed()


@prog.do(None)
def setup_plugins() -> Do:
    yield bootstrap_rplugins()
    yield install_rplugins()
    yield post_setup()


@prog
@do(NS[CrmRibosome, Boolean])
def add_plugins(rplugins: List[Rplugin]) -> None:
    yield Ribo.zoom_main(NS.modify(lambda s: s.append.rplugins(rplugins)))
    yield Ribo.setting(autostart)


@prog.do(None)
def plugins_added(plugins: List[Rplugin]) -> Do:
    autostart = yield add_plugins(plugins)
    if autostart:
        yield setup_plugins()


@prog.do(None)
def init() -> Do:
    plugins = yield initialize()
    yield plugins_added(plugins)


@prog.echo
@do(NS[CrmRibosome, Echo])
def show_plugins() -> Do:
    dir = yield Ribo.setting(venv_dir)
    rplugins = yield Ribo.inspect_main(lambda a: a.rplugins)
    return Echo.info(resources.show_plugins(dir, rplugins))


class AddPluginOptions(Dat['AddPluginOptions']):

    @staticmethod
    def cons(
            name: str=None,
            pythonpath: List[str]=None,
            debug: bool=None,
            interpreter: str=None,
            extensions: List[str]=None,
    ) -> AddPluginOptions:
        return AddPluginOptions(
            Maybe.optional(name),
            Maybe.optional(pythonpath),
            Maybe.optional(debug),
            Maybe.optional(interpreter),
            Maybe.optional(extensions),
        )

    def __init__(
            self,
            name: Maybe[str],
            pythonpath: Maybe[List[str]],
            debug: Maybe[bool],
            interpreter: Maybe[str],
            extensions: Maybe[List[str]],
    ) -> None:
        self.name = name
        self.pythonpath = pythonpath
        self.debug = debug
        self.interpreter = interpreter
        self.extensions = extensions


@prog.do(None)
def add_plugin(spec: str, options: AddPluginOptions) -> Do:
    plugin = cons_rplugin(ConfigRplugin(spec, options.name, options.debug, options.pythonpath, options.interpreter,
                                        options.extensions))
    yield plugins_added(List(plugin))


__all__ = ('init', 'show_plugins')
