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


def updated_plugin(name: str) -> str:
    return f'updated plugin \'{name}\''

__all__ = ('xdg_cache_home', 'xdg_cache_home_env_var', 'create_venv_dir_error', 'installed_plugin',
           'updated_plugin', 'no_plugins_match_for_activation', 'no_plugins_match_for_deactivation')
