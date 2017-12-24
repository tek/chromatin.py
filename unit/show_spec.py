from kallikrein import k, Expectation
from kallikrein.matchers.maybe import be_just

from ribosome.test.integration.run import DispatchHelper
from ribosome.trans.action import LogMessage, Info
from ribosome.nvim.io import NS
from ribosome.trans.send_message import transform_data_state

from amino import List, Just, __
from amino.test.spec import SpecBase
from amino.test import temp_dir, fixture_path

from chromatin.model.rplugin import Rplugin
from chromatin import config
from chromatin.util import resources

from unit._support.log_buffer_env import LogBufferEnv

name = 'flagellum'


class ShowSpec(SpecBase):
    '''
    show one plugin $one
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
        rplugin = Rplugin.cons(name, self.spec)
        plugin = Rplugin.cons('flagellum', self.spec)
        helper0 = DispatchHelper.cons(config.copy(state_ctor=LogBufferEnv.cons), vars=vars)
        data0 = helper0.state.data
        data = data0.copy(rplugins=List(rplugin))
        def logger(msg: LogMessage) -> NS[LogBufferEnv, None]:
            return transform_data_state(NS.modify(__.append1.log_buffer(msg)))
        helper = helper0.copy(
            state=helper0.state.copy(data=data, logger=Just(logger)),
        )
        r = helper.loop('chromatin:command:show_plugins').unsafe(helper.vim)
        return k(r.data.log_buffer.head).must(be_just(Info(resources.show_plugins(dir, List(plugin)))))

__all__ = ('ShowSpec',)
