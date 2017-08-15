from ribosome.machine import message

StageI = message('StageI')
AddPlugin = message('AddPlugin', 'spec')
ShowPlugins = message('ShowPlugins')
SetupPlugins = message('SetupPlugins')
SetupVenvs = message('SetupVenvs')
InstallMissing = message('InstallMissing')
AddVenv = message('AddVenv', 'venv')
VenvJob = message('VenvJob', 'job')
Installed = message('Installed', 'venv')

__all__ = ('StageI', 'AddPlugin', 'ShowPlugins', 'SetupPlugins', 'SetupVenvs', 'InstallMissing', 'AddVenv', 'VenvJob',
           'Installed')
