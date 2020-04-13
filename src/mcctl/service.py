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
from pathlib import Path
from mcctl import config, settings
import subprocess as sp

unitName = settings.cfgDict['systemd_service']


def isActive(instance: str) -> bool:
    """Test if an instance is running

    systemd is queried to determine if the service of the server is running.

    Arguments:
        instance {str} -- The name of the instance.

    Returns:
        bool -- true: Server running, false: Server inactive/dead
    """

    serviceInstance = unitName + instance
    testCmd = shlex.split("systemctl is-active {0}".format(serviceInstance))
    testOut = sp.run(testCmd, stdout=sp.PIPE, stderr=sp.PIPE)
    return testOut.returncode == 0


def isEnabled(instance: str) -> bool:
    """Test if an instance is enabled

    systemd is queried to determine if the service of the server is flagged to start on system boot.

    Arguments:
        instance {str} -- The name of the instance.

    Returns:
        bool -- true: Server starts on system boot, false: Server stays inactive/dead
    """

    serviceInstance = unitName + instance
    testCmd = shlex.split("systemctl is-enabled {0}".format(serviceInstance))
    testOut = sp.run(testCmd, stdout=sp.PIPE, stderr=sp.PIPE)
    return testOut.returncode == 0


def setStatus(instance: str, action: str):
    """Apply a systemd action to a minecraft server service.

    systemd is called to start, stop, restart, enable or disable a service of the Unit mcserver@.service.

    Arguments:
        instance {str} -- The name of the instance.
        action {str} -- The systemd action to apply to the service. Can be ["start", "restart", "stop", "enable", "disable"].
    """

    assert action in ["start", "restart", "stop", "enable",
                      "disable"], "Invalid action '{}'".format(action)
    serviceInstance = unitName + instance
    cmd = shlex.split("systemctl {0} {1}".format(action, serviceInstance))
    out = sp.run(cmd)
    assert out.returncode == 0, "Exit Code {0} for command '{1}')".format(
        out.returncode, instance)
    if action in ["start", "restart", "stop"]:
        time.sleep(1)
        assert isActive(instance) != (action == "stop"), "Command Failed! (Service Action '{0}' on '{1}' failed)".format(
            action, instance)
