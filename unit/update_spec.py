from kallikrein import k, Expectation
from kallikrein.matchers.maybe import be_just
from kallikrein.matchers import contain
from kallikrein.matchers.match_with import match_with

from ribosome.compute.output import Echo

from test.base import rplugin_dir, single_venv_data

from amino import Map, List
from amino.test.spec import SpecBase

from chromatin.model.rplugin import ActiveRpluginMeta
from chromatin.util import resources
from chromatin.config.state import ChromatinState

name = 'flagellum'
spec = rplugin_dir(name)
rplugin, venv, helper = single_venv_data(
    name,
    spec,
    chromatin_rplugins=[dict(name=name, spec=spec)],
)
active_rplugin = ActiveRpluginMeta(name, 3, 1111)
helper1 = helper.update_data(
    rplugins=List(rplugin),
    venvs=Map({name: venv.meta}),
    active=List(active_rplugin),
    ready=List(name),
)


def check(state: ChromatinState) -> Expectation:
    return k(state.data.log_buffer.head).must(be_just(Echo.info(resources.updated_plugin(rplugin.name))))


class UpdateSpec(SpecBase):
    '''
    update one plugin $one
    '''

    def one(self) -> Expectation:
        return helper1.k_s('command:update', 'flagellum').must(contain(match_with(check)))


__all__ = ('UpdateSpec',)
