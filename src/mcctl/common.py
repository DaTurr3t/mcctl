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

from mcctl import web, storage, config, proc

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
