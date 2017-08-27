from ribosome.machine import message, json_message

Start = message('Start')
ReadConf = message('ReadConf')
AddPlugin = json_message('AddPlugin', 'spec')
ShowPlugins = message('ShowPlugins')
SetupPlugins = message('SetupPlugins')
SetupVenvs = message('SetupVenvs')
PostSetup = message('PostSetup')
InstallMissing = message('InstallMissing')
AddVenv = message('AddVenv', 'venv')
IsInstalled = message('Installed', 'venv')
Installed = message('Installed', 'venv')
Updated = message('Updated', 'venv')
Activate = message('Activate', varargs='plugins')
Activated = message('Activated', 'venv', 'channel')
AlreadyActive = message('AlreadyActive', 'venv')
UpdatePlugins = message('UpdatePlugins', varargs='plugins')
Reboot = message('Reboot', 'venv')

__all__ = ('ReadConf', 'Start', 'AddPlugin', 'ShowPlugins', 'SetupPlugins', 'SetupVenvs', 'InstallMissing',
           'AddVenv', 'IsInstalled', 'Installed', 'Updated', 'Activate', 'Activated', 'PostSetup', 'UpdatePlugins',
           'Reboot', 'AlreadyActive')
