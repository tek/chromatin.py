from typing import Any

from kallikrein import k, Expectation
from kallikrein.matchers.maybe import be_just

from ribosome.test.integration.run import DispatchHelper
from ribosome.nvim.io import NS
from ribosome.plugin_state import PluginState
from ribosome.dispatch.data import DIO, GatherSubprocsDIO
from ribosome.dispatch.execute import execute_io
from ribosome.trans.action import TransResult, TransAction, Info, LogMessage
from ribosome.process import SubprocessResult
from ribosome.trans.send_message import transform_data_state

from amino import Just, Map, List, Nil, Right, Path, __
from amino.test.spec import SpecBase
from amino.test import temp_dir, fixture_path

from chromatin import config
from chromatin.model.rplugin import cons_rplugin, ActiveRpluginMeta
from chromatin.model.venv import Venv, VenvMeta
from chromatin.util import resources

from unit._support.log_buffer_env import LogBufferEnv

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
        active = ActiveRpluginMeta(name, channel, pid)
        venv = Venv(rplugin, VenvMeta(name, dir / name, Right(Path('/dev/null')), Right(Path('/dev/null'))))
        responses_strict = Map(
            {
                'jobstart': channel,
                'jobpid': pid,
                'FlagellumRpcHandlers': '[]',
                'silent FlagellumStage1': 0,
                'silent FlagellumStage2': 0,
                'silent FlagellumStage3': 0,
                'silent FlagellumStage4': 0,
            }
        )
        def responses(req: str) -> Any:
            return responses_strict.lift(req).o(Just(0))
        def x_io(dio: DIO) -> NS[PluginState, TransAction]:
            return (
                NS.pure(TransResult((List(SubprocessResult(0, Nil, Nil, venv)), Nil)))
                if isinstance(dio, GatherSubprocsDIO) else
                execute_io(dio)
            )
        helper0 = DispatchHelper.cons(config.copy(state_ctor=LogBufferEnv.cons), vars=vars, responses=responses,
                                      io_executor=x_io)
        data0 = helper0.state.data
        data = data0.copy(
            rplugins=List(rplugin),
            venvs=Map({name: venv.meta}),
            active=List(active),
            ready=List(name),
        )
        def logger(msg: LogMessage) -> NS[LogBufferEnv, None]:
            return transform_data_state(NS.modify(__.append1.log_buffer(msg)))
        helper = helper0.copy(
            state=helper0.state.copy(data=data, logger=Just(logger)),
        )
        r = helper.loop('chromatin:command:update', ('flagellum',)).unsafe(helper.vim)
        return k(r.data.log_buffer.head).must(be_just(Info(resources.updated_plugin(rplugin.name))))

__all__ = ('UpdateSpec',)
