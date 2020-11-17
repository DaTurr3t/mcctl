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
# along with mcctl. If not, see <http://www.gnu.org/licenses/>.

from shutil import copy
from pathlib import Path
from os import getlogin, chmod
from configparser import ConfigParser

CFGVARS = ConfigParser()

try:
    _LOGIN_USER = getlogin()
except FileNotFoundError:
    _LOGIN_USER = "nobody"

_GLOBALCFG = Path("/etc/mcctl.conf")
_USERCFG = Path("~/.local/mcctl.conf").expanduser()
_TMPCFG = Path(f"/tmp/mcctl.{_LOGIN_USER}.conf")


_SYSTEM_DEFAULTS = {
    'systemd_service': 'mcserver',
    'server_user': 'mcserver',
}
_USER_DEFAULTS = {
    'editor': '/usr/bin/vim',
    'shell': '/usr/bin/bash'
}

# Load User Vars and set Defaults.
CFGVARS['system'] = _SYSTEM_DEFAULTS
CFGVARS['user'] = _USER_DEFAULTS
try:
    _USERCFG_EXISTS = _USERCFG.is_file()
except PermissionError:
    _USERCFG_EXISTS = False

if _USERCFG_EXISTS:
    try:
        copy(_USERCFG, _TMPCFG)
        chmod(_TMPCFG, 0o0664)
    except OSError as ex:
        print(f"WARN: Unable to copy User Config: {ex}")

# Overwrite default Values
_LOADED_FROM_DISK = bool(CFGVARS.read(_GLOBALCFG))
CFGVARS.read(_TMPCFG)


def write_cfg():
    """Write the Config File to prevent writing when running as module."""
    if not _LOADED_FROM_DISK:
        cfg = ConfigParser()
        cfg['system'] = _SYSTEM_DEFAULTS
        cfg['user'] = _USER_DEFAULTS
        try:
            with open(_GLOBALCFG, 'w') as configfile:
                cfg.write(configfile)
        except OSError as ex:
            print(f"WARN: Unable to write Config: {ex}")
