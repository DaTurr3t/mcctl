# mcctl: A Minecraft Server Management Utility written in Python
# Copyright (C) 2020 Matthias Cotting

# This file is part of mcctl.

# mcctl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# mcctl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY
# without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with mcctl.  If not, see < http: // www.gnu.org/licenses/>.

import subprocess as sp
import shlex


def attach(instance):
    cmd = shlex.split("runuser -l mcserver -c 'screen -r mc-{}'".format(instance))
    sp.run(cmd)
    pass


def exec(instance, command):
    cmd = shlex.split(
        "runuser -l mcserver -c 'screen -p 0 -S mc-{0} -X stuff \"{1}^M\"'".format(instance, command))
    sp.run(cmd)
    pass
