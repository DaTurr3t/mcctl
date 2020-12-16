import difflib
import tempfile as tmpf
from pathlib import Path
from mcctl import service, storage, web, visuals


def install(instance: str, sources: list, restart: bool = False) -> None:
    """Install a list of archived or bare plugins on a server.

    Args:
        instance (str): The name of the instance.
        sources (list): A list of zip and jar Files/URLs which contain or are Plugins.
        restart (bool, optional): Restart the Server after Installation. Defaults to False.

    Raises:
        FileNotFoundError: If a Plugin File or Archive is not found.
        ValueError: Unsupported File Format.
    """
    instance_path = storage.get_instance_path(instance)
    plugin_dest = instance_path / "plugins"

    if not instance_path.is_dir():
        raise FileNotFoundError(f"Instance not found: {instance_path}.")
    if not plugin_dest.is_dir():
        raise FileNotFoundError("This Instance does not support plugins.")

    unique_files = set(sources)
    with tmpf.TemporaryDirectory() as tmp_dir:
        for source in unique_files:
            if web.is_url(source):
                print(f"Downloading '{source}'")
                downloaded = web.download(source, tmp_dir)
                unique_files.add(downloaded)
                unique_files.discard(source)
        installed = set()
        plugin_sources = (Path(x) for x in unique_files)
        for plugin_source in plugin_sources:
            print(f"Installing {plugin_source.name}...")
            if plugin_source.suffix == ".zip":
                installed_files = storage.install_compressed_plugin(plugin_source, plugin_dest)
                installed.update(installed_files)
            elif plugin_source.suffix == ".jar":
                installed_file = storage.install_bare_plugin(plugin_source, plugin_dest)
                installed.add(installed_file)
            else:
                raise ValueError(f"'{plugin_source}' is not a .zip- or .jar-File.")
    restarted = ". Manual restart/reload required."
    if restart:
        restarted = " and restarted Server."
        service.notified_set_status(instance, "restart", "Installing Plugins.")
    print(f"Installed {', '.join(installed)}{restarted}")


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
    plugin_path = instance_path / "plugins"
    if not instance_path.is_dir():
        raise FileNotFoundError(f"Instance not found: {instance_path}.")
    if not plugin_path.is_dir():
        raise FileNotFoundError("This Instance does not support plugins.")

    installed_names = (x.name for x in plugin_path.iterdir() if x.suffix == ".jar")
    resolved_names = set()
    for plugin_search in plugins:
        resolved_names.update(x for x in installed_names if plugin_search.lower() in x.lower())
    if len(resolved_names) > 0:
        print("The following plugins will be removed:")
        print(f"  {', '.join(resolved_names)}")
        if force or visuals.bool_selector("Is this ok?"):
            if restart:
                service.notified_set_status(instance, "restart", "Removing Plugins.")
            for plugin_name in resolved_names:
                rm_path = plugin_path / plugin_name
                rm_path.unlink()
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
        new_plugins (list): A list of newly installed plugins.
        force (bool, optional): Remove matching Plugins without confirmation prompt. Defaults to False.

    Returns:
        set: A collection of all uninstalled plugins.
    """
    plugin_path = storage.get_instance_path(instance) / "plugins"
    installed_names = {x.name for x in plugin_path.iterdir() if x.suffix == ".jar"}
    old_installed = installed_names.difference(new_plugins)
    resolved_names = set()
    for plugin_name in new_plugins:
        resolved_names.update(difflib.get_close_matches(plugin_name, old_installed, 2))
    if len(resolved_names) > 0:
        print("The following plugins seem to be old Versions of the Plugin(s) just installed:")
        print(f"  {', '.join(resolved_names)}")
        if force or visuals.bool_selector("Remove them?"):
            for plugin_name in resolved_names:
                rm_path = plugin_path / plugin_name
                rm_path.unlink()
            print(f"Autoremoved {', '.join(resolved_names)}")
            return resolved_names
    else:
        print("No similar plugins found to uninstall.")
    return set()
