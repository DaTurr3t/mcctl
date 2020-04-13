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
from mcctl import service, config, settings

serverUser = settings.cfgDict['server_user']

def getHomePath(userName: str = serverUser) -> Path:
    """Wrapper to return the home Directory of a user

    Arguments:
        userName {str} -- The username of which the home directory should be determined.

    Returns:
        Path -- The home directory of the user.
    """

    userData = getpwnam(userName)
    return Path(userData.pw_dir)


def getChildPaths(path: Path) -> list:
    """Wrapper to get all subdirectories and files.

    Arguments:
        path {Path} -- Path to walk

    Returns:
        list -- A list of all paths found.
    """

    return list(path.rglob("*"))


def getJarList(filter: str = ''):
    """Get List of all cached .jar-files

    Lists all cached .jar-Files in the Type-Tag format.

    Keyword Arguments:
        filter {str} -- Filter for version, type or version. (default: {''})
    """

    jars = getRelativePaths(getHomePath() / "jars", ".jar", -1)
    for jar in jars:
        if filter in str(jar):
            print(str(jar).replace("/", ":").replace(".jar", ''))


def chown(path: Path, user: str, group=None):
    """Change owner of file or of a path recursively.

    Changes the owner of a file or of a path and its subdirectories.
    The gid of the default group of the user is used if [group] is omitted.

    Arguments:
        path {Path} -- The path of which owners should be recursively changed.
        user {str} -- User that should own the path.

    Keyword Arguments:
        group {[type]} -- Group that should own the path. (default: {None})
    """

    if group is None:
        group = getpwnam(user).pw_gid
    if path.is_dir():
        fileList = getChildPaths(path)
    else:
        fileList = [path]
    for f in fileList:
        shutil.chown(f, user, group)


def getRelativePaths(path: Path, filter: str = '', filterIdx: int = 0) -> list:
    """Get relative subdirectories of path.

    Get the subdirectories of a path, without any of the path itself.
    E.g. if 'path/to/dir' has two subdirectories 'path/to/dir/one' and 'path/to/dir/two', 'one' and 'two' are listed.

    The Filter allows simple tests on a directory in the truncated Path. The directory to test against is specified by filterIdx.
    0 -  the first directory of the path is tested. -1 - the last directory is tested, etc.

    Arguments:
        path {Path} -- The path of which the subdirecories should be returned.

    Keyword Arguments:
        filter {str} -- A string that is checked agains a specified  (default: {''})
        filterIdx {int} -- The index of the directory to test against. (default: {0})

    Returns:
        list -- A list of all relative Paths found.
    """

    pathList = []
    length = len(path.parts)
    for filePath in getChildPaths(path):
        relPath = Path(*filePath.parts[length:])
        if filter in relPath.parts[filterIdx]:
            pathList.append(relPath)
    return pathList


def createDirs(path: Path):
    """Wrapper to create Paths recursively, with mode rwxr-x---.

    Arguments:
        path {Path} -- Path to create, if nonexistent.
    """

    Path.mkdir(path, mode=0o0750, parents=True, exist_ok=True)


def copy(source: Path, dest: Path):
    """Wrapper to copy a file or directory

    If [dest] is a directory and [source] is a file, the filename of [source] is retained.

    Arguments:
        source {Path} -- Source file
        dest {Path} -- Destionation file or directory

    Returns:
        Path -- The Destination Path of the copied file.
    """

    return shutil.copy(source, dest)


def export(instance: str, zipPath=None, compress: bool = False, worldOnly: bool = False) -> Path:
    """Export a minecraft server instance to a Zip-File.

    Export a minecraft server instance to a Zip-File for archiving or similar. 
    Optionally, the File can also be compressed and all config Files can be excluded.

    Arguments:
        instance {str} -- The name of the Instance to be exported.

    Keyword Arguments:
        zipPath {Path} -- The path of the Zip-File that is generated. (default: {None})
        compress {bool} -- True: Compress the Zip-File using ZIP_DEFLATE. False: Use ZIP_STORE (default: {False})
        worldOnly {bool} -- Only export the World data without configuration files. (default: {False})

    Returns:
        Path -- The Path where the Zip-File was saved to.
    """

    if zipPath == None:
        zipPath = Path("{0}_{1}.zip".format(
            instance, datetime.now().strftime("%y-%m-%d-%H.%M.%S")))
    basePath = getHomePath()
    serverPath = Path(basePath, "instances", instance)

    world = ""
    if worldOnly:
        serverCfg = config.getProperties(serverPath / "server.properties")
        world = serverCfg["level-name"]

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


def remove(instance: str, confirm: bool = True):
    """Remove an instance from disk.

    Arguments:
        instance {str} -- The name of the Instance to be deleted.

    Keyword Arguments:
        confirm {bool} -- Ask the user if they are sure to delete the instance. (default: {True})
    """

    basePath = getHomePath()
    delPath = basePath / "instances" / instance
    assert delPath.exists(), "Instance not found"
    assert not (service.isEnabled(instance) or service.isActive(
        instance)), "The server is still persistent and/or running"
    if confirm:
        ans = input(
            "Are you absolutely sure you want to remove the Instance '{}'? [y/n]: ".format(instance))
        while ans.lower() not in ["y", "n"]:
            ans = input("Please answer [y]es or [n]o: ")
    else:
        ans = "y"
    if ans == "y":
        shutil.rmtree(delPath)
