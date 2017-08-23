from ribosome.machine import message, json_message

StageI = message('StageI')
StageII = message('StageII')
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
Activate = message('Activate', 'name', varargs='plugins')
Activated = message('Activated', 'venv')
UpdatePlugins = message('UpdatePlugins', varargs='plugins')
Reboot = message('Reboot', 'venv')

__all__ = ('StageI', 'AddPlugin', 'ShowPlugins', 'SetupPlugins', 'SetupVenvs', 'InstallMissing', 'AddVenv',
           'IsInstalled', 'Installed', 'Updated', 'Activate', 'Activated', 'StageII', 'PostSetup', 'UpdatePlugins',
           'Reboot')
