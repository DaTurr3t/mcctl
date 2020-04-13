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

from pathlib import Path


def propertiesToDict(propertyList: list) -> dict:
    """Convert an array of properties to a dict

    Takes a list of strings in "KEY=VALUE" form, and remodels it into a dict.
    Comments are removed from the File.

    Arguments:
        propertyList {list} -- The list to convert

    Raises:
        ValueError: Raised if a property is missing the "="-sign.

    Returns:
        dict -- A dict with all properties from the property list.
    """

    propertyDict = {}
    for line in propertyList:
        line = line.rstrip()
        if not line.startswith("#"):
            try:
                key, value = line.split("=", 1)
                propertyDict[key] = value
            except:
                raise ValueError(
                    "Unable to set Property '{}'".format(line))
    return propertyDict


def getProperties(filePath: Path) -> dict:
    """Create a dict from a property file

    Takes a the contents of a file line by line in "KEY=VALUE" form, and remodels it into a dict.

    Arguments:
        filePath {Path} -- The path of the input file.

    Returns:
        dict -- A dict with all properties from the specified file.
    """

    with open(filePath, "r") as configFile:
        config = propertiesToDict(list(configFile))
    return config


def setProperties(filePath: Path, properties: dict):
    """Write a configuration file from dict

    The properties is written into the specified file in "KEY=VALUE" form.

    Arguments:
        filePath {Path} -- The path of the output file.
        properties {dict} -- A dict with properties.
    """

    if not filePath.exists():
        filePath.touch()
    with open(filePath, "r+") as configFile:
        oldConfig = propertiesToDict(list(configFile))
        oldConfig.update(properties)

        newConfig = []
        for key, value in oldConfig.items():
            newConfig.append("{0}={1}".format(key, value))
        configFile.seek(0)
        configFile.write('\n'.join(newConfig) + '\n')
        configFile.truncate()


def acceptEula(instancePath: Path) -> bool:
    """Prints and modufies EULA according to user input

    The EULA will be displayed to Console and a dialog will ask the user to accept.

    Arguments:
        instancePath {Path} -- path to the instance.

    Returns:
        bool -- returns if the EULA was accepted.
    """

    filePath = instancePath / "eula.txt"
    assert filePath.exists(), "EULA not found"
    with open(filePath, "r+") as eula:
        contents = []
        for line in eula:
            if line.startswith("#"):
                contents.append(line)
                print(line.rstrip().lstrip("#"))
            else:
                ans = input(
                    "Enter [true] to accept the EULA or [false] to abort: ")
                while not ans.lower() in ["true", "false"]:
                    ans = input("Please Type 'true' or 'false': ")
                accepted = ans.lower() == "true"
                if accepted:
                    contents.append(line.replace("eula=false", "eula=true"))
                    eula.seek(0)
                    eula.writelines(contents)
                    eula.truncate()
                return accepted
