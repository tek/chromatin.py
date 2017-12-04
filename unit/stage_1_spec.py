from typing import Any

from kallikrein import k, Expectation
from kallikrein.matchers import contain

from ribosome.test.integration.run import DispatchHelper
from ribosome.nvim.io import NvimIOState
from ribosome.plugin_state import PluginState

from amino import do, Just, Map
from amino.do import Do
from amino.test.spec import SpecBase
from amino.test import temp_dir, fixture_path

from chromatin import config

name = 'flagellum'


class Stage1Spec(SpecBase):
    '''
    create one virtualenv $one
    foo $foo
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
        helper = DispatchHelper.cons(config, 'core', vars=vars, responses=responses)
        r = helper.loop('chromatin:command:stage_1').unsafe(helper.vim)
        return k(r.data.venvs.k).must(contain(name))

    def foo(self) -> Expectation:
        dir = temp_dir('rplugin', 'venv')
        vars = dict(
            chromatin_rplugins=[dict(spec='foo')],
            chromatin_venv_dir=str(dir),
        )
        helper = DispatchHelper.cons(config, 'core', vars=vars)
        helper1 = helper.copy(state=helper.state.copy())
        @do(NvimIOState[PluginState, None])
        def run() -> Do:
            yield helper1.loop()
        return k(1) == 1

__all__ = ('Stage1Spec',)
