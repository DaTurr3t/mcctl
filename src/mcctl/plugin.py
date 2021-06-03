#!/bin/env python3

# mcctl: A Minecraft Server Management Utility written in Python
# Copyright (C) 2021 Matthias Cotting

# This file is part of mcctl.

# mcctl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# mcctl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with mcctl. If not, see <http://www.gnu.org/licenses/>.


import difflib
import tempfile as tmpf
from pathlib import Path
from . import storage, web, visuals, common


def install(instance: str, sources: list, restart: bool = False, autoupgrade: str = "ask") -> None:
    """Install a list of archived or bare plugins on a server.

    Args:
        instance (str): The name of the instance.
        sources (list): A list of zip and jar Files/URLs which contain or are Plugins.
        autoupgrade (bool): Uninstall similarly named Plugins but ask first.
        restart (bool, optional): Restart the Server after Installation. Defaults to False.

    Raises:
        FileNotFoundError: If a Plugin File or Archive is not found.
        ValueError: Unsupported File Format/No sources specified.
    """
    instance_path = storage.get_instance_path(instance)
    plugin_dest = storage.get_plugin_path(instance)

    if not instance_path.is_dir():
        raise FileNotFoundError(f"Instance not found: {instance_path}.")
    if not plugin_dest.is_dir():
        raise FileNotFoundError("This Instance does not support plugins.")
    if not sources:
        raise ValueError("No Plugins specified to install.")

    unique_files = set(sources)
    with tmpf.TemporaryDirectory() as tmp_dir:
        for source in unique_files:
            if web.is_url(source):
                print(f"Downloading '{source}'...")
                downloaded = web.download(source, tmp_dir)
                unique_files.add(downloaded)
                unique_files.discard(source)
        installed = set()
        plugin_sources = (Path(x) for x in unique_files)
        for plugin_source in plugin_sources:
            print(f"Installing '{plugin_source.name}'...")
            if plugin_source.suffix == ".zip":
                installed_files = storage.install_compressed_plugin(
                    plugin_source, plugin_dest)
                installed.update(installed_files)

            elif plugin_source.suffix == ".jar":
                installed_file = storage.install_bare_plugin(
                    plugin_source, plugin_dest)
                installed.add(installed_file)

            else:
                raise ValueError(f"'{plugin_source}' is not a .zip- or .jar-File.")
    state_note = "Manual restart/reload required."
    if restart:
        state_note = "Restarted Server."
        common.notified_set_status(instance, "restart", "Installing Plugins.")
    print(f"Installed {', '.join(installed)}. {state_note}")
    if autoupgrade:
        auto_uninstall(instance, installed, False)


def uninstall(instance: str, plugins: list, restart: bool = False, force: bool = False) -> set:
    """Uninstall a Plugin from a Server Instance.

    Uninstall all plugins which contain an entry from {plugins} in their filename.

    Args:
        instance (str): The name of the instance.
        plugins (list): A list of plugin search terms, case insensitive.
        force (bool, optional): Don't prompt and proceed with deletion. Defaults to False.

    Raises:
        FileNotFoundError: If the instance does not exist or does not support plugins.

    Returns:
        set: A collection of all uninstalled plugins.
    """
    instance_path = storage.get_instance_path(instance)
    plugin_path = storage.get_plugin_path(instance)
    if not instance_path.is_dir():
        raise FileNotFoundError(f"Instance not found: {instance_path}.")
    if not plugin_path.is_dir():
        raise FileNotFoundError("This Instance does not support plugins.")

    installed_names = (x.name for x in plugin_path.iterdir()
                       if x.suffix == ".jar")
    resolved_names = set()
    for plugin_search in plugins:
        resolved_names.update(x for x in installed_names
                              if plugin_search.lower() in x.lower())
    if len(resolved_names) > 0:
        print("The following plugins will be removed:")
        print(f"  {', '.join(resolved_names)}")
        if force or visuals.bool_selector("Is this ok?"):
            if restart:
                common.notified_set_status(instance, "stop", "Removing Plugins.")
            for plugin_name in resolved_names:
                rm_path = plugin_path / plugin_name
                rm_path.unlink()
            if restart:
                common.notified_set_status(instance, "start")
            print(f"Removed {', '.join(resolved_names)}")
            return resolved_names
    else:
        print("No plugins found to uninstall.")
    return set()


def auto_uninstall(instance: str, new_plugins: list, force: bool = False) -> set:
    """Automatically uninstall old/similar Versions of a Plugin based on its Name.

    Uninstall Plugins which are similar by name to remove old Versions. Installed Plugins are matched with
    a sequence matcher against the new ones. if the match is higher than 0.6, the plugin is considered
    an older Version and added to the uninstall list.

    Args:
        instance (str): The name of the instance.
        new_plugins (list): A list of newly installed plugin names.
        force (bool, optional): Remove matching Plugins without confirmation prompt. Defaults to False.

    Returns:
        set: A collection of all uninstalled plugins.
    """
    plugin_path = storage.get_plugin_path(instance)
    installed_names = {x.name for x in plugin_path.iterdir()
                       if x.suffix == ".jar"}
    old_installed = installed_names.difference(new_plugins)
    resolved_names = set()
    for plugin_name in new_plugins:
        resolved_names.update(difflib.get_close_matches(
            plugin_name, old_installed, 2))
    if len(resolved_names) > 0:
        print(
            "The following plugins seem to be old Versions of the Plugin(s) just installed:")
        print(f"  {', '.join(resolved_names)}")
        if force or visuals.bool_selector("Remove them?"):
            for plugin_name in resolved_names:
                rm_path = plugin_path / plugin_name
                rm_path.unlink()
            print(f"Automatically removed {', '.join(resolved_names)}")
            return resolved_names
    else:
        print("No similar plugins found to uninstall.")
    return set()


def get_plugins(instance: str) -> tuple:
    """Return a List of all Jar Plugin files of an Instance.

    Args:
        instance (str): The name of the instance.

    Raises:
        FileNotFoundError: If no plugin folder exists (likely means server does not support plugins).

    Returns:
        tuple: All Filenames of installed plugins.
    """
    plugin_path = storage.get_plugin_path(instance)
    if plugin_path.is_dir():
        plugins = [x.name for x in plugin_path.iterdir() if x.suffix == ".jar"]
    else:
        raise FileNotFoundError("Plugin Folder not found.")
    return plugins


def list_plugins(filter_str: str = '') -> None:
    """List all Servers which have plugins installed.

    Args:
        filter_str (str, optional): Simple line filter. Filter by Instance or plugin name. Defaults to ''.
    """
    base_path = storage.get_instance_path(bare=True)
    instance_paths = base_path.iterdir()

    template = "{:16} {:^14} {}"
    print(template.format("Instance", "Plugins", "Installed"))

    for instance_path in instance_paths:
        instance = instance_path.name
        try:
            plugins = get_plugins(instance)
        except FileNotFoundError:
            plugins = ()
        resolved = template.format(
            instance, ("supported" if plugins else "not supported"), ", ".join(plugins))
        if filter_str in resolved:
            print(resolved)
