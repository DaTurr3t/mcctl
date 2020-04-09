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

import subprocess as sp
import shlex
import time
from modules.storage import getHomePath
from modules.service import isActive


def attach(instance):
    cmd = shlex.split(
        "runuser -l mcserver -c 'screen -r mc-{}'".format(instance))
    sp.run(cmd)

def exec(instance, command, timeout=0.5):
    if not isActive(instance):
        raise Exception("The Server is not running ({})".format(instance))

    logPath = getHomePath() / "instances" / instance / "logs/latest.log"

    oldCount = 0
    lineCount = sum(1 for line in open(logPath))

    cmd = shlex.split(
        "runuser -l mcserver -c 'screen -p 0 -S mc-{0} -X stuff \"{1}^M\"'".format(instance, command))
    sp.run(cmd)

    while lineCount > oldCount:
        time.sleep(timeout)
        with open("{0}/{1}".format(dir, logPath)) as log:
            for i, line in enumerate(log):
                if i >= lineCount:
                    print(line.rstrip())
        oldCount = lineCount
        lineCount = i + 1