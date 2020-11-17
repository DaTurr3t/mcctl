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
# along with mcctl. If not, see <http:// www.gnu.org/licenses/>.

import shlex
import time
import subprocess as sproc
from mcctl import CFGVARS, proc


UNIT_NAME = CFGVARS.get('system', 'systemd_service')


def is_active(instance: str) -> bool:
    """Test if an instance is running.

    systemd is queried to determine if the service of the server is running.

    Arguments:
        instance (str): The name of the instance.

    Returns:
        bool: true: Server running, false: Server inactive/dead
    """
    service_instance = "@".join((UNIT_NAME, instance))
    test_cmd = shlex.split(f"systemctl is-active {service_instance}")
    test_out = sproc.run(test_cmd, stdout=sproc.PIPE,
                         stderr=sproc.PIPE, check=False)
    return test_out.returncode == 0


def is_enabled(instance: str) -> bool:
    """Test if an instance is enabled.

    systemd is queried to determine if the service of the server is flagged to start on system boot.

    Arguments:
        instance (str): The name of the instance.

    Returns:
        bool: true: Server starts on system boot, false: Server stays inactive/dead
    """
    service_instance = "@".join((UNIT_NAME, instance))
    test_cmd = shlex.split(f"systemctl is-enabled {service_instance}")
    test_out = sproc.run(test_cmd, stdout=sproc.PIPE,
                         stderr=sproc.PIPE, check=False)
    return test_out.returncode == 0


def set_status(instance: str, action: str):
    """Apply a systemd action to a minecraft server service.

    systemd is called to start, stop, restart, enable or disable a service
    of the Unit mcserver@.service.

    Arguments:
        instance (str): The name of the instance.
        action (str): The systemd action to apply to the service.
            Can be "start", "restart", "stop", "enable", "disable".
    """
    allowed = ("start", "restart", "stop", "enable", "disable")
    assert action in allowed, f"Invalid action '{action}'"

    service_instance = "@".join((UNIT_NAME, instance))
    cmd = shlex.split(f"systemctl {action} {service_instance}")
    with proc.managed_run_as(0, 0):
        sproc.run(cmd, check=True)
    if action in ("start", "restart", "stop"):
        time.sleep(1)
        if is_active(instance) == (action == "stop"):
            raise OSError(f"Command Failed! ({action} of '{instance}' failed).")


def notified_set_status(instance: str, action: str, message: str = '', persistent: bool = False):
    """Notifies the Players on the Server if applicable and sets the Service Status.

    Arguments:
        instance (str): The name of the instance.
        action (str): The systemd action to apply to the service. Can be "start", "restart", "stop".

    Keyword Arguments:
        message (str): A message relayed to Server Chat, e.g. reason the Server is shutting down.
        persistent (bool): If True, the Server will not start after a Machine reboot (default: {False})
        restart (bool): If True, persistent wil be ignored and the server wil be restarted (default: {False})
    """
    allowed = ("start", "restart", "stop")
    assert action in allowed, f"Invalid action '{action}'"

    if persistent and action != "restart":
        persistent_action = {"start": "enable", "stop": "disable"}
        set_status(instance, persistent_action.get(action))

    if action in ("stop", "restart"):
        msgcol = "6" if action == "restart" else "4"
        msg = f"say §{msgcol}Server {action} pending"
        msg += f": {message}" if message else "."
        try:
            proc.mc_exec(instance, shlex.split(msg))
        except ConnectionError:
            pass
    set_status(instance, action)
