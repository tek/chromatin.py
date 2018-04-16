from kallikrein import k, Expectation
from kallikrein.matchers.maybe import be_just
from kallikrein.matchers import contain
from kallikrein.matchers.match_with import match_with

from ribosome.test.integration.run import RequestHelper
from ribosome.compute.output import Echo

from test.base import buffering_logger, rplugin_dir

from amino import List, Map
from amino.test.spec import SpecBase
from amino.test import temp_dir, fixture_path
from amino.lenses.lens import lens

from chromatin.model.rplugin import Rplugin
from chromatin.util import resources
from chromatin.config.config import chromatin_config
from chromatin.config.state import ChromatinState

from unit._support.log_buffer_env import LogBufferEnv

name = 'flagellum'
spec = rplugin_dir(name)
dir = temp_dir('rplugin', 'venv')
vars = Map(
    chromatin_rplugins=[dict(name=name, spec=spec)],
    chromatin_venv_dir=str(dir),
)
rplugin = Rplugin.cons(name, spec)
plugin = Rplugin.cons('flagellum', spec)
helper = RequestHelper.strict(lens.basic.state_ctor.set(LogBufferEnv.cons)(chromatin_config), vars=vars,
                              logger=buffering_logger).update_data(rplugins=List(rplugin))


def check(state: ChromatinState) -> Expectation:
    return k(state.data.log_buffer.head).must(be_just(Echo.info(resources.show_plugins(dir, List(plugin)))))


class ShowSpec(SpecBase):
    '''
    show one plugin $one
    '''

    @property
    def spec(self) -> str:
        return str(fixture_path('rplugin', name))

    def one(self) -> Expectation:
        return helper.k_s('command:show_plugins').must(contain(match_with(check)))


__all__ = ('ShowSpec',)
