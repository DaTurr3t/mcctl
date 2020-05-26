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
import subprocess as sp
from mcctl import settings, proc


UNIT_NAME = settings.CFG_DICT['systemd_service']


def is_active(instance: str) -> bool:
    """Test if an instance is running

    systemd is queried to determine if the service of the server is running.

    Arguments:
        instance {str} -- The name of the instance.

    Returns:
        bool -- true: Server running, false: Server inactive/dead
    """

    service_instance = UNIT_NAME + instance
    test_cmd = shlex.split("systemctl is-active {0}".format(service_instance))
    test_out = sp.run(test_cmd, stdout=sp.PIPE, stderr=sp.PIPE, check=False)
    return test_out.returncode == 0


def is_enabled(instance: str) -> bool:
    """Test if an instance is enabled

    systemd is queried to determine if the service of the server is flagged to start on system boot.

    Arguments:
        instance {str} -- The name of the instance.

    Returns:
        bool -- true: Server starts on system boot, false: Server stays inactive/dead
    """

    service_instance = UNIT_NAME + instance
    test_cmd = shlex.split("systemctl is-enabled {0}".format(service_instance))
    test_out = sp.run(test_cmd, stdout=sp.PIPE, stderr=sp.PIPE, check=False)
    return test_out.returncode == 0


def set_status(instance: str, action: str):
    """Apply a systemd action to a minecraft server service.

    systemd is called to start, stop, restart, enable or disable a service
    of the Unit mcserver@.service.

    Arguments:
        instance {str} -- The name of the instance.
        action {str} -- The systemd action to apply to the service.
            Can be "start", "restart", "stop", "enable", "disable".
    """

    assert action in ["start", "restart", "stop", "enable",
                      "disable"], "Invalid action '{}'".format(action)

    service_instance = UNIT_NAME + instance
    cmd = shlex.split("systemctl {0} {1}".format(action, service_instance))
    reset = proc.run_as(0, 0)
    out = sp.run(cmd, check=False)
    proc.run_as(*reset)

    assert out.returncode == 0, "Exit Code {0} for command '{1}'".format(
        out.returncode, instance)
    if action in ["start", "restart", "stop"]:
        time.sleep(1)
        assert is_active(instance) != (
            action == "stop"), "Command Failed! (Service Action '{0}' on '{1}' failed)".format(
                action, instance)


def notified_stop(instance: str, reason: str, persistent: bool = False, restart: bool = False):
    """Notifies the Players on the Server why a Shutdown is occuring.

    Arguments:
        instance {str} -- The name of the instance.
        reason {str} -- The Reason the Server is shut down.

    Keyword Arguments:
        persistent {bool} -- If True, the Server will not start after a Machine reboot (default: {False})
        restart {bool} -- IF True, persistent wil be ignored and the server wil be restarted (default: {False})
    """
    action = "restart" if restart else "stop"
    msgcol = "6" if restart else "4"
    if persistent and not restart:
        set_status(instance, "disable")

    reason_msg = "say §{0}{1}ing Server. Reason: {2}".format(
        msgcol, action.capitalize(), reason)
    proc.mc_exec(instance, reason_msg.split())
    set_status(instance, action)
