# Chromatin

This **neovim** python remote plugin provides management for plugins written with [ribosome] and distributed over
**pypi**.

Each plugin is installed with `pip` into a separate virtualenv and loaded automatically, without the need for
`UpdateRemotePlugins`.

# Install

The plugin itself needs [ribosome] to be installed:

```
pip install ribosome
```

# Usage

## Declare
To add a plugin, call the command `Cram` from an `after/plugin` file:

```viml
Cram myo
Cram /home/tek/path/to/proteome { 'name': 'proteome' }
```

Any string that `pip` can understand will work, but the name has to be supplied in the options.

## Install

If the variable `g:chromatin_autostart` is unset or `1`, all plugins will be installed and activated after startup.
To manually trigger installation, execute `CrmSetupPlugins`.

## Activate

Each plugin gets its own plugin host, allowing differing library dependency versions.

In order to manually trigger loading the plugins, execute `CrmActivate [plugin_names]`.

## Update

The command `CrmUpdate [plugin_names]` runs `pip install --upgrade` for the specified or all plugins.

## Configure

After a plugin has been loaded, files in `{runtimepath}/chromatin/<plugin_name>/*.vim` are sourced to allow for
post-load configuration.

[ribosome]: https://github.com/tek/ribosome
