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

import sys
import shutil
from pathlib import Path
import zipfile as zf
from datetime import datetime


def getHomePath(userName="mcserver"):
    with open("/etc/passwd", "r") as passwd:
        for userData in passwd.readlines():
            if userName in userData:
                return Path(userData.split(":")[5])


def rename(instance, newName):
    basePath = getHomePath()
    serverPath = basePath / "instances" / instance
    serverPath.rename(newName)
    pass


def getChildPaths(path, worldName=None):
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


def export(instance, zipPath=None, worldOnly=False):
    if zipPath == None:
        zipPath = "{0}_{1}.zip".format(
            instance, datetime.now().strftime("%y-%m-%d-%H.%M.%S"))

    world = "world" if worldOnly else ""

    basePath = getHomePath()
    serverPath = Path(basePath, "instances", instance)
    fileList = getChildPaths(serverPath, world)
    totalSize = sum([x.stat().st_size for x in fileList])
    pathLen = max([len(str(x)) for x in fileList])
    with zf.ZipFile(zipPath, "w", compression=zf.ZIP_DEFLATED, allowZip64=True) as zipFile:
        written = 0
        for filePath in fileList:
            padding = " "*(pathLen + 4 - len(str(filePath)))
            written += filePath.stat().st_size
            sys.stdout.write("\r[{0}%]\r       Compressing: {1} ...{2}".format(
                written * 100 / totalSize, filePath, padding))
            zipFile.write(filePath)


def delete(instance):
    ans = input(
        "Are you absolutely sure to delete the Instance '{}'? [y/n]: ".format(instance)).lower()
    while ans not in ["y", "n"]:
        ans = input("Please answer [y]es or [n]o: ")
    if ans == "y":
        basePath = getHomePath()
        delPath = basePath / "instances" / instance
        shutil.rmtree(delPath)
    pass
