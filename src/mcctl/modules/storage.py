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
# along with mcctl.  If not, see <http:// www.gnu.org/licenses/>.

import sys
import shutil
from pathlib import Path
import zipfile as zf
from datetime import datetime
from pwd import getpwnam
from modules import service


def getHomePath(userName="mcserver"):
    userData = getpwnam(userName)
    return Path(userData.pw_dir)


def rename(instance, newName):
    basePath = getHomePath()
    serverPath = basePath / "instances" / instance
    serverPath.rename(newName)


def getChildPaths(path):
    return list(path.rglob("*"))


def chown(path, user, group=None):
    if group is None:
        group = getpwnam(user).pw_grp
    if path.is_dir():
        fileList = getChildPaths(path)
    else:
        fileList = [path]
    for f in fileList:
        shutil.chown(f, user, group)


def getRelativePaths(path, filter=None):
    if filter == None:
        filter = ''
    print(filter)
    pathList = []
    length = len(path.parts)
    for filePath in path.rglob("*"):
        relPath = Path(*filePath.parts[length:])
        if filter in relPath.parts[0]:
            pathList.append(relPath)
    return pathList


def createDirs(path):
    Path.mkdir(path, mode=0o0750, parents=True, exist_ok=True)


def copy(source, dest):
    return shutil.copy(source, dest)


def export(instance, zipPath=None, compress=False, worldOnly=False):
    if zipPath == None:
        zipPath = Path("{0}_{1}.zip".format(
            instance, datetime.now().strftime("%y-%m-%d-%H.%M.%S")))

    world = "world" if worldOnly else ""
    print(worldOnly)
    basePath = getHomePath()
    serverPath = Path(basePath, "instances", instance)
    fileList = getRelativePaths(serverPath, world)
    totalSize = sum([(serverPath / x).stat().st_size for x in fileList])
    compressMode = zf.ZIP_DEFLATED if compress else zf.ZIP_STORED
    with zf.ZipFile(zipPath, "w", compression=compressMode, allowZip64=True) as zipFile:
        written = 0
        for filePath in fileList:
            fullPath = serverPath / filePath
            written += fullPath.stat().st_size
            sys.stdout.write("\r[%3.0d%%] Writing: %s...\033[K" % (
                written * 100 / totalSize, filePath))
            zipFile.write(fullPath, filePath)
    print()
    return zipPath


def delete(instance, confirm=True):
    basePath = getHomePath()
    delPath = basePath / "instances" / instance
    assert delPath.exists(), "Instance not found"
    assert not (service.isEnabled(instance) or service.isActive(
        instance)), "Server is still enabled/running"
    if confirm:
        ans = input(
            "Are you absolutely sure you want to delete the Instance '{}'? [y/n]: ".format(instance))
        while ans.lower() not in ["y", "n"]:
            ans = input("Please answer [y]es or [n]o: ")
    else:
        ans = "y"
    if ans == "y":
        shutil.rmtree(delPath)
