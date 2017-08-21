from ribosome.machine import message, json_message

StageI = message('StageI')
AddPlugin = json_message('AddPlugin', 'spec')
ShowPlugins = message('ShowPlugins')
SetupPlugins = message('SetupPlugins')
SetupVenvs = message('SetupVenvs')
InstallMissing = message('InstallMissing')
AddVenv = message('AddVenv', 'venv')
Installed = message('Installed', 'venv')
ActivateAll = message('ActivateAll')
Activated = message('Activated', 'venv')

__all__ = ('StageI', 'AddPlugin', 'ShowPlugins', 'SetupPlugins', 'SetupVenvs', 'InstallMissing', 'AddVenv', 'Installed',
           'ActivateAll', 'Activated')
