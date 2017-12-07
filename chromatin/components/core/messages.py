# from ribosome.trans.message_base import Msg, json_pmessage, pmessage

# from chromatin.venv import Venv


# class ReadConf(Msg): pass


# class ShowPlugins(Msg): pass


# class SetupPlugins(Msg): pass


# class SetupVenvs(Msg): pass


# class PostSetup(Msg): pass


# class InstallMissing(Msg): pass

# AddPlugin = json_pmessage('AddPlugin', 'spec')


# class AddVenv(Msg, venv=Venv): pass


# class IsInstalled(Msg, venv=Venv): pass


# class Installed(Msg, venv=Venv): pass


# class Updated(Msg, venv=Venv): pass

# Activate = pmessage('Activate', varargs='plugins')
# Deactivate = pmessage('Deactivate', varargs='plugins')


# class Activated(Msg, venv=Venv): pass


# class Deactivated(Msg, venv=Venv): pass


# class AlreadyActive(Msg, venv=Venv): pass


# class ActivationComplete(Msg): pass


# class InitializationComplete(Msg): pass

# UpdatePlugins = pmessage('UpdatePlugins', varargs='plugins')
# Reboot = pmessage('Reboot', varargs='plugins')
# DefinedHandlers = pmessage('DefinedHandlers', 'venv', 'handlers')

# __all__ = ('ReadConf', 'AddPlugin', 'ShowPlugins', 'SetupPlugins', 'SetupVenvs', 'InstallMissing', 'AddVenv',
#            'IsInstalled', 'Installed', 'Updated', 'Activate', 'Deactivate', 'Activated', 'Deactivated', 'PostSetup',
#            'AlreadyActive', 'ActivationComplete', 'InitializationComplete', 'UpdatePlugins', 'Reboot',
#            'DefinedHandlers')
