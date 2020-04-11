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


def chownRecurse(path):
    fileList = getChildPaths(path)
    for f in fileList:
        shutil.chown(f, "mcserver", "mcserver")


def getRelativePaths(path, worldName=None):
    if worldName == None:
        worldName = ''
    pathList = []
    length = len(path.parts) - 1
    for filePath in path.glob("{}*/**".format(worldName)):
        relPath = Path(*filePath.parts[length:])
        pathList.append(relPath)
    return pathList


def createDirs(path):
    Path.mkdir(path, mode=0o0750, parents=True, exist_ok=True)


def copy(source, dest):
    return shutil.copy(source, dest)


def export(instance, zipPath=None, worldOnly=False):
    if zipPath == None:
        zipPath = "{0}_{1}.zip".format(
            instance, datetime.now().strftime("%y-%m-%d-%H.%M.%S"))

    world = "world" if worldOnly else ""

    basePath = getHomePath()
    serverPath = Path(basePath, "instances", instance)
    fileList = getRelativePaths(serverPath, world)
    totalSize = sum([x.stat().st_size for x in fileList])
    with zf.ZipFile(zipPath, "w", compression=zf.ZIP_DEFLATED, allowZip64=True) as zipFile:
        written = 0
        for filePath in fileList:
            written += filePath.stat().st_size
            sys.stdout.write("\r[%3.0d%%] Compressing: %s..." % (
                written * 100 / totalSize, filePath))
            zipFile.write(filePath)


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
