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


def create(instance: str, source: str, memory: str, properties: list):
    """Creates a new Minecraft Server Instance.

    Downloads the correct jar-file, configures the server and asks the user to accept the EULA.

    Arguments:
        instance {str} -- The Instance ID.
        source {str} -- The Type ID of the Minecraft Server Binary.
        memory {str} -- The Memory-String. Can be appended by K, M or G, to signal Kilo- Mega- or Gigabytes.
        properties {list} -- A list with Strings in the format of "KEY=VALUE".
    """

    instancePath = storage.getHomePath() / "instances" / instance
    assert not instancePath.exists(), "Instance already exists"
    storage.createDirs(instancePath)

    jarPathSrc = web.pull(source)
    jarPathDest = instancePath / "server.jar"
    storage.copy(jarPathSrc, jarPathDest)
    proc.preStart(jarPathDest)
    if config.acceptEula(instancePath):
        if not properties is None:
            propertiesDict = config.propertiesToDict(properties)
            config.setProperties(
                instancePath / "server.properties", propertiesDict)
        if not memory is None:
            config.setProperties(instancePath / "jvm-env", {"MEM": memory})
        print("Configured and ready to start.")
    else:
        print("How can you not agree that tacos are tasty?!?")
        storage.remove(instance, confirm=False)


def getInstanceList(filter: str = ''):
    """Print a list of all instances

    Output a table of all instances with their respective Name, Server Version String, Status and persistence.

    Keyword Arguments:
        filter {str} -- Filter the list by instance name. (default: {''})
    """

    basePath = storage.getHomePath() / "instances"
    serverPaths = basePath.iterdir()
    servers = [x.name for x in serverPaths]

    template = "%-15s%-20s%-12s%-12s"
    th = template % (
        "Name", "Server Version", "Status", "Persistent")

    print(th)
    for name in servers:
        if filter in name:
            cfg = config.getProperties(basePath / name / "server.properties")
            port = int(cfg["server-port"])
            ms = status.MineStat('localhost', port)

            version = ms.version if not ms.version is None else "n/a"
            runStatus = "Active" if service.isActive(name) else "Inactive"
            contents = template % (
                name, version,
                runStatus,
                service.isEnabled(name))
            print(contents)


def rename(instance: str, newName: str):
    """Renames a server instance

    A server instance is renamed. The server has to be stopped and disabled, so no invalid service links can occur.

    Arguments:
        instance {str} -- Current name
        newName {str} -- New name of the instance
    """

    assert not (service.isEnabled(instance) or service.isActive(
        instance)), "The server is still persistent and/or running"
    basePath = storage.getHomePath()
    serverPath = basePath / "instances" / instance
    serverPath.rename(serverPath.parent / newName)
