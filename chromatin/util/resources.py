from amino import Path, List
from amino.options import EnvOption

xdg_cache_home = EnvOption('XDG_CACHE_HOME')


def create_venv_dir_error(dir: Path) -> str:
    return f'could not create venv dir `{dir}`'


def no_plugins_match_for_update(names: List[str]) -> str:
    return f'no plugins match for update: {names.join_comma}'


def no_plugins_match_for_activation(names: List[str]) -> str:
    return f'no plugins match for activation: {names.join_comma}'


def no_plugins_match_for_deactivation(names: List[str]) -> str:
    return f'no plugins match for deactivation: {names.join_comma}'


def installed_plugin(name: str) -> str:
    return f'installed plugin \'{name}\''


def plugins_install_failed(names: List[str]) -> str:
    return f'failed to install rplugins: {names.join_comma}'


def installed_plugins(names: List[str]) -> str:
    return f'installed plugins {names.join_comma}'


def updated_plugin(name: str) -> str:
    return f'updated plugin \'{name}\''


def updated_plugins(names: List[str]) -> str:
    return f'updated plugins {names.join_comma}'

__all__ = ('xdg_cache_home', 'create_venv_dir_error', 'installed_plugin', 'updated_plugin',
           'no_plugins_match_for_activation', 'no_plugins_match_for_deactivation', 'plugins_install_failed',
           'installed_plugins', 'updated_plugins')
