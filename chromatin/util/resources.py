from amino import Path, List, _
from amino.options import EnvOption
from amino.util.string import plural_s

from chromatin.model.rplugin import Rplugin

xdg_cache_home = EnvOption('XDG_CACHE_HOME')


def create_venv_dir_error(dir: Path) -> str:
    return f'could not create venv dir `{dir}`'


def no_plugins_match_for_update(names: List[str]) -> str:
    return f'no plugins match for update: {names.join_comma}'


def no_plugins_match_for_activation(names: List[str]) -> str:
    return f'no plugins match for activation: {names.join_comma}'


def no_plugins_match_for_deactivation(names: List[str]) -> str:
    return f'no plugins match for deactivation: {names.join_comma}'


def plugins_install_failed(names: List[str]) -> str:
    return f'failed to install rplugins: {names.join_comma}'


def handled_plugins(action: str, names: List[str]) -> str:
    return f'{action} plugin{plural_s(names)}: {names.join_comma}'


def installed_plugins(names: List[str]) -> str:
    return handled_plugins('installed', names)


def installed_plugin(name: str) -> str:
    return installed_plugins(List(name))


def updated_plugins(names: List[str]) -> str:
    return handled_plugins('updated', names)


def updated_plugin(name: str) -> str:
    return updated_plugins(List(name))


def already_active(names: List[str]) -> str:
    return f'plugin{plural_s(names)} already active: {names.join_comma}'


def show_plugins(venv_dir: Path, plugins: List[Rplugin]) -> str:
    venv_dir_msg = f'virtualenv dir: {venv_dir}'
    plugins_desc = plugins.map(_.spec).cons('Configured plugins:')
    return plugins_desc.cons(venv_dir_msg).join_lines


__all__ = ('xdg_cache_home', 'create_venv_dir_error', 'installed_plugin', 'updated_plugin',
           'no_plugins_match_for_activation', 'no_plugins_match_for_deactivation', 'plugins_install_failed',
           'installed_plugins', 'updated_plugins', 'already_active', 'show_plugins_message')
