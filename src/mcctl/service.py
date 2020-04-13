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
from mcctl import storage, config
import subprocess as sp
from mcctl import status

unitName = "mcserver@"


def isActive(instance: str) -> bool:
    global unitName
    serviceInstance = unitName + instance
    testCmd = shlex.split("systemctl is-active {0}".format(serviceInstance))
    testOut = sp.run(testCmd, stdout=sp.PIPE, stderr=sp.PIPE)
    return testOut.returncode == 0


def isEnabled(instance: str) -> bool:
    global unitName
    serviceInstance = unitName + instance
    testCmd = shlex.split("systemctl is-enabled {0}".format(serviceInstance))
    testOut = sp.run(testCmd, stdout=sp.PIPE, stderr=sp.PIPE)
    return testOut.returncode == 0


def setStatus(instance: str, action: str):
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


def getInstanceList(filter: str = ''):
    basePath = storage.getHomePath() / "instances"
    serverPaths = basePath.iterdir()
    servers = [x.name for x in serverPaths]

    template = "%-15s%-20s%-12s%-12s"
    th = template % (
        "Name", "Server Version", "Status", "Persistent")
    
    print(th)
    for name in servers:
        if filter in name:
            cfg = config.getProperties(basePath / name / "server.properties")
            port = int(cfg["server-port"])
            ms = status.MineStat('localhost', port)

            version = ms.version if not ms.version is None else "N/A"
            runStatus = "Active" if isActive(name) else "Inactive"
            contents = template % (
                name, version,
                runStatus,
                isEnabled(name))
            print(contents)
