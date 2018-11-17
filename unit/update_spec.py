from kallikrein import k, Expectation
from kallikrein.matchers import contain

from ribosome.compute.output import Echo
from ribosome.nvim.io.state import NS
from ribosome.test.prog import request
from ribosome.test.unit import unit_test, update_data
from ribosome.data.plugin_state import PS

from test.base import rplugin_dir, single_venv_config, present_venv

from amino import Map, List, do, Do
from amino.test.spec import SpecBase
from amino.lenses.lens import lens

from chromatin.model.rplugin import ActiveRpluginMeta
from chromatin.util import resources

name = 'flagellum'
spec = rplugin_dir(name)
active_rplugin = ActiveRpluginMeta(name, 3, 1111)
rplugin, venv, conf = single_venv_config(name, spec, chromatin_rplugins=[dict(name=name, spec=spec)])


@do(NS[PS, Expectation])
def one_spec() -> Do:
    yield NS.lift(present_venv(name))
    yield update_data(
        rplugins=List(rplugin),
        venvs=List(name),
        active=List(active_rplugin),
        ready=List(name),
    )
    yield request('update', 'flagellum')
    log_buffer = yield NS.inspect(lambda a: a.data.log_buffer)
    return k(log_buffer).must(contain(Echo.info(resources.updated_plugin(rplugin.name))))


class UpdateSpec(SpecBase):
    '''
    update one plugin $one
    '''

    def one(self) -> Expectation:
        return unit_test(conf, one_spec)


__all__ = ('UpdateSpec',)
