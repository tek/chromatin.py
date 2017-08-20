from ribosome.machine import message, json_message

StageI = message('StageI')
AddPlugin = json_message('AddPlugin', 'spec')
ShowPlugins = message('ShowPlugins')
SetupPlugins = message('SetupPlugins')
SetupVenvs = message('SetupVenvs')
InstallMissing = message('InstallMissing')
AddVenv = message('AddVenv', 'venv')
VenvJob = message('VenvJob', 'job')
Installed = message('Installed', 'venv')
ActivateAll = message('ActivateAll')
EnvVenvJob = message('EnvVenvJob', 'job')
Activated = message('Activated', 'venv')
PluginJob = message('PluginJob', 'job')

__all__ = ('StageI', 'AddPlugin', 'ShowPlugins', 'SetupPlugins', 'SetupVenvs', 'InstallMissing', 'AddVenv', 'VenvJob',
           'Installed', 'ActivateAll', 'EnvVenvJob', 'Activated', 'PluginJob')
