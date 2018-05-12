import shutil
from typing import Any, Tuple, Callable

from amino import Path, do, IO, Do, Maybe, Nothing, List, Just, Map, Boolean

from kallikrein import Expectation, k
from kallikrein.matchers.typed import have_type
from kallikrein.matcher import Matcher
from kallikrein.matchers import contain
from kallikrein.matchers.end_with import end_with
from amino.test.path import base_dir
from amino.test import fixture_path, temp_dir

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.command import nvim_command, nvim_command_output, nvim_sync_command
from ribosome.nvim.api.option import option_cat
from ribosome.nvim.api.variable import variable_set_prefixed, variable_raw
from ribosome.nvim.io.api import N
from ribosome.test.prog import request
from ribosome.test.config import TestConfig
from ribosome.nvim.io.state import NS
from ribosome.test.integration.external import external_state_test
from ribosome.nvim.api.exists import wait_until_valid
from ribosome.test.integration.embed import plugin_test
from ribosome.test.klk.matchers.command import command_must_exist
from ribosome.test.klk.expectation import await_k

from chromatin.model.rplugin import Rplugin
from chromatin.model.venv import VenvExistent, Venv
from chromatin.rplugin import venv_exists, rplugin_ready, check_venv
from chromatin import chromatin_config

from test.base import simple_rplugin


venvs_path = base_dir().parent / 'temp' / 'venv'


def venv_path(name: str) -> Path:
    return venvs_path / name


@do(IO[None])
def clear_cache() -> Do:
    yield IO.delay(shutil.rmtree, str(venvs_path), ignore_errors=True)
    yield IO.delay(venvs_path.mkdir, parents=True, exist_ok=True)


def plug_exists(name: str, **kw: Any) -> NvimIO[Expectation]:
    cmd = f'{name}Test'
    return await_k(command_must_exist, cmd, **kw)


def venv_existent(base_dir: Path, timeout: float=10) -> Callable[[Rplugin], NvimIO[None]]:
    def check(rplugin: Rplugin) -> NvimIO[None]:
        return wait_until_valid(
            str(rplugin),
            lambda n: N.from_io(venv_exists(base_dir, rplugin)),
            timeout=timeout,
            interval=.5,
        )
    return check


def package_installed(base_dir: Path, timeout: float=20) -> Callable[[Rplugin], NvimIO[None]]:
    def check(rplugin: Rplugin) -> NvimIO[None]:
        return wait_until_valid(
            str(rplugin),
            lambda n: N.from_io(rplugin_ready(base_dir, rplugin)),
            timeout=timeout,
            interval=.5,
        )
    return check


@do(NvimIO[Venv])
def plugin_venv(base_dir: Path, rplugin: Rplugin) -> Do:
    yield venv_existent(base_dir)(rplugin)
    venv_status = yield N.from_io(check_venv(base_dir, rplugin))
    yield (
        N.pure(venv_status.venv)
        if isinstance(venv_status, VenvExistent) else
        N.error(f'venv for {rplugin} did not appear')
    )


@do(NvimIO[Path])
def setup_venv_dir(venv_dir: Maybe[Path] = Nothing) -> Do:
    rtp = fixture_path('rplugin', 'config', 'rtp')
    yield option_cat('runtimepath', List(rtp))
    dir = venv_dir | temp_dir('rplugin', 'venv')
    yield variable_set_prefixed('venv_dir', str(dir))
    return dir


@do(NvimIO[Rplugin])
def setup_one(name: str, venv_dir: Maybe[Path]=Nothing) -> Do:
    plugin = simple_rplugin(name, name)
    path = fixture_path('rplugin', name)
    yield nvim_command('Cram', str(path), name)
    return plugin


@do(NvimIO[Tuple[Path, Rplugin]])
def setup_one_with_venvs(name: str, venv_dir: Maybe[Path] = Nothing) -> Do:
    base_dir = yield setup_venv_dir(venv_dir)
    plugin = yield setup_one(name, venv_dir)
    return base_dir, plugin


@do(NvimIO[Tuple[Venv, Rplugin]])
def install_one(name: str, venv_dir: Maybe[Path]=Nothing) -> Do:
    base_dir, plugin = yield setup_one_with_venvs(name, venv_dir)
    yield nvim_command('CrmSetupPlugins')
    yield venv_existent(base_dir)(plugin)
    package_installed(base_dir, plugin)
    venv = yield plugin_venv(base_dir, plugin)
    return base_dir, venv, plugin


@do(NvimIO[Venv])
def activate_one(name: str, prefix: str) -> Do:
    base_dir, venv, plugin = yield install_one(name)
    yield nvim_command('CrmActivate')
    later(plug_exists(prefix))
    return venv


def setup_venv(venv: str) -> NvimIO[Rplugin]:
    return setup_one(venv, Just(venvs_path))


@do(NvimIO[None])
def setup_venvs(names: List[str]) -> Do:
    venvs = yield setup_venv_dir(Just(venvs_path))
    create = names.exists(lambda a: not venv_path(a).exists())
    if create:
        yield N.from_io(clear_cache())
    plugins = yield names.traverse(setup_venv, NvimIO)
    yield nvim_sync_command('CrmSetupPlugins')
    yield plugins.traverse(venv_existent(venvs, 30), NvimIO)
    yield plugins.traverse(package_installed(venvs), NvimIO)


vars = Map(
    chromatin_autostart=False,
    chromatin_autoreboot=False,
    chromatin_handle_crm=False,
    chromatin_debug_pythonpath=True,
    chromatin_venv_dir=str(venvs_path),
)
test_config = TestConfig.cons(chromatin_config, vars=vars)


@do(NvimIO[Expectation])
def run_venv_test(
        names: List[str],
        spec: Callable[..., NvimIO[Expectation]],
        *a: Any,
        **kw: Any,
) -> Do:
    yield setup_venvs(names)
    yield spec(*a, **kw)


def cached_venvs_test(
        names: List[str],
        spec: Callable[..., NvimIO[Expectation]],
        *a: Any,
        config: TestConfig=test_config,
        **kw: Any,
) -> Expectation:
    return plugin_test(config, run_venv_test, names, spec, *a, **kw)


@do(NvimIO[Expectation])
def log_matches(matcher: Matcher[List[str]]) -> Do:
    output = yield N.from_io(IO.file(test_config.log_file))
    return k(output).must(matcher)


def log_entry(line: str) -> NvimIO[Expectation]:
    return log_matches(contain(end_with(line)))


__all__ = ('cached_venvs_test', 'log_matches', 'log_entry',)
