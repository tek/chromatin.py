from typing import Any, Tuple, TypeVar, Generic

from amino import Map, List, Either, Nil, Right, Path, __
from amino.case import Case
from amino.test import temp_dir, fixture_path
from amino.lenses.lens import lens

from ribosome.nvim.api.data import StrictNvimApi
from ribosome import NvimApi
from ribosome.test.integration.run import Handler, RequestHelper
from ribosome.compute.output import (ProgIO, ProgGatherIOs, GatherIOs, ProgGatherSubprocesses, GatherSubprocesses, Echo,
                                     ProgIOEcho)
from ribosome.compute.prog import Prog
from ribosome.process import SubprocessResult
from ribosome.nvim.io.state import NS
from ribosome.compute.api import prog

from chromatin.model.venv import Venv, VenvMeta
from chromatin.config.config import chromatin_config
from chromatin.settings import ChromatinSettings
from chromatin.env import Env
from chromatin.config.component import ChromatinComponent
from chromatin.model.rplugin import cons_rplugin

from unit._support.log_buffer_env import LogBufferEnv

A = TypeVar('A')
function_responses = Map(
    jobstart=3,
    jobpid=1111,
    jobstop=0,
    FlagellumRpcHandlers='[]',
)
command_responses = Map(
    FlagellumStage1=0,
    FlagellumStage2=0,
    FlagellumStage3=0,
    FlagellumStage4=0,
)
CrmRequestHelper = RequestHelper[ChromatinSettings, Env, ChromatinComponent]


def test_handler(responses: Map[str, Any]) -> Handler:
    def handler(vim: StrictNvimApi, name: str, args: List[Any]) -> Either[str, Tuple[NvimApi, Any]]:
        return responses.lift(name).map(lambda a: (vim, a)).to_either(Nil)
    return handler


def test_function_handler(**extra: Any) -> Handler:
    return test_handler(function_responses ** Map(extra))


def test_command_handler(**extra: Any) -> Handler:
    return test_handler(command_responses ** Map(extra))


@prog
def buffering_logger(msg: Echo) -> NS[LogBufferEnv, None]:
    return NS.modify(__.append1.log_buffer(msg))


class single_venv_io_interpreter(Generic[A], Case[ProgIO, Prog[A]], alg=ProgIO):

    def __init__(self, venv: Venv) -> None:
        self.venv = venv

    def prog_gather_ios(self, output_type: ProgGatherIOs, output: GatherIOs[A]) -> Prog[A]:
        return Prog.pure(List(Right(self.venv)))

    def prog_gather_subprocesses(self, output_type: ProgGatherSubprocesses, output: GatherSubprocesses[A]) -> Prog[A]:
        return Prog.pure(List(Right(SubprocessResult(0, Nil, Nil, self.venv))))

    def prog_io_echo(self, po: ProgIOEcho, output: Echo) -> Prog[None]:
        return buffering_logger(output).replace(None)

    def case_default(self, po: ProgIO, output: A) -> Prog[A]:
        return Prog.unit


def rplugin_dir(name: str) -> str:
    return str(fixture_path('rplugin', name))


def single_venv_data(name: str, spec: str, **extra_vars: Any) -> CrmRequestHelper:
    dir = temp_dir('rplugin', 'venv')
    vars = Map(chromatin_venv_dir=str(dir)) ** Map(extra_vars)
    rplugin = cons_rplugin(name, spec)
    venv = Venv(rplugin, VenvMeta(name, dir / name, Right(Path('/dev/null')), Right(Path('/dev/null'))))
    conf = lens.basic.state_ctor.set(LogBufferEnv.cons)(chromatin_config)
    return rplugin, venv, (
        RequestHelper.cons(conf, vars=vars, io_interpreter=single_venv_io_interpreter(venv), logger=buffering_logger)
        .strict(function_handler=test_function_handler(exists=1), command_handler=test_command_handler())
    )


def single_venv_helper(name: str, spec: str, **extra_vars: Any) -> CrmRequestHelper:
    i, i, helper = single_venv_data(name, spec, **extra_vars)
    return helper


__all__ = ('test_handler', 'test_function_handler', 'single_venv_io_interpreter', 'rplugin_dir', 'test_command_handler',
           'single_venv_data')
