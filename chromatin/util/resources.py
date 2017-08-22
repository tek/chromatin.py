from amino import Path

xdg_cache_home_env_var = 'XDG_CACHE_HOME'


def create_venv_dir_error(dir: Path) -> str:
    return f'could not create venv dir `{dir}`'

__all__ = ('xdg_cache_home_env_var', 'create_venv_dir_error')
