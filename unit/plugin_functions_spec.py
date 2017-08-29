from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right
from kallikrein.matchers.length import have_length

from chromatin.plugins.core.main import PluginFunctions

from amino import Just, _, List

from ribosome.test.spec import MockNvimFacade
from chromatin.env import Env

plugins = List(dict(spec='flagellum'), dict(spec='cilia'))
vars = dict(chromatin_rplugins=plugins)
vim = MockNvimFacade('chromatin', vars)
env = Env(vim_facade=Just(vim))


class PluginFunctionsSpec:
    '''read config from vim variables $read_conf
    '''

    @property
    def funcs(self) -> PluginFunctions:
        return PluginFunctions()

    def read_conf(self) -> Expectation:
        r = self.funcs.read_conf()
        return k(r.run_s(env) / _.plugins).must(be_right(have_length(2)))

__all__ = ('PluginFunctionsSpec',)
