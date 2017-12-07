from typing import Any

from kallikrein import k, Expectation
from kallikrein.matchers import contain

from ribosome.test.integration.run import DispatchHelper
from ribosome.nvim.io import NS
from ribosome.plugin_state import PluginState
from ribosome.dispatch.data import DIO, GatherIOsDIO, GatherSubprocsDIO
from ribosome.dispatch.execute import execute_io
from ribosome.trans.action import TransResult, TransAction
from ribosome.process import SubprocessResult

from amino import Just, Map, List, Nil, Right, Path
from amino.test.spec import SpecBase
from amino.test import temp_dir, fixture_path

from chromatin import config
from chromatin.venv import Venv, ActiveVenv

name = 'flagellum'


class AddSpec(SpecBase):
    '''
    add a plugin $add
    '''

    @property
    def spec(self) -> str:
        return str(fixture_path('rplugin', name))

    def add(self) -> Expectation:
        dir = temp_dir('rplugin', 'venv')
        vars = dict(
            chromatin_rplugins=[dict(name=name, spec=self.spec)],
            chromatin_venv_dir=str(dir),
        )
        venv = Venv(name, dir / name, Right(Path('/dev/null')), Right(Path('/dev/null')))
        responses_strict = Map(
            {
                'jobstart': 3,
                'jobpid': 1111,
                'FlagellumRpcHandlers': [],
                'silent FlagellumStage1': 0,
                'silent FlagellumStage2': 0,
                'silent FlagellumStage3': 0,
                'silent FlagellumStage4': 0,
            }
        )
        def responses(req: str) -> Any:
            if req == 'FlagellumRpcHandlers':
                return Just([])
            else:
                return responses_strict.lift(req).o(Just(0))
        def x_io(dio: DIO) -> NS[PluginState, TransAction]:
            if isinstance(dio, GatherIOsDIO):
                return NS.pure(dio.io.handle_result(List(Right(venv))))
            elif isinstance(dio, GatherSubprocsDIO):
                return NS.pure(TransResult((List(SubprocessResult(0, Nil, Nil, venv)), Nil)))
            else:
                return execute_io(dio)
        helper = DispatchHelper.cons(config, 'core', vars=vars, responses=responses, io_executor=x_io)
        r = helper.loop('chromatin:command:cram', (self.spec, 'flagellum')).unsafe(helper.vim)
        return k(r.data.venvs.k).must(contain(name)) & k(r.data.active).must(contain(ActiveVenv(venv, 3, 1111)))

__all__ = ('AddSpec',)
