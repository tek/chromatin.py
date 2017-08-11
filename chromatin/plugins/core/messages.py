from ribosome.machine import message

AddPlugin = message('AddPlugin', 'spec')
ShowPlugins = message('ShowPlugins')
StageI = message('StageI')

__all__ = ('AddPlugin', 'ShowPlugins', 'StageI')
