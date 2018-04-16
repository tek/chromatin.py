from typing import TypeVar

from kallikrein import k, Expectation
from kallikrein.matchers import contain
from kallikrein.matchers.match_with import match_with

from test.base import single_venv_helper, rplugin_dir

from amino import Path
from amino.test.spec import SpecBase

from ribosome.test.klk import kn

from chromatin.model.rplugin import ActiveRpluginMeta
from chromatin.config.state import ChromatinState

name = 'flagellum'
A = TypeVar('A')


# TODO kallikrein: make `match_with` work with `MultiExpectation`
class AddSpec(SpecBase):
    '''
    add a plugin $add
    add a plugin from directory $directory
    '''

    def add(self) -> Expectation:
        spec = rplugin_dir(name)
        helper = single_venv_helper(name, spec)
        def check(state: ChromatinState) -> Expectation:
            return (
                # k(state.data.venvs.k).must(contain(name)) &
                k(state.data.active).must(contain(ActiveRpluginMeta(name, 3, 1111)))
            )
        return helper.k_s('command:cram', spec, name).must(contain(match_with(check)))

    def directory(self) -> Expectation:
        plugins_dir = rplugin_dir(name)
        plugin_dir = Path(plugins_dir) / name
        spec = f'dir:{plugin_dir}'
        helper = single_venv_helper(name, spec)
        def check(state: ChromatinState) -> Expectation:
            return k(state.data.active).must(contain(ActiveRpluginMeta(name, 3, 1111)))
        return helper.k_s('command:cram', spec, 'flagellum').must(contain(match_with(check)))


__all__ = ('AddSpec',)
