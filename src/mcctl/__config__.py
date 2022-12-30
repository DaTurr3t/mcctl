#!/bin/env python3

# mcctl: A Minecraft Server Management Utility written in Python
# Copyright (C) 2021 Matthias Cotting

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

import os
from shutil import copy
from pathlib import Path
from pwd import getpwnam
from configparser import ConfigParser
from . import ENCODING

CFGVARS = ConfigParser()

try:
    LOGIN_USER = os.getlogin()
except FileNotFoundError:
    LOGIN_USER = "nobody"
_USERDATA = getpwnam(LOGIN_USER)

_GLOBALCFG = Path("/etc/mcctl.conf")
_USERCFG = Path(f"{_USERDATA.pw_dir}/.local/mcctl.conf")
_TMPCFG = Path(f"/tmp/mcctl.{LOGIN_USER}.conf")


_SYSTEM_DEFAULTS = {
    'systemd_service': 'mcserver',
    'server_user': 'mcserver',
    'env_file': 'jvm-env',
}
_USER_DEFAULTS = {
    'editor': 'vim',
    'shell': '/bin/bash'
}

# Load User Vars and set Defaults.
CFGVARS['system'] = _SYSTEM_DEFAULTS
CFGVARS['user'] = _USER_DEFAULTS


def read_cfg() -> None:
    """Read Configuration Files."""
    if os.getuid() == _USERDATA.pw_uid and _USERCFG.is_file():
        try:
            copy(_USERCFG, _TMPCFG)
            os.chmod(_TMPCFG, 0o0664)
        except OSError as ex:
            print(f"WARN: Unable to copy User Config: {ex}")

    # Overwrite default Values
    CFGVARS.read((_GLOBALCFG, _TMPCFG))


def write_cfg(user: bool = False) -> None:
    """Write the Config File to prevent writing when running as module."""
    cfg_path = _USERCFG if user else _GLOBALCFG
    if not cfg_path.is_file():
        cfg = ConfigParser()
        if not user:
            cfg['system'] = _SYSTEM_DEFAULTS
        cfg['user'] = _USER_DEFAULTS

        with open(cfg_path, 'w', encoding=ENCODING) as configfile:
            cfg.write(configfile)
        if user:
            os.chown(cfg_path, _USERDATA.pw_uid, _USERDATA.pw_gid)
        print(f"Config File written to '{str(cfg_path)}'.")
    else:
        raise FileExistsError(f"'{str(cfg_path)}' already exists.")
