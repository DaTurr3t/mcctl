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

from configparser import ConfigParser
from pathlib import Path

PARSER = ConfigParser()

CFGPATH = Path("/etc/mcctl.conf")

PARSER['settings'] = {
    'systemd_service': 'mcserver@', 'server_user': 'mcserver'}

# Overwrite default Values
if PARSER.read(CFGPATH) == []:
    try:
        with open(CFGPATH, 'w') as configfile:
            PARSER.write(configfile)
    except PermissionError:
        pass

CFG_DICT = dict(PARSER.items('settings'))

del PARSER, CFGPATH
