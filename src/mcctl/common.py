#!/bin/env python3

# mcctl: A Minecraft Server Management Utility written in Python
# Copyright (C) 2020 Matthias Cotting

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

import codecs
from socket import error as sock_error
from mcstatus import MinecraftServer
from mcctl import web, storage, service, config, proc, visuals, CFGVARS


def create(instance: str, source: str, memory: str, properties: list, literal_url: bool = False, start: bool = False) -> None:
    """Create a new Minecraft Server Instance.

    Downloads the correct jar-file, configures the server and asks the user to accept the EULA.

    Arguments:
        instance (str): The Instance ID.
        source (str): The Type ID of the Minecraft Server Binary.
        memory (str): The Memory-String. Can be appended by K, M or G, to signal Kilo- Mega- or Gigabytes.
        properties (list): A list with Strings in the format of "KEY=VALUE".
        literal_url (bool): Determines if the TypeID is a literal URL. Default: False
        start (bool): Starts the Server directly if set to True. Default: False
    """
    instance_path = storage.get_instance_path(instance)
    if instance_path.exists():
        raise FileExistsError("Instance already exists.")

    storage.create_dirs(instance_path)

    jar_path_src, version = web.pull(source, literal_url)
    jar_path_dest = instance_path / "server.jar"
    storage.copy(jar_path_src, jar_path_dest)
    proc.pre_start(jar_path_dest)
    if config.accept_eula(instance_path):
        if properties:
            properties_dict = config.properties_to_dict(properties)
            config.set_properties(
                instance_path / "server.properties", properties_dict)
        if memory:
            env_path = instance_path / CFGVARS.get('system', 'env_file')
            config.set_properties(env_path, {"MEM": memory})
        if start:
            service.notified_set_status(instance, "start", persistent=True)

        started = "and started " if start else ""
        print(f"Configured {started}with Version '{version}'.")

    else:
        print("How can you not agree that tacos are tasty?!?")
        storage.remove(instance, force=True)


def list_instances(filter_str: str = '') -> None:
    """Print a list of all instances.

    Output a table of all instances with their respective Name, Server Version String, Status and persistence.

    Keyword Arguments:
        filter_str (str): Filter the list by instance name. (default: {''})
    """
    base_path = storage.get_instance_path(bare=True)
    server_paths = base_path.iterdir()
    servers = [x.name for x in server_paths]

    template = "{:16} {:20} {:16} {:10} {:10}"
    title = template.format("Name", "Server Version",
                            "Player Count", "Status", "Persistent")

    print(title)
    for name in servers:
        if filter_str in name:
            cfg = config.get_properties(base_path / name / "server.properties")
            port = int(cfg.get("server-port"))

            try:
                server = MinecraftServer('localhost', port)
                mc_status = server.status()
                online = mc_status.players.online
                proto = mc_status.version.protocol
                version = mc_status.version.name
            except (ConnectionError, sock_error):
                online = 0
                proto = -1
                version = "n/a"

            unit = service.get_unit(name)
            service_state = unit.Unit.ActiveState.decode()
            if proto > -1 and service_state == "active":
                run_status = "Starting"
            else:
                run_status = service_state.capitalize()

            contents = template.format(
                name, version, f"{online}/{cfg.get('max-players')}",
                run_status, str(service.is_enabled(name)))
            print(contents)


def is_ready(instance: str) -> bool:
    """Check if the Server is ready to serve connections/is fully started.

    Args:
        instance (str): The Instance ID.

    Returns:
        bool: True if the Server is ready to serve connections.
    """
    cfg = config.get_properties(
        storage.get_instance_path(instance) / "server.properties")
    port = int(cfg.get("server-port"))
    try:
        server = MinecraftServer('localhost', port)
        mc_status = server.status()
        proto = mc_status.version.protocol
    except (ConnectionError, sock_error):
        return False

    return proto > -1


def mc_ls(what: str, filter_str: str = '') -> None:
    """List things such as jars or instances.

    A Function to bundle all Listing Functions, invokes selected Function.

    Args:
        what (str): What to list (jars or instances)
        filter (str): Filter by Instance Name, type or version. (default: '')

    Raises:
        ValueError: Raised if "what" is invalid.
    """
    if what == 'jars':
        storage.get_jar_list(filter_str)
    elif what == 'instances':
        list_instances(filter_str)
    else:
        raise ValueError(f"Cannot List '{what}'.")


def rename(instance: str, new_name: str) -> None:
    """Rename a server instance.

    A server instance is renamed. The server has to be stopped and disabled, so no invalid service links can occur.

    Arguments:
        instance (str): Current name of the Instance.
        new_name (str): New name of the Instance.
    """
    unit = service.get_unit(instance)
    if (service.is_enabled(unit) or service.is_active(unit)):
        raise OSError("The server is still persistent and/or running.")
    server_path = storage.get_instance_path(instance)
    server_path.rename(server_path.parent / new_name)


def update(instance: str, source: str, literal_url: bool = False, restart: bool = False) -> None:
    """Change the Jar File of a server.

    Stops the Server if necessary, deletes the old Jar File and copies the new one, starts the Server again.

    Arguments:
        instance (str): The Instance ID.
        source (str): The Type ID or URL of the new minecraft server Jar.
        literal_url (bool): Determines if the TypeID is a literal URL. Default: False
        allow_restart (bool): Allows a Server restart if the Server is running. Default: False
    """
    jar_src, version = web.pull(source, literal_url)
    jar_dest = storage.get_instance_path(instance) / "server.jar"
    storage.copy(jar_src, jar_dest)

    additions = ''
    unit = service.get_unit(instance)
    if service.is_active(unit) and restart:
        service.notified_set_status(
            instance, "restart", f"Updating to Version {version}")
    else:
        additions = " Manual restart required."
    print(f"Update successful.{additions}")


def configure(instance: str, editor: str, properties: list = None, edit_paths: list = None, memory: str = None, restart: bool = False) -> None:
    """Edits configurations, restarts the server if forced, and swaps in the new configurations.

    Args:
        instance (str): The Instance ID.
        editor (str): A Path to an Editor Binary.
        properties (list): The Properties to be changed in the server.properties File.
        edit_paths (list): The Paths to be edited interactively with the specified Editor.
        memory (str): Update the Memory Allocation. Can be appended by K, M or G, to signal Kilo- Mega- or Gigabytes.
        restart (bool, optional): Stops the server, applies changes and starts it again when set to true.
        Defaults to False.
    """
    instance_path = storage.get_instance_path(instance)
    paths = {}

    if properties:
        properties_path = instance_path / "server.properties"
        tmp_path = storage.tmpcopy(properties_path)
        properties_dict = config.properties_to_dict(properties)
        config.set_properties(tmp_path, properties_dict)
        paths.update({properties_path: tmp_path})

    if memory:
        env_path = instance_path / CFGVARS.get('system', 'env_file')
        tmp_path = storage.tmpcopy(env_path)
        config.set_properties(tmp_path, {"MEM": memory})
        paths.update({env_path: tmp_path})

    if edit_paths:
        for file_path in edit_paths:
            # Check if a Temporary File of the Config already exists
            if file_path not in paths.keys():
                abspath = instance_path / file_path
                tmp_path = storage.tmpcopy(abspath)
                proc.edit(tmp_path, editor)
                if storage.get_file_hash(tmp_path) != storage.get_file_hash(abspath):
                    paths.update({abspath: tmp_path})
                else:
                    tmp_path.unlink()
            else:
                proc.edit(paths[file_path], editor)

    unit = service.get_unit(instance)
    do_restart = service.is_active(unit) and len(paths) > 0 and restart
    if do_restart:
        service.notified_set_status(
            instance, "stop", "Reconfiguring and restarting Server.")

    for dst, src in paths.items():
        storage.move(src, dst)

    if do_restart:
        service.notified_set_status(instance, "start")


def status(instance: str) -> None:
    """Show Status Information about a Service.

    Args:
        instance (str): The name of the instance.
    """
    instance_path = storage.get_instance_path(instance)
    if not instance_path.exists():
        raise FileNotFoundError("Instance Path not found.")

    properties = config.get_properties(
        instance_path / "server.properties")
    try:
        envinfo = config.get_properties(
            instance_path / CFGVARS.get('system', 'env_file'))
    except FileNotFoundError:
        envinfo = {}

    port = properties.get("server-port")
    server = MinecraftServer('localhost', int(port))
    mc_status = server.status()

    unit = service.get_unit(instance)
    state = unit.ActiveState.decode().capitalize()
    files = storage.get_child_paths(instance_path)
    total_size = sum(x.stat().st_size for x in files)

    cmdvars = {k: v for k, v in (x.decode().split("=")
                                 for x in unit.Service.Environment)}
    cmdvars.update(envinfo)
    cmd = " ".join(x.decode() for x in unit.Service.ExecStart[0][1])
    resolved_cmd = cmd.replace("${", "{").format(**cmdvars)

    info = {
        "MOTD": codecs.decode(properties.get("motd", "?"), "unicode-escape").replace("\\", ""),
        "Player Count": f"{mc_status.players.online}/{properties.get('max-players', '?')}",
        "Version": f"{mc_status.version.name} (protocol {mc_status.version.protocol})",
        "Server Port": port,
        "Size on Disk": visuals.get_fmtbytes(total_size),
        "Persistent": str(unit.UnitFileState.decode() == "enabled"),
        "Status": f"{state} ({unit.SubState.decode()})",
        "Process": f"({unit.Service.MainPID}) {resolved_cmd}",
        "Memory Usage": f"{visuals.get_fmtbytes(unit.Service.MemoryCurrent)} ({cmdvars.get('MEM')} for JVM)",
    }

    maxlen = len(max(info, key=len))
    print(f"--- [{state.upper()}] {unit.Unit.Description.decode()} ---")
    for key, val in info.items():
        print(f"{key:>{maxlen}}: {val}")
    print()


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
    cache_path = storage.get_home_path() / ".plugin_cache"

    if not instance_path.is_dir():
        raise FileNotFoundError("Instance not found.")
    if not plugin_dest.is_dir():
        raise FileNotFoundError("No Plugin Folder found.")

    unique_files = set(sources)
    storage.create_dirs(cache_path)
    for potential_url in unique_files:
        if web.is_url(potential_url):
            downloaded = web.download(potential_url, cache_path)
            unique_files.add(downloaded)
            unique_files.discard(potential_url)

    installed = []
    plugin_sources = (storage.Path(x) for x in unique_files)
    for plugin_source in plugin_sources:
        if plugin_source.suffix == ".zip":
            installed.extend(storage.install_compressed_plugin(
                plugin_source, plugin_dest))
        elif plugin_source.suffix == ".jar":
            installed.append(storage.install_bare_plugin(
                plugin_source, plugin_dest))
        else:
            raise ValueError(f"'{plugin_source}' is not '.zip' or '.jar'.")
    add = ". Manual restart/reload required."
    storage.remove_dirs(cache_path)
    if restart:
        add = "and restarted Server."
        service.notified_set_status(instance, "restart", "Installing Plugins.")
    print(f"Installed {', '.join(installed)}{add}")
