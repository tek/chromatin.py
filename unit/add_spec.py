from typing import TypeVar

from kallikrein import k, Expectation
from kallikrein.matchers import contain

from test.base import rplugin_dir, single_venv_config, present_venv

from amino import Path, do, Do
from amino.test.spec import SpecBase

from ribosome.test.prog import request
from ribosome.nvim.io.state import NS
from ribosome.test.unit import unit_test
from ribosome.nvim.api.variable import variable_set_prefixed

from chromatin.model.rplugin import ActiveRpluginMeta
from chromatin.env import Env

name = 'flagellum'
hs_name = 'flagellum.hs'
A = TypeVar('A')
target = ActiveRpluginMeta(name, 3, 1111)


@do(NS[Env, Expectation])
def add_spec(spec: str) -> Do:
    yield NS.lift(present_venv(name))
    yield NS.lift(variable_set_prefixed('interpreter', '/usr/bin/python3.7'))
    yield NS.lift(variable_set_prefixed('debug_pythonpath', True))
    yield request('cram', spec, name=name)
    data = yield NS.inspect(lambda a: a.data)
    return k(data.venvs).must(contain(name)) & k(data.active).must(contain(target))


@do(NS[Env, Expectation])
def directory_spec(spec: str) -> Do:
    yield request('cram', spec, name='flagellum')
    active = yield NS.inspect(lambda a: a.data.active)
    return k(active).must(contain(target))


@do(NS[Env, Expectation])
def hs_directory_spec(spec: str) -> Do:
    yield request('cram', spec, name=name)
    active = yield NS.inspect(lambda a: a.data.active)
    return k(active).must(contain(target))


class AddSpec(SpecBase):
    '''
    add a plugin $add
    add a plugin from directory $directory
    add a haskell plugin from directory $hs_directory
    '''

    def add(self) -> Expectation:
        spec = rplugin_dir(name)
        rplugin, venv, conf = single_venv_config(name, spec)
        return unit_test(conf, add_spec, spec)

    def directory(self) -> Expectation:
        plugins_dir = rplugin_dir(name)
        plugin_dir = Path(plugins_dir) / name
        spec = f'dir:{plugin_dir}'
        rplugin, venv, conf = single_venv_config(name, spec)
        return unit_test(conf, directory_spec, spec)

    def hs_directory(self) -> Expectation:
        plugin_dir = rplugin_dir(hs_name)
        spec = f'hs_dir:{plugin_dir}'
        rplugin, venv, conf = single_venv_config(name, spec)
        return unit_test(conf, hs_directory_spec, spec)


__all__ = ('AddSpec',)
