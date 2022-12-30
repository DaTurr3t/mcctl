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

import codecs
import json
import shlex

from mcstatus import MinecraftServer

from . import (ENCODING, config, plugin, proc, service, status, storage,
               visuals, web)
from .__config__ import CFGVARS


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
    storage.symlink(jar_path_src, jar_path_dest)
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
            notified_set_status(instance, "start", persistent=True)

        started = " and started" if start else ""
        print(f"Configured{started} '{instance}' with Version '{version}'.")

    else:
        print("How can you not agree that tacos are tasty?!?")
        raise ValueError("EULA was not accepted.")


def get_online_state(unit: service.Unit, protocol_version: int) -> str:
    """Return a status which takes startup into account.

    Return a status which takes startup into account. "starting" if the Unit is
    running but the server does not respond, or just the Unit substate otherwise.

    Args:
        unit (Unit): A Unit Object
        protocol_version (int): The Minecraft Server Status Protocol Version

    Returns:
        str: The State of the Server.
    """
    state = unit.SubState.decode()
    if state == "running" and protocol_version < 0:
        state = "starting"
    return state


def collect_server_data(instance: str) -> dict:
    """Collect Data about the server and return it as a dict.

    Args:
        instance (str): The instance of which the data should be collected.

    Returns:
        dict: A dict containing various Information about the server.
    """
    instance_path = storage.get_instance_path(instance)
    if not instance_path.exists():
        raise FileNotFoundError(f"Instance not found: {instance_path}.")

    properties = config.get_properties(
        instance_path / "server.properties")
    try:
        envinfo = config.get_properties(
            instance_path / CFGVARS.get('system', 'env_file'))
    except FileNotFoundError:
        envinfo = None

    port = properties.get("server-port")
    server = MinecraftServer('localhost', int(port))
    status_info = status.get_simple_status(server)

    files = storage.get_child_paths(instance_path)
    total_size = sum(x.stat().st_size for x in files)

    unit = service.get_unit(instance)
    state = get_online_state(unit, status_info.get("proto"))

    cmdvars = {k: v for k, v in (x.decode().split("=") for x in unit.Service.Environment)}
    if envinfo:
        envinfo_keys = envinfo.keys()
        for k in cmdvars.keys():
            if k in envinfo_keys:
                cmdvars[k] = envinfo[k]
    cmd = " ".join(x.decode() for x in unit.Service.ExecStart[0][1])
    resolved_cmd = cmd.replace("${", "{").format(**cmdvars)

    jar_path = instance_path / cmdvars.get("JARFILE", "server.jar")
    resolved_jar_path = storage.get_real_abspath(jar_path)
    type_id = None
    if resolved_jar_path != jar_path:
        type_id = storage.get_type_id(resolved_jar_path)

    try:
        with open(instance_path / "whitelist.json", encoding=ENCODING) as wlist_hnd:
            whitelist = json.load(wlist_hnd)
    except FileNotFoundError:
        whitelist = None

    try:
        plugins = plugin.get_plugins(instance)
    except FileNotFoundError:
        plugins = None

    data = {
        "instance_name": instance,
        "instance_path": str(instance_path),
        "total_file_size": total_size,
        "status": {
            "players_online": status_info.get('online'),
            "players_max": properties.get('max-players', '?'),
            "protocol_name": status_info.get('proto'),
            "protocol_version": status_info.get('version'),
        },
        "service": {
            "description": unit.Unit.Description.decode(),
            "unit_file_state": unit.UnitFileState.decode(),
            "state": state,
            "main_pid": unit.Service.MainPID,
            "start_command": resolved_cmd,
            "memory_usage": unit.Service.MemoryCurrent,
            "env": cmdvars,
        },
        "type_id": type_id,
        "config": {
            "server.properties": properties,
            "whitelist": whitelist,
            "env_file": envinfo
        },
        "plugins": plugins,
    }

    return data


def list_instances(filter_str: str = '') -> None:
    """Print a list of all instances.

    Output a table of all instances with their respective Name, Server Version String, Status and persistence.

    Keyword Arguments:
        filter_str (str): Filter the list by instance name. (default: {''})
    """
    base_path = storage.get_instance_path(bare=True)
    server_paths = base_path.iterdir()
    servers = [x.name for x in server_paths if x.glob("server.properties")]

    name_col_width = str(len(max(servers, key=len)) + 1)
    template = "{:" + name_col_width + "} {:<6} {:20} {:14} {:10} {:10}"
    title = template.format(
        "Name", "Port", "Server Version",
        "Player Count", "Status", "Persistent"
    )

    print(title)
    for name in servers:
        if filter_str in name:
            cfg = config.get_properties(base_path / name / "server.properties")
            port = int(cfg.get("server-port"))
            server = MinecraftServer('localhost', port)
            status_info = status.get_simple_status(server)

            unit = service.get_unit(name)
            state = get_online_state(unit, status_info.get("proto"))

            player_ratio = f"{status_info.get('online')}/{cfg.get('max-players')}"
            contents = template.format(
                name, port, status_info.get("version"), player_ratio,
                state.capitalize(), str(service.is_enabled(unit)))
            print(contents)


def mc_ls(what: str, filter_str: str = '') -> None:
    """List things such as jars or instances.

    A Function to bundle all Listing Functions, invokes selected Function.

    Args:
        what (str): What to list (jars, instances or plugins)
        filter (str): Filter by Instance Name, type or version. (default: '')

    Raises:
        ValueError: Raised if "what" is invalid.
    """
    ls_types = {
        "instances": list_instances,
        "jars": storage.list_jars,
        "plugins": plugin.list_plugins
    }

    func = ls_types.get(what)
    if func is None:
        raise LookupError(f"Cannot List '{what}'.")
    func(filter_str)


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
    storage.symlink(jar_src, jar_dest)

    additions = ''
    unit = service.get_unit(instance)
    if service.is_active(unit) and restart:
        notified_set_status(instance, "restart", f"Updating to Version {version}")
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
    if not any((properties, edit_paths, memory)):
        raise ValueError("No properties or files to edit specified.")

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
        path_keys = paths.keys()
        for file_path in edit_paths:
            # Check if a Temporary File of the Config already exists
            if file_path not in path_keys:
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
        notified_set_status(instance, "stop", "Reconfiguring and restarting Server.")

    for dst, src in paths.items():
        storage.move(src, dst)

    if do_restart:
        notified_set_status(instance, "start")


def mc_status(instance: str) -> None:
    """Show Status Information about a Service.

    Args:
        instance (str): The name of the instance.
    """
    data = collect_server_data(instance)
    properties = data["config"].get("server.properties")
    status_info = data["status"]
    service_info = data["service"]
    state = service_info.get('state')
    env = service_info.get('env')

    info = {
        "MOTD": codecs.decode(properties.get("motd", "?"), "unicode-escape").replace("\\", ""),
        "Player Count": f"{status_info.get('players_online')}/{properties.get('max-players', '?')}",
        "Version": f"{status_info.get('protocol_version')} (protocol {status_info.get('protocol_name')})",
        "Server Port": properties.get("server-port", "?"),
        "Size on Disk": visuals.get_fmtbytes(data.get("total_file_size")),
        "Persistent": str(service_info.get('unit_file_state') == "enabled"),
        "Status": f"{state.capitalize()}",
        "Process": f"({service_info.get('main_pid')}) {service_info.get('start_command')}",
        "Memory Usage": f"{visuals.get_fmtbytes(service_info.get('memory_usage'))} ({env.get('MEM')} for JVM)",
    }

    maxlen = len(max(info.keys(), key=len))
    print(f"--- [{state.upper()}] {service_info.get('description')} ---")
    for key, val in info.items():
        print(f"{key:>{maxlen}}: {val}")
    print()


def notified_set_status(instance: str, action: str, message: str = '', persistent: bool = False) -> None:
    """Notifies the Players on the Server if applicable and sets the Service Status.

    Arguments:
        instance (str): The name of the instance.
        action (str): The systemd action to apply to the service. Can be "start", "restart", "stop".

    Keyword Arguments:
        message (str): A message relayed to Server Chat, e.g. reason the Server is shutting down.
        persistent (bool): If True, the Server will not start after a Machine reboot (default: {False})
        restart (bool): If True, persistent wil be ignored and the server wil be restarted (default: {False})
    """
    if action not in ("start", "restart", "stop"):
        raise ValueError(f"Invalid action '{action}'")

    unit = service.get_unit(instance)
    if persistent and action != "restart":
        enable = (action == "start")
        service.set_persistence(unit, enable)

    if action in ("stop", "restart"):
        msgcol = "6" if action == "restart" else "4"
        msg = f"say §{msgcol}Server {action} pending"
        msg += f": {message}" if message else "."
        try:
            proc.mc_exec(instance, shlex.split(msg))
        except ConnectionError:
            pass
    service.set_status(unit, action)


def inspect(instance: str) -> None:
    """Print JSON-Formatted information about the Server.

    Args:
        instance (str): The instance name.
    """
    data = collect_server_data(instance)
    print(json.dumps(data, indent=4))
