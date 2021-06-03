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


from socket import error as sock_error
from mcstatus import MinecraftServer
from . import config, storage


def get_simple_status(server: MinecraftServer) -> dict:
    """Get a safe, displayable Status from a server.

    Args:
        server (MinecraftServer): A Minecraft Server Object

    Returns:
        dict: online count, proto and version info
    """
    try:
        mc_status = server.status()
        values = {
            "online": mc_status.players.online,
            "proto": mc_status.version.protocol,
            "version": mc_status.version.name
        }
    except (ConnectionError, sock_error):
        values = {
            "online": 0,
            "proto": -1,
            "version": "n/a"
        }
    return values


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
