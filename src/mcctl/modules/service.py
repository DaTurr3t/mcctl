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
from pathlib import Path
from modules import storage
import subprocess as sp
unitName = "mcserver@"


def isActive(instance):
    global unitName
    serviceInstance = unitName + instance
    testCmd = shlex.split("systemctl is-active {0}".format(serviceInstance))
    testOut = sp.run(testCmd, stdout=sp.PIPE, stderr=sp.PIPE)
    return testOut.returncode == 0


def isEnabled(instance):
    global unitName
    serviceInstance = unitName + instance
    testCmd = shlex.split("systemctl is-enabled {0}".format(serviceInstance))
    testOut = sp.run(testCmd, stdout=sp.PIPE, stderr=sp.PIPE)
    return testOut.returncode == 0


def setStatus(instance, action):
    global unitName
    serviceInstance = unitName + instance
    cmd = shlex.split("systemctl {0} {1}".format(action, serviceInstance))
    out = sp.run(cmd)
    assert out.returncode == 0, "Exit Code {0} for command '{1}')".format(
        out.returncode, instance)
    if action in ["start", "restart", "stop"]:
        time.sleep(1)
        assert isActive(instance) != (action == "stop"), "Command Failed! (Service Action '{0}' on {1} failed)".format(
            action, instance)


def getInstanceList(instance):
    basePath = storage.getHomePath() / "instances"
    serverPaths = basePath.iterdir()
    servers = [x.name for x in serverPaths]

    template = "%-15s%-20s%-12s%-12s"
    th = template % (
        "Name", "Server Type", "Status", "Persistent")
    contents = ""
    if instance == "all":
        for name in servers:
            contents += template % (
                name, "Server Jar",
                "Active" if isActive(name) else "Inactive",
                isEnabled(name)) + "\n"

    elif instance in servers:
        contents = template % (
            instance, "Server Jar",
            "Active" if isActive(instance) else "Inactive",
            isEnabled(instance)) + "\n"

    print(th)
    print(contents, end="")
