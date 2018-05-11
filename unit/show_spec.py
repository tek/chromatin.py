from kallikrein import k, Expectation
from kallikrein.matchers import contain

from ribosome.compute.output import Echo
from ribosome.nvim.io.state import NS
from ribosome.data.plugin_state import PS
from ribosome.test.unit import update_data, unit_test
from ribosome.test.prog import request

from tests.base import rplugin_dir, single_venv_config

from amino import List, do, Do
from amino.test.spec import SpecBase
from amino.test import temp_dir

from chromatin.util import resources

name = 'flagellum'
spec = rplugin_dir(name)
dir = temp_dir('rplugin', 'venv')
rplugin, venv, conf = single_venv_config(
    name,
    spec,
    chromatin_rplugins=[dict(name=name, spec=spec)],
    chromatin_venv_dir=str(dir),
)


@do(NS[PS, Expectation])
def one_spec() -> Do:
    yield update_data(rplugins=List(rplugin))
    yield request('show_plugins')
    log_buffer = yield NS.inspect(lambda a: a.data.log_buffer)
    return k(log_buffer).must(contain(Echo.info(resources.show_plugins(dir, List(rplugin)))))


class ShowSpec(SpecBase):
    '''
    show one plugin $one
    '''

    def one(self) -> Expectation:
        return unit_test(conf, one_spec)


__all__ = ('ShowSpec',)
