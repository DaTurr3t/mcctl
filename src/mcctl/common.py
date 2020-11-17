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

from socket import error as sock_error
from mcstatus import MinecraftServer
from mcctl import web, storage, service, config, proc


def create(instance: str, source: str, memory: str, properties: list, literal_url: bool = False, start: bool = False):
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
            config.set_properties(instance_path / "jvm-env", {"MEM": memory})
        if start:
            service.set_status(instance, "enable")
            service.set_status(instance, "start")

        started = "and started " if start else ""
        print(f"Configured {started}with Version '{version}'.")

    else:
        print("How can you not agree that tacos are tasty?!?")
        storage.remove(instance, confirm=False)


def get_instance_list(filter_str: str = ''):
    """Print a list of all instances.

    Output a table of all instances with their respective Name, Server Version String, Status and persistence.

    Keyword Arguments:
        filter_str (str): Filter the list by instance name. (default: {''})
    """
    base_path = storage.get_instance_path(bare=True)
    server_paths = base_path.iterdir()
    servers = [x.name for x in server_paths]

    template = "%-12s %-20s %-16s %-10s %-10s"
    title = template % (
        "Name", "Server Version", "Player Count", "Status", "Persistent")

    print(title)
    for name in servers:
        if filter_str in name:
            cfg = config.get_properties(base_path / name / "server.properties")
            port = int(cfg.get("server-port"))

            try:
                server = MinecraftServer('localhost', port)
                status = server.status()
                online = status.players.online
                proto = status.version.protocol
                version = status.version.name
            except (ConnectionError, sock_error):
                online = 0
                proto = -1
                version = "n/a"

            if service.is_active(name):
                if proto > -1:
                    run_status = "Active"
                else:
                    run_status = "Starting"
            else:
                run_status = "Inactive"

            contents = template % (
                name, version,
                f"{online}/{cfg.get('max-players')}",
                run_status, service.is_enabled(name))
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
        status = server.status()
        proto = status.version.protocol
    except (ConnectionError, sock_error):
        return False

    return proto > -1


def mc_ls(what: str, filter_str: str = ''):
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
        get_instance_list(filter_str)
    else:
        raise ValueError(f"Cannot List '{what}'.")


def rename(instance: str, new_name: str):
    """Rename a server instance.

    A server instance is renamed. The server has to be stopped and disabled, so no invalid service links can occur.

    Arguments:
        instance (str): Current name of the Instance.
        new_name (str): New name of the Instance.
    """
    if (service.is_enabled(instance) or service.is_active(instance)):
        raise OSError("The server is still persistent and/or running.")
    server_path = storage.get_instance_path(instance)
    server_path.rename(server_path.parent / new_name)


def update(instance: str, source: str, literal_url: bool = False, restart: bool = False):
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
    if service.is_active(instance) and restart:
        service.notified_set_status(
            instance, "restart", f"Updating to Version {version}")
    else:
        additions = " Manual restart required."
    print(f"Update successful.{additions}")


def configure(instance: str, edit_paths: list, properties: list, editor: str, restart: bool = False):
    """Edits configurations, restarts the server if forced, and swaps in the new configurations.

    Args:
        instance (str): The Instance ID.
        edit_paths (list): The Paths to be edited interactively with the specified Editor.
        properties (list): The Properties to be changed in the server.properties File.
        editor (str): A Path to an Editor Binary.
        force (bool, optional): Stops the server, applies changes and starts it again when set to true.
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

    do_restart = service.is_active(instance) and restart and len(paths) > 0
    if do_restart:
        service.notified_set_status(
            instance, "stop", "Reconfiguring and restarting Server.")

    for pair in list(paths.items()):
        storage.move(*pair[::-1])

    if restart:
        service.set_status(instance, "start")
