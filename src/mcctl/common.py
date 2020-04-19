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

from mcctl import web, storage, service, config, proc, status


def create(instance: str, source: str, memory: str, properties: list, start: bool):
    """Creates a new Minecraft Server Instance.

    Downloads the correct jar-file, configures the server and asks the user to accept the EULA.

    Arguments:
        instance {str} -- The Instance ID.
        source {str} -- The Type ID of the Minecraft Server Binary.
        memory {str} -- The Memory-String. Can be appended by K, M or G, to signal Kilo- Mega- or Gigabytes.
        properties {list} -- A list with Strings in the format of "KEY=VALUE".
        start {bool} -- Starts the Server directly if set to True.
    """

    instance_path = storage.get_home_path() / "instances" / instance
    assert not instance_path.exists(), "Instance already exists"
    storage.create_dirs(instance_path)

    jar_path_src = web.pull(source)
    jar_path_dest = instance_path / "server.jar"
    storage.copy(jar_path_src, jar_path_dest)
    proc.pre_start(jar_path_dest)
    if config.accept_eula(instance_path):
        if not properties is None:
            properties_dict = config.properties_to_dict(properties)
            config.set_properties(
                instance_path / "server.properties", properties_dict)
        if not memory is None:
            config.set_properties(instance_path / "jvm-env", {"MEM": memory})
        if start:
            proc.run_as(0, 0)
            service.set_status(instance, "enable")
            service.set_status(instance, "start")
            print("Configured and started.")
    else:
        print("How can you not agree that tacos are tasty?!?")
        storage.remove(instance, confirm=False)


def get_instance_list(filter_str: str = ''):
    """Print a list of all instances

    Output a table of all instances with their respective Name, Server Version String, Status and persistence.

    Keyword Arguments:
        filter_str {str} -- Filter the list by instance name. (default: {''})
    """

    base_path = storage.get_home_path() / "instances"
    server_paths = base_path.iterdir()
    servers = [x.name for x in server_paths]

    template = "%-15s%-20s%-12s%-12s"
    title = template % (
        "Name", "Server Version", "Status", "Persistent")

    print(title)
    for name in servers:
        if filter_str in name:
            cfg = config.get_properties(base_path / name / "server.properties")
            port = int(cfg["server-port"])
            mc_ping = status.MineStat('localhost', port)

            version = mc_ping.version if not mc_ping.version is None else "n/a"
            run_status = "Active" if service.is_active(name) else "Inactive"
            contents = template % (
                name, version,
                run_status,
                service.is_enabled(name))
            print(contents)


def rename(instance: str, new_name: str):
    """Renames a server instance

    A server instance is renamed. The server has to be stopped and disabled, so no invalid service links can occur.

    Arguments:
        instance {str} -- Current name
        new_name {str} -- New name of the instance
    """

    assert not (service.is_enabled(instance) or service.is_active(
        instance)), "The server is still persistent and/or running"
    base_path = storage.get_home_path()
    server_path = base_path / "instances" / instance
    server_path.rename(server_path.parent / new_name)


def update(instance: str, new_type_id: str, literal_url: bool = False):
    """Change the Jar File of a server

    Stops the Server if necessary, deletes the old Jar File and copies the new one, starts the Server again.

    Arguments:
        instance {str} -- The Instance ID.
        new_type_id {str} -- The Type ID of the new minecraft server Jar.
    """

    running = service.is_active(instance)
    if running:
        service.set_status(instance, "stop")

    jar_src = web.pull(new_type_id, literal_url)
    jar_dest = storage.get_home_path() / "instances" / instance / "server.jar"
    storage.copy(jar_src, jar_dest)

    if running:

        service.set_status(instance, "start")
