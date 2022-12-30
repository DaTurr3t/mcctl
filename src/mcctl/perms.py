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
import sys
from contextlib import contextmanager
from pwd import getpwnam
from typing import Callable, NoReturn

from .__config__ import CFGVARS


def set_eids(uid: int, gid: int) -> tuple:
    """Change the user of the currently running python instance.

    Set the EGID and EUID of the running Python script to the permissions of <as_user>.

    Arguments:
        uid (int): The Effective User ID that is set.
        gid (int): The Effective Group ID that is set.

    Retruns:
        old_ids (tuple): A tuple of the UID and GID that were set before the change.
    """
    old_ids = (os.geteuid(), os.getegid())
    os.setegid(gid)
    os.seteuid(uid)

    return old_ids


@contextmanager
def run_as(uid: int, gid: int) -> None:
    """Manage the User Context and reset it after execution of the "with"-Block.

    Args:
        uid (int): The Effective User ID that is set during the "with"-Block.
        gid (int): The Effective Group ID that is set during the "with"-Block.
    """
    old = set_eids(uid, gid)
    try:
        yield
    finally:
        set_eids(*old)


def elevate(user: str = "root") -> NoReturn:
    """Replace the current Process with a new one as a different User. Requires sudo.

    Args:
        user (str, optional): The User that will be switched to. Defaults to "root".
    """
    desired_uid = getpwnam(user).pw_uid
    if os.getuid() == desired_uid:
        return
    package = sys.modules['__main__'].__package__  # pylint: disable=no-member
    if package:
        args = [sys.executable, "-m", package] + sys.argv[1:]
    else:
        args = sys.argv

    userargs = ["-u", user] if user != 'root' else []
    sudoargs = ["sudo"] + userargs + args
    os.execvp(sudoargs[0], sudoargs)


def demote() -> Callable:
    """Demote a subprocess. for use in preexec_fn.

    Returns:
        Callable: Returns a function executed by Popen() before running the external command.
    """
    user_name = CFGVARS.get('system', 'server_user')
    user = getpwnam(user_name)

    def set_ids() -> None:
        if os.getgid() + os.getuid() == 0:
            # Set EGID and EUID so that GID and UID can be set correctly.
            os.setegid(0)
            os.seteuid(0)

            os.setgid(user.pw_gid)
            os.setuid(user.pw_uid)

    return set_ids
