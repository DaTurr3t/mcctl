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


def properties_to_dict(property_list: list) -> dict:
    """Convert an array of properties to a dict

    Takes a list of strings in "KEY=VALUE" form, and remodels it into a dict.
    Comments are removed from the File.

    Arguments:
        property_list {list} -- The list to convert

    Raises:
        ValueError: Raised if a property is missing the "="-sign.

    Returns:
        dict -- A dict with all properties from the property list.
    """

    property_dict = {}
    for line in property_list:
        line = line.rstrip()
        if not line.startswith("#"):
            try:
                key, value = line.split("=", 1)
                property_dict[key] = value
            except:
                raise ValueError(
                    "Unable to set Property '{}'".format(line))
    return property_dict


def get_properties(file_path: Path) -> dict:
    """Create a dict from a property file

    Takes a the contents of a file line by line in "KEY=VALUE" form, and remodels it into a dict.

    Arguments:
        file_path {Path} -- The path of the input file.

    Returns:
        dict -- A dict with all properties from the specified file.
    """

    with open(file_path, "r") as config_file:
        config = properties_to_dict(list(config_file))
    return config


def set_properties(file_path: Path, properties: dict):
    """Write a configuration file from dict

    The properties is written into the specified file in "KEY=VALUE" form.

    Arguments:
        file_path {Path} -- The path of the output file.
        properties {dict} -- A dict with properties.
    """

    if not file_path.exists():
        file_path.touch()
    with open(file_path, "r+") as config_file:
        old_config = properties_to_dict(list(config_file))
        old_config.update(properties)

        new_config = []
        for key, value in old_config.items():
            new_config.append("{0}={1}".format(key, value))
        config_file.seek(0)
        config_file.write('\n'.join(new_config) + '\n')
        config_file.truncate()


def accept_eula(instance_path: Path) -> bool:
    """Prints and modufies EULA according to user input

    The EULA will be displayed to Console and a dialog will ask the user to accept.

    Arguments:
        instance_path {Path} -- path to the instance.

    Returns:
        bool -- returns if the EULA was accepted.
    """

    file_path = instance_path / "eula.txt"
    assert file_path.exists(), "EULA not found"
    with open(file_path, "r+") as eula:
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
