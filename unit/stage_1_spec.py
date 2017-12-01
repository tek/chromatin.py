from kallikrein import k, Expectation
from kallikrein.matchers import contain

from ribosome.test.integration.run import DispatchHelper
from ribosome.nvim.io import NvimIOState
from ribosome.plugin_state import PluginState

from amino import do
from amino.do import Do
from amino.test.spec import SpecBase
from amino.test import temp_dir

from chromatin import config


class Stage1Spec(SpecBase):
    '''
    create one virtualenv $one
    '''

    def one(self) -> Expectation:
        dir = temp_dir('rplugin', 'venv')
        vars = dict(
            chromatin_rplugins=[dict(spec='foo')],
            chromatin_venv_dir=str(dir),
        )
        helper = DispatchHelper.cons(config, 'core', vars=vars)
        @do(NvimIOState[PluginState, None])
        def run() -> Do:
            yield helper.loop('chromatin:command:stage_1')
        r = run().unsafe(helper.vim)
        return k(r.data.venvs.k).must(contain('foo'))

__all__ = ('Stage1Spec',)
