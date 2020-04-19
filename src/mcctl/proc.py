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

import shlex
import time
import os
import subprocess as sproc
from pathlib import Path
from pwd import getpwnam
from mcctl import settings
from mcctl.storage import get_home_path
from mcctl.service import is_active
from mcctl.visuals import compute


def attach(instance: str):
    """Attach to the console of a server.

    Launches screen to reattach to the screen session of the server.

    Arguments:
        instance {str} -- The name of the instance.
    """

    assert is_active(instance), "The Server is not running"
    cmd = shlex.split('screen -r mc-{}'.format(instance))
    proc = sproc.Popen(cmd, preexec_fn=demote())
    proc.wait()


def mc_exec(instance: str, command: list, timeout: int = 0.5):
    """Execute a command on the console of a server.

    Uses the 'stuff' command of screen to pass the minecraft command to the server.
    Return Values are read from 'latest.log' shortly after the command is executed.
    The logfile is read every <timeout> seconds. If nothing is appended to the Log in this timespan, the function completes.

    Arguments:
        instance {str} -- The name of the instance.
        command {list} -- A list of the individual parts of the command executed on the server console.

    Keyword Arguments:
        timeout {int} -- The timeout interval between log reads. (default: {0.5})
    """

    assert is_active(
        instance), "The Server is not running"

    log_path = get_home_path() / "instances" / instance / "logs/latest.log"

    old_count = 0
    line_count = sum(1 for line in open(log_path))

    jar_cmd = " ".join(command)
    cmd = shlex.split(
        'screen -p 0 -S mc-{0} -X stuff "{1}^M"'.format(instance, jar_cmd))
    proc = sproc.Popen(cmd, preexec_fn=demote())
    proc.wait()

    while line_count > old_count:
        time.sleep(timeout)
        i = 0
        with open(log_path) as log:
            for i, line in enumerate(log):
                if i >= line_count:
                    print(line.rstrip())
        old_count = line_count
        line_count = i + 1


def get_ids(user: str) -> tuple:
    """Wrapper for getpwnam() that only returns UID and GID.

    Arguments:
        user {str} -- User of which passwd information should be retrieved.

    Returns:
        tuple -- A Tuple containing th UID and GID of the user.
    """
    user_data = getpwnam(user)
    return (user_data.pw_uid, user_data.pw_gid)


def run_as(uid: int, gid: int) -> tuple:
    """Changes the user of the current python Script

    Set the EGID and EUID of the running Python script to the permissions of <as_user>.

    Arguments:
        as_user {str} -- The User of which the UID and GID is used.

    Retruns:
        old_ids {tuple}  -- A tuple of the UID and GID that were set before the change.
    """
    old_ids = (os.geteuid(), os.getegid())

    os.setegid(gid)
    os.seteuid(uid)

    return old_ids


def demote():
    """A Function containing instructions to demote a subprocess.

    Returns:
        NoneType -- Returns a function executed by Popen() before running the external command.
    """
    user_name = settings.CFG_DICT['server_user']
    user = getpwnam(user_name)

    def set_ids():
        # Set EGID and EUID so that GID and UID can be set correctly.
        os.setegid(0)
        os.seteuid(0)

        os.setgid(user.pw_gid)
        os.setuid(user.pw_uid)

    return set_ids


def pre_start(jar_path: Path, watch_file=None, kill_sec: int = 80) -> bool:
    """Prepares the server and lets it create configuration files and such.

    Starts the server and waits for it to exit or for [watchFile] to be created.
    If the file exists, the server is sent SIGTERM to shut it down again.

    Arguments:
        jar_path {Path} -- Path to the jar-file of the server.

    Keyword Arguments:
        watch_file {Path} -- A file to be awaited for creation. Ignored if set to None. (default: {None})
        kill_sec {int} -- Time to wait before killing the server. (default: {80})

    Returns:
        bool -- True: The server stopped as expected. False: The server had to be killed.
    """

    cmd = shlex.split('/bin/java -jar {}'.format(jar_path))
    proc = sproc.Popen(cmd, cwd=jar_path.parent,
                       preexec_fn=demote(), stdout=sproc.PIPE, stderr=sproc.PIPE)

    fps = 4
    signaled = False
    success = False
    for i in range(kill_sec*fps+1):
        print("\r{} Setting up config files...".format(compute(2)), end="")
        time.sleep(1/fps)
        if not signaled and watch_file is not None and watch_file.exists():
            proc.terminate()
            signaled = True
        elif i == kill_sec * fps:
            proc.kill()
        elif proc.poll() is not None:
            success = True
            break
    print()
    return success
