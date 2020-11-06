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

CFGVARS = ConfigParser()

GLOBALCFG = Path("/etc/mcctl.conf")
LOCALCFG = Path("~/.local/mcctl.conf")

DEFAULTS = {
    'systemd_service': 'mcserver@',
    'server_user': 'mcserver',
    'default_editor': '/usr/bin/vi',
    'default_shell': '/bin/bash'
}
CFGVARS['settings'] = DEFAULTS

# Overwrite default Values
LOADED = bool(CFGVARS.read(GLOBALCFG))
CFGVARS.read(LOCALCFG)

def write_cfg():
    """Write the Config File to prevent writing when running as module
    """

    if not LOADED:
        cfg = ConfigParser()
        cfg['settings'] = DEFAULTS
        try:
            with open(GLOBALCFG, 'w') as configfile:
                cfg.write(configfile)
        except OSError as ex:
            print("WARN: Unable to write Config: {}".format(ex))
