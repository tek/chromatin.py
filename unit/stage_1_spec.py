from typing import Any

from kallikrein import k, Expectation
from kallikrein.matchers import contain
from kallikrein.matchers.either import be_right
from kallikrein.matchers.typed import have_type
from kallikrein.matchers.comparison import eq

from ribosome.test.integration.run import DispatchHelper
from ribosome.nvim.io import NS
from ribosome.plugin_state import PluginState
from ribosome.dispatch.data import DIO, GatherIOsDIO, GatherSubprocsDIO
from ribosome.dispatch.execute import execute_io
from ribosome.process import SubprocessResult

from amino import Just, Map, List, Nil, Right, Path, _
from amino.test.spec import SpecBase
from amino.test import temp_dir, fixture_path

from chromatin import config
from chromatin.model.venv import Venv, VenvMeta
from chromatin.model.rplugin import cons_rplugin, ActiveRpluginMeta, VenvRplugin

name = 'flagellum'


class Stage1Spec(SpecBase):
    '''
    create one virtualenv $one
    dogfood chromatin $crm_rplugin
    '''

    @property
    def spec(self) -> str:
        return str(fixture_path('rplugin', name))

    def one(self) -> Expectation:
        dir = temp_dir('rplugin', 'venv')
        vars = dict(
            chromatin_rplugins=[dict(name=name, spec=self.spec)],
            chromatin_venv_dir=str(dir),
        )
        rplugin = cons_rplugin(name, self.spec)
        venv = Venv(rplugin, VenvMeta(name, dir / name, Right(Path('/dev/null')), Right(Path('/dev/null'))))
        active_rplugin = ActiveRpluginMeta(rplugin.name, 3, 1111)
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
        def x_io(dio: DIO) -> NS[PluginState, Any]:
            if isinstance(dio, GatherIOsDIO):
                return NS.pure(List(Right(venv)))
            elif isinstance(dio, GatherSubprocsDIO):
                return NS.pure(List(Right(SubprocessResult(0, Nil, Nil, venv))))
            else:
                return execute_io(dio)
        helper = DispatchHelper.cons(config, vars=vars, responses=responses, io_executor=x_io)
        r = helper.loop('command:stage_1').unsafe(helper.vim)
        return k(r.data.venvs.k).must(contain(name)) & k(r.data.active).must(contain(active_rplugin))

    def crm_rplugin(self) -> Expectation:
        helper = DispatchHelper.cons(config)
        r = helper.loop('command:stage_1').unsafe(helper.vim)
        rplugin = r.data.chromatin_rplugin.to_either('no chromatin rplugin')
        venv = r.data.chromatin_venv.to_either('no chromatin venv')
        return (
            k(rplugin).must(be_right(VenvRplugin('chromatin', 'chromatin'))) &
            k(venv // _.meta.python_executable).must(be_right(have_type(Path))) &
            k(venv / _.meta.rplugin).must(eq(rplugin / _.name))
        )


__all__ = ('Stage1Spec',)
