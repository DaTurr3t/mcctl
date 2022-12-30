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

from pathlib import Path

from . import ENCODING


def properties_to_dict(property_list: list) -> dict:
    """Convert an array of properties to a dict.

    Takes a list of strings in "KEY=VALUE" form, and remodels it into a dict.
    Comments are removed from the File.

    Arguments:
        property_list (list): A list of strings to turn into properties.

    Raises:
        ValueError: Raised if a property is missing the "="-sign.

    Returns:
        dict: A dict with all properties from the property list.
    """
    property_dict = {}
    for line in property_list:
        if "=" in line:
            try:
                key, value = line.split("=", 1)
                property_dict[key] = value
            except KeyError:
                raise ValueError(f"Unable to set Property '{line}'") from None
    return property_dict


def get_properties(file_path: Path, encoding: str = "iso8859_1") -> dict:
    """Create a dict from a property file.

    Takes a the contents of a file line by line in "KEY=VALUE" form, and remodels it into a dict.

    Arguments:
        file_path (Path): The path of the input file.

    Keyword Arguments:
        encoding (str): The encoding of the properties File (Default: "iso8859_1").

    Returns:
        dict: A dict with all properties from the specified file.
    """
    with open(file_path, "r", encoding=encoding) as config_file:
        config = properties_to_dict(config_file.read().splitlines())
    return config


def set_properties(file_path: Path, properties: dict, encoding: str = "iso8859_1") -> None:
    """Write a server.properties file from dict.

    The properties are written into the specified file in "KEY=VALUE" form.

    Keyword Arguments:
        encoding (str): The encoding of the properties File (Default: "iso8859_1").

    Arguments:
        file_path (Path): The path of the output file.
        properties (dict): A dict with properties.
    """
    if not file_path.exists():
        file_path.touch()

    old_config = get_properties(file_path)
    old_config.update(properties)

    new_config = [f"{key}={value}\n" for key, value in old_config.items()]
    with open(file_path, "w", encoding=encoding) as config_file:
        config_file.writelines(new_config)


def accept_eula(instance_path: Path) -> bool:
    """Print and modify EULA according to user input.

    The EULA will be displayed to Console and a dialog will ask the user to accept.

    Arguments:
        instance_path (Path): path to the instance.

    Returns:
        bool: returns if the EULA was accepted.
    """
    accepted = False
    file_path = instance_path / "eula.txt"

    if not file_path.is_file():
        raise FileNotFoundError("EULA File not found.")
    with open(file_path, "r+", encoding=ENCODING) as eula:
        contents = []
        for line in eula:
            if line.startswith("#"):
                contents.append(line)
                print(line.rstrip().lstrip("#"))
            else:
                ans = input(
                    "Enter [true] to accept the EULA or [false] to abort: ")
                while not ans.lower() in ("true", "false"):
                    ans = input("Please Type 'true' or 'false': ")
                accepted = ans.lower() == "true"
                if accepted:
                    contents.append(line.replace("eula=false", "eula=true"))
                    eula.seek(0)
                    eula.writelines(contents)
                    eula.truncate()
    return accepted
