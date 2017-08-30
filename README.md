# Chromatin

This **neovim** python remote plugin provides management for plugins written with [ribosome] and distributed over
**pypi**.

Each plugin is installed with `pip` into a separate virtualenv and loaded automatically, without the need for
`UpdateRemotePlugins`, allowing runtime reloading of the complete plugin package.

# Install

The plugin itself needs [ribosome] to be installed:

```
pip install ribosome
```

# Usage

## Declare
When starting, **chromatin** reads plugin configuration from `g:chromating_rplugins`:

```viml
let g:chromatin_rplugins = [
  \ {'name': 'myo' },
  \ { 'name': 'proteome', 'spec': '/home/tek/path/to/proteome' },
  \ ]
```

To add a plugin at runtime, use the command `Cram`:

```
Cram myo
Cram /home/tek/path/to/proteome { 'name': 'proteome' }
```

Any string that `pip` can understand will work as a spec, but the name has to be supplied in the options for nontrivial
requirements.

## Install

If the variable `g:chromatin_autostart` is unset or `1`, all plugins will be installed and activated on neovim startup
or after they have been added.

To manually trigger installation, execute `CrmSetupPlugins`.

Virtualenvs are stored in `g:chromatin_venv_dir`, defaulting to `~/.cache/chromatin/venvs`.

## Activate

Each plugin gets its own plugin host, allowing differing library dependency versions.

In order to manually trigger the activation of plugins, execute `CrmActivate [plugin_names]`.

## Update

The command `CrmUpdate [plugin_names]` runs `pip install --upgrade` for the specified or all plugins.

## Deactivate

Plugins hosts can be shut down with the command `CrmDeactivate [plugins]`, removing all request handlers. The command
`CrmReboot [plugins]` combines deactivating and reactivating plugins, allowing plugins to be updated at runtime.

By default, plugins are rebooted after an update unless the variable `g:chromatin_autoreboot` is set to `0`.

## Configure

After a plugin has been loaded, files matching `{runtimepath}/chromatin/<plugin_name>/*.vim` are sourced to allow for
post-load configuration.

[ribosome]: https://github.com/tek/ribosome
