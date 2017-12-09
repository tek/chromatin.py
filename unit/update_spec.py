from typing import Any

from kallikrein import k, Expectation
from kallikrein.matchers import contain
from kallikrein.matchers.typed import have_type

from ribosome.test.integration.run import DispatchHelper
from ribosome.nvim.io import NS
from ribosome.plugin_state import PluginState
from ribosome.dispatch.data import DIO, GatherSubprocsDIO
from ribosome.dispatch.execute import execute_io
from ribosome.trans.action import TransResult, TransAction
from ribosome.process import SubprocessResult
from ribosome.trans.messages import Info

from amino import Just, Map, List, Nil, Right, Path
from amino.test.spec import SpecBase
from amino.test import temp_dir, fixture_path

from chromatin import config
from chromatin.model.rplugin import Rplugin, cons_rplugin, ActiveRplugin
from chromatin.model.venv import Venv

name = 'flagellum'


class UpdateSpec(SpecBase):
    '''
    update one plugin $one
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
        channel = 3
        pid = 1111
        rplugin = cons_rplugin(name, self.spec)
        active = ActiveRplugin(rplugin, channel, pid)
        venv = Venv(rplugin, dir / name, Right(Path('/dev/null')), Right(Path('/dev/null')))
        responses_strict = Map(
            {
                'jobstart': channel,
                'jobpid': pid,
                'FlagellumRpcHandlers': [],
                'silent FlagellumStage1': 0,
                'silent FlagellumStage2': 0,
                'silent FlagellumStage3': 0,
                'silent FlagellumStage4': 0,
            }
        )
        def responses(req: str) -> Any:
            return (
                Just([])
                if req == 'FlagellumRpcHandlers' else
                responses_strict.lift(req).o(Just(0))
            )
        def x_io(dio: DIO) -> NS[PluginState, TransAction]:
            return (
                NS.pure(TransResult((List(SubprocessResult(0, Nil, Nil, venv)), Nil)))
                if isinstance(dio, GatherSubprocsDIO) else
                execute_io(dio)
            )
        helper0 = DispatchHelper.cons(config, 'core', vars=vars, responses=responses, io_executor=x_io)
        data0 = helper0.state.data
        data = data0.copy(
            plugins=List(Rplugin.cons('flagellum', self.spec)),
            venvs=Map({name: venv}),
            active=List(active),
            ready=List(rplugin),
        )
        helper = helper0.copy(state=helper0.state.copy(data=data))
        r = helper.loop('chromatin:command:update', ('flagellum',)).unsafe(helper.vim)
        return k(r.message_log).must(contain(have_type(Info)))

__all__ = ('UpdateSpec',)
