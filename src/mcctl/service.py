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

import time
import shlex
from pystemd.systemd1 import Unit, Manager
from mcctl import CFGVARS, proc


UNIT_NAME = CFGVARS.get('system', 'systemd_service')


def get_unit(instance: str) -> str:
    """Return the systemd Unit name of the Instance.

    Args:
        instance (str): The name of the instance.

    Returns:
        str: The systemd service Unit.
    """
    unit = Unit(f"{UNIT_NAME}@{instance}.service")
    unit.load()
    return unit


def is_active(unit: Unit) -> bool:
    """Test if an instance is running.

    systemd is queried to determine if the service of the server is running.

    Arguments:
        unit (Unit): A systemd Unit object, already loaded.

    Returns:
        bool: true: Server running, false: Server inactive/dead
    """
    return unit.Unit.ActiveState.decode() == 'active'


def is_enabled(unit: Unit) -> bool:
    """Test if an instance is enabled.

    systemd is queried to determine if the service of the server is flagged to start on system boot.

    Arguments:
        unit (Unit): A systemd Unit object, already loaded.

    Returns:
        bool: true: Server starts on system boot, false: Server stays inactive/dead
    """
    return unit.Unit.UnitFileState.decode() == 'enabled'


def set_status(unit: Unit, action: str) -> None:
    """Apply a systemd action to a minecraft server service.

    systemd is called to start, stop, restart, enable or disable a service
    of the Unit mcserver@.service.

    Arguments:
        unit (Unit): A systemd Unit object, already loaded.
        action (str): The systemd action to apply to the service.
            Can be "start", "restart", "stop".
    """
    if action not in ("start", "restart", "stop"):
        raise ValueError(f"Invalid action '{action}'")

    with proc.managed_run_as(0, 0):
        action_func = getattr(unit.Unit, action.capitalize())
        action_func("replace")

    state = None
    while state in ("deactivating", "activating", None):
        state = unit.Unit.ActiveState.decode()
        time.sleep(0.5)
    if action in ("start", "restart", "stop"):
        should_be_dead = (action == "stop")
        if is_active(unit) == should_be_dead:
            raise OSError(f"{action.capitalize()} failed! (Unit is {state}).")


def set_persistence(unit: Unit, enable: bool = True) -> None:
    """Set the Persistence of a systemd Unit.

    Args:
        unit (Unit): A systemd Unit object, already loaded.
        enable (bool, optional): Wether to enable or disable the Unit. Defaults to True.
    """
    with Manager() as mgr:
        if enable:
            link = mgr.Manager.EnableUnitFiles([unit.Unit.Id], False, True)[1]
            if link[0]:
                print(f"Linked Unit: '{link[0][1].decode()}'")
        else:
            link = mgr.Manager.DisableUnitFiles([unit.Unit.Id], False)
            if link[0]:
                print(f"Unlinked Unit: '{link[0][1].decode()}'")


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

    unit = get_unit(instance)
    if persistent and action != "restart":
        enable = (action == "start")
        set_persistence(unit, enable)

    if action in ("stop", "restart"):
        msgcol = "6" if action == "restart" else "4"
        msg = f"say §{msgcol}Server {action} pending"
        msg += f": {message}" if message else "."
        try:
            proc.mc_exec(instance, shlex.split(msg))
        except ConnectionError:
            pass
    set_status(unit, action)
