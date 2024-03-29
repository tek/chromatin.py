from kallikrein import k, Expectation
from kallikrein.matchers import contain
from kallikrein.matchers.either import be_right
from kallikrein.matchers.typed import have_type
from kallikrein.matchers.comparison import eq

from amino import Path, _, do, Do
from amino.test.spec import SpecBase
from amino.test import temp_dir

from ribosome.nvim.io.state import NS
from ribosome.data.plugin_state import PS
from ribosome.test.prog import request
from ribosome.test.unit import unit_test

from chromatin.model.rplugin import ActiveRpluginMeta, DistRplugin

from test.base import rplugin_dir, single_venv_config, present_venv

name = 'flagellum'

spec = rplugin_dir(name)
active_rplugin = ActiveRpluginMeta(name, 3, 1111)
rplugin, venv, conf = single_venv_config(name, spec, chromatin_rplugins=[dict(name=name, spec=spec)])


@do(NS[PS, Expectation])
def one_spec() -> Do:
    yield NS.lift(present_venv(name))
    yield request('init')
    data = yield NS.inspect(lambda a: a.data)
    return k(data.venvs).must(contain(name)) & k(data.active).must(contain(active_rplugin))


@do(NS[PS, Expectation])
def crm_rplugin_spec() -> Do:
    temp_dir('rplugin', 'venv', name, 'lib', 'python3.7')
    yield request('init')
    data = yield NS.inspect(lambda a: a.data)
    rplugin = data.chromatin_rplugin.to_either('no chromatin rplugin')
    venv = data.chromatin_venv.to_either('no chromatin venv')
    return (
        k(rplugin).must(be_right(DistRplugin.cons('chromatin', 'chromatin'))) &
        k(venv).must(eq(rplugin / _.name))
    )


class InitSpec(SpecBase):
    '''
    create one virtualenv $one
    dogfood chromatin $crm_rplugin
    '''

    def one(self) -> Expectation:
        return unit_test(conf, one_spec)

    def crm_rplugin(self) -> Expectation:
        return unit_test(conf, crm_rplugin_spec)


__all__ = ('InitSpec',)
