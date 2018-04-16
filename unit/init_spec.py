from kallikrein import k, Expectation
from kallikrein.matchers import contain
from kallikrein.matchers.either import be_right
from kallikrein.matchers.typed import have_type
from kallikrein.matchers.comparison import eq
from kallikrein.matchers.match_with import match_with

from ribosome.test.integration.run import RequestHelper

from amino import Path, _
from amino.test.spec import SpecBase

from chromatin.model.rplugin import ActiveRpluginMeta, VenvRplugin
from chromatin.config.state import ChromatinState
from chromatin.config.config import chromatin_config

from test.base import rplugin_dir, single_venv_helper

name = 'flagellum'

spec = rplugin_dir(name)
helper = single_venv_helper(
    name,
    spec,
    chromatin_rplugins=[dict(name=name, spec=spec)],
)
active_rplugin = ActiveRpluginMeta(name, 3, 1111)


def check_venv(state: ChromatinState) -> Expectation:
    return k(state.data.venvs.k).must(contain(name))


def check_active_venv(state: ChromatinState) -> Expectation:
    return k(state.data.active).must(contain(active_rplugin))


class InitSpec(SpecBase):
    '''
    create one virtualenv $one
    dogfood chromatin $crm_rplugin
    '''

    def one(self) -> Expectation:
        return helper.k(helper.run_s, 'command:init').must(
            contain(match_with(check_venv)) &
            contain(match_with(check_active_venv))
        )

    def crm_rplugin(self) -> Expectation:
        helper = RequestHelper.strict(chromatin_config)
        r = helper.run_s('command:init').unsafe(helper.vim)
        rplugin = r.data.chromatin_rplugin.to_either('no chromatin rplugin')
        venv = r.data.chromatin_venv.to_either('no chromatin venv')
        return (
            k(rplugin).must(be_right(VenvRplugin('chromatin', 'chromatin'))) &
            k(venv // _.meta.python_executable).must(be_right(have_type(Path))) &
            k(venv / _.meta.rplugin).must(eq(rplugin / _.name))
        )


__all__ = ('InitSpec',)
