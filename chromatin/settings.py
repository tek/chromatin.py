from amino import Path, Try, Right, Either, do, Nil
from amino.do import Do
from amino.boolean import true, false

from ribosome.config import PluginSettings
from ribosome.config.settings import bool_setting, path_setting, list_setting

from chromatin.util.resources import xdg_cache_home, create_venv_dir_error

handle_crm_help = '''When updating plugins, chromatin can also update itself. To take effect, neovim has to be
restarted.
'''
venv_dir_help = '''Chromatin stores installed plugins in separate virtualenvs located in subdirectories of this setting.
'''
rplugin_help = '''The remote plugins managed by chromatin can be configured as a list of dictionaries of the form:
{
    'name': 'title',
    'spec': 'title==0.1.1',
}
`spec` can be any specifier that `pip` understands. If omitted, `name` is used.
'''
autostart_help = '''When set, chromatin will commence installation and activation of plugins on start.
'''
debug_pythonpath_help = '''When set, rplugins will bei started with the outer python env, effectively keeping the
$PYTHONPATH env var as it is in neovim.
'''
autoreboot_help = '''When set, plugins will be de- and reactivated after being updated.
'''


@do(Either[str, Path])
def default_venv_dir() -> Do:
    xdg_cache_path = xdg_cache_home.value / Path | (Path.home() / '.cache')
    venv_dir = xdg_cache_path / 'chromatin' / 'venvs'
    yield Try(venv_dir.mkdir, parents=True, exist_ok=True).lmap(lambda a: create_venv_dir_error(venv_dir))
    yield Right(venv_dir)


class CrmSettings(PluginSettings):

    def __init__(self) -> None:
        super().__init__('chromatin')
        self.handle_crm = bool_setting('handle_crm', 'update chromatin', handle_crm_help, True, Right(true))
        self.venv_dir = path_setting('venv_dir', 'virtualenv base directory', venv_dir_help, True, default_venv_dir())
        self.rplugins = list_setting('rplugins', 'rplugin config', rplugin_help, True, Right(Nil))
        self.autostart = bool_setting('autostart', 'autostart plugins', autostart_help, True, Right(true))
        self.debug_pythonpath = bool_setting('debug_pythonpath', 'pass through $PYTHONPATH', debug_pythonpath_help,
                                             True, Right(false))
        self.autoreboot = bool_setting('autoreboot', 'autoreboot plugins', autoreboot_help, True, Right(true))


__all__ = ('CrmSettings',)