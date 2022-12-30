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
# along with mcctl. If not, see <http:// www.gnu.org/licenses/>.


import gzip
import hashlib
import os
import random
import shutil
import string
import tempfile as tmpf
import zipfile as zf
from datetime import datetime
from grp import getgrgid
from pathlib import Path
from pwd import getpwnam

from . import config, perms, service, visuals
from .__config__ import CFGVARS

SERVER_USER = CFGVARS.get('system', 'server_user')


def get_home_path(user_name: str = SERVER_USER) -> Path:
    """Return the home directory of a user.

    Arguments:
        user_name (str): The username of which the home directory should be determined.

    Returns:
        Path: The home directory of the user.
    """
    user_data = getpwnam(user_name)
    return Path(user_data.pw_dir)


def get_instance_path(instance: str = '', bare: bool = False) -> Path:
    """Return the assembled absolute Instance Path.

    Keyword Arguments:
        instance (str): The name of the Instance.
        bare (bool): Allow returning the bare Instance Folder.

    Returns:
        Path: The absolute Path to the Instance
    """
    if not instance and not bare:
        raise ValueError("No valid Instance supplied")
    return get_home_path() / "instances" / instance


def get_plugin_path(instance: str) -> Path:
    """Return the assembled absolute Plugin Path.

    Arguments:
        instance (str): The name of the Instance.

    Returns:
        Path: The absolute Path to the Plugin folder of the Instance.
    """
    return get_instance_path(instance) / "plugins"


def get_jar_path(type_id: str = '', bare: bool = False) -> Path:
    """Return the assembled asolute Path of a cached .jar-File.

    Args:
        type_id (str, optional): The type_id of the .jar-File. Defaults to ''.
        bare (bool, optional): Allow returning the bare Jar Cache Folder. Defaults to False.

    Returns:
        Path: The Path to the .jar-File supplied.
    """
    bare_path = get_home_path() / "jars"
    if ':' in type_id:
        return bare_path / f"{type_id.replace(':', '/')}.jar"
    elif bare:
        return bare_path
    raise ValueError("No valid Type-ID supplied")


def get_type_id(jar_path: Path) -> str:
    """Assemble the Type ID from the Jar Path in the Cache.

    Args:
        jar_path (Path): The Path to the Jar in the Cache.

    Raises:
        ValueError: If the relative Path is too short to be processed into a Type ID.

    Returns:
        str: a Type ID to download a Jar File.
    """
    jar_path = Path(jar_path)
    bare_path = get_home_path() / "jars"
    relative_jar = jar_path.relative_to(bare_path) if jar_path.is_absolute() else jar_path
    if len(str(relative_jar).split("/")) < 2:
        raise ValueError("Jar Path is too short.")
    fname = relative_jar.stem
    dirs = str(relative_jar.parent).split("/")
    type_id = ":".join(dirs + [fname])
    return type_id


def get_child_paths(path: Path) -> list:
    """Get all subdirectories and files of a Path.

    Arguments:
        path (Path): Path to walk.

    Returns:
        list: A list of all paths found.
    """
    return sorted(path.rglob("*"))


def list_jars(filter_str: str = '') -> None:
    """Get a List of all cached .jar-files.

    Lists all cached .jar-Files in the Type-Tag format.

    Keyword Arguments:
        filter_str (str): Filter for version, type or version. (default: {''})
    """
    jars = get_relative_paths(get_home_path() / "jars", ".jar", -1)
    for jar in jars:
        if filter_str in str(jar):
            print(str(jar).replace("/", ":").replace(".jar", ''))


def chown(path: Path, user: str, group: str = None) -> None:
    """Change owner of file or of a path recursively.

    Changes the owner of a file or of a path and its subdirectories.
    The gid of the default group of the user is used if [group] is omitted.

    Arguments:
        path (Path): The path of which owners should be recursively changed.
        user (str): User that should own the path.

    Keyword Arguments:
        group (str): Group that should own the path. (default: {None})
    """
    if not group:
        gid = getpwnam(user).pw_gid
        group = getgrgid(gid).gr_name
    if path.is_dir():
        file_list = get_child_paths(path)
    else:
        file_list = [path]
    for fle in file_list:
        shutil.chown(fle, user, group)


def get_relative_paths(path: Path, filter_str: str = '', filter_idx: int = 0) -> list:
    """Get relative subdirectories of path.

    Get the subdirectories of a path, without any of the path itself. Files are omitted.
    E.g. if 'path/to/dir' has two subdirectories 'path/to/dir/one' and 'path/to/dir/two', 'one' and 'two' are listed.

    The Filter allows simple tests on a directory in the truncated Path. The directory to test against is specified by filter_idx.
    0 -  the first directory of the path is tested. -1 - the last directory is tested, etc.

    Arguments:
        path (Path): The path of which the subdirecories should be returned.

    Keyword Arguments:
        filter_str (str): A string that is checked against a specified directory. (default: {''})
        filter_idx (int): The index of the directory to test against. (default: {0})

    Returns:
        list: A list of all relative Paths found.
    """
    path_list = []
    length = len(path.parts)
    for file_path in get_child_paths(path):
        rel_path = Path(*file_path.parts[length:])
        if filter_str in rel_path.parts[filter_idx]:
            path_list.append(rel_path)
    return path_list


def create_dirs(path: Path) -> None:
    """Create Paths recursively, with mode rwxr-x---.

    Arguments:
        path (Path): Path to create, if nonexistent.
    """
    Path.mkdir(path, mode=0o0750, parents=True, exist_ok=True)


def remove_all(path: Path) -> None:
    """Remove a path and its children, or a single file.

    Arguments:
        path (Path): Path to delete.
    """
    shutil.rmtree(path)


def copy(source: Path, dest: Path) -> Path:
    """Copy a file or directory.

    If [dest] is a directory and [source] is a file, the filename of [source] is retained.

    Arguments:
        source (Path): Source file or directory.
        dest (Path): Destionation file or directory.

    Returns:
        Path: The Destination Path of the copied file.
    """
    return shutil.copy(source, dest)


def symlink(src: Path, dst: Path) -> None:
    """Create a symbolic Link for a file or directory. Existing Symlinks are overwritten.

    Args:
        src (Path): The original File/Directory.
        dst (Path): The Link itself.
    """
    if dst.is_symlink():
        dst.unlink()
    os.symlink(src, dst)


def get_real_abspath(path: Path) -> Path:
    """Return the real, absolute Path of a potential symlink. If the path is not a symlink, return the input Path.

    Args:
        path (Path): A file/directory that is potentially a symlink.

    Returns:
        Path: The real, absolute Path of the file. Returns the original path if not a symlink.
    """
    if path.is_symlink():
        link = Path(os.readlink(path))
        if not link.is_absolute():
            link = path / link
        return link
    else:
        return path


def move(source: Path, dest: Path) -> Path:
    """Move a file or directory.

    If [dest] is a directory and [source] is a file, the filename of [source] is retained.

    Arguments:
        source (Path): Source file or directory.
        dest (Path): Destionation file or directory.

    Returns:
        Path: The Destination Path of the copied file.
    """
    return shutil.move(source, dest)


def export(instance: str, zip_path: Path = None, compress: bool = False, world_only: bool = False) -> Path:
    """Export a minecraft server instance to a Zip-File.

    Export a minecraft server instance to a Zip-File for archiving or similar.
    Optionally, the File can also be compressed and all config Files can be excluded.

    Arguments:
        instance (str): The name of the Instance to be exported.

    Keyword Arguments:
        zip_path (Path): The path of the Zip-File that is generated. (default: {None})
        compress (bool): True: Compress the Zip-File using ZIP_DEFLATE. False: Use ZIP_STORE (default: {False})
        world_only (bool): Only export the World data without configuration files. (default: {False})

    Returns:
        Path: The Path where the Zip-File was saved to.
    """
    if not zip_path:
        zip_path = Path(
            f"{instance}_{datetime.now().strftime('%y-%m-%d-%H.%M.%S')}.zip")

    server_path = get_instance_path(instance)

    filter_str = ""
    if world_only:
        server_cfg = config.get_properties(server_path / "server.properties")
        filter_str = server_cfg.get("level-name", "world")

    file_list = get_relative_paths(server_path, filter_str)
    total_size = sum((server_path / x).stat().st_size for x in file_list)
    compress_mode = zf.ZIP_DEFLATED if compress else zf.ZIP_STORED
    with perms.run_as(0, 0), zf.ZipFile(zip_path, "w", compression=compress_mode, allowZip64=True) as zip_file:
        written = 0
        for file_path in file_list:
            full_path = server_path / file_path
            written += full_path.stat().st_size
            msg = f"\r[{(written * 100 / total_size):3.0f}%] Writing: {file_path}...\033[K"
            print(msg, end='', flush=True)
            zip_file.write(full_path, file_path)
    print()

    try:
        login_name = os.getlogin()
    except FileNotFoundError:
        login_name = None
        print("WARN: Unable to retrieve Login Name.")
    if login_name:
        with perms.run_as(0, 0):
            chown(zip_path, login_name)

    print(f"Archive saved in '{zip_path}'.")
    return zip_path


def remove(instance: str, force: bool = False) -> None:
    """Remove an instance from disk.

    Arguments:
        instance (str): The name of the Instance to be deleted.

    Keyword Arguments:
        force (bool): Delete the Instance without a prompt. (default: {False})
    """
    del_path = get_instance_path(instance)
    if not del_path.exists():
        raise FileNotFoundError(f"Instance Path not found: {del_path}.")
    unit = service.get_unit(instance)
    if (service.is_enabled(unit) or service.is_active(unit)):
        raise OSError("The server is still running and/or persistent.")

    prompt_msg = f"Are you absolutely sure you want to remove the Instance '{instance}'?"
    do_remove = force or visuals.bool_selector(prompt_msg)

    if do_remove:
        remove_all(del_path)


def remove_jar(source: str, force: bool = False) -> None:
    """Remove an .jar-File from disk.

    Arguments:
        type_id (str): The type_id of the .jar-File to be deleted.
    Keyword Arguments:
        force (bool): Delete the Jar File without a prompt. (default: {False})
    """
    del_all = source == "all"
    if not del_all:
        del_path = get_jar_path(source)
        msg = f"Are you absolutely sure you want to remove the Server Jar '{source}'?"
    else:
        del_path = get_jar_path(bare=True)
        msg = "Are you sure you want to remove all unused cached Server Jars?"

    if not del_all:
        if not del_path.exists():
            raise FileNotFoundError(f"Type-ID not found in cache: {del_path}.")
        all_instances = get_instance_path(bare=True).iterdir()
        for instance_path in all_instances:
            env_path = instance_path / CFGVARS.get('system', 'env_file')
            try:
                env = config.get_properties(env_path)
            except OSError:
                env = {}
            server_jar = instance_path / env.get("JARFILE", "server.jar")
            if get_real_abspath(server_jar) == del_path:
                raise OSError(
                    f"Type-ID is associated with Instance {instance_path.name}.")
    else:
        if not del_path.exists():
            raise FileNotFoundError("Cache already cleared.")
    if force or visuals.bool_selector(msg):
        if not del_all:
            del_path.unlink()
        else:
            remove_all(del_path)


def logs(instance: str, limit: int = 0) -> None:
    """Get the last lines of the Log.

    Arguments:
        instance (str): The name of the instance to read logs from.

    Keyword Arguments:
        limit (int): The amount of lines to output. 0 returns all lines. (default: {0})
    """
    if limit < 0:
        raise OverflowError("Line Limit is lower than minimum of 0.")
    log_path = get_instance_path(instance) / "logs"
    log_paths = get_child_paths(log_path)

    lines = []
    for log in reversed(log_paths):
        opener = gzip.open if log.name.endswith(".gz") else open
        with opener(log, "rt") as log_file:
            lines = log_file.readlines() + lines
        if len(lines) >= limit and limit != 0:
            break

    lines_out = lines[-limit:]
    print(''.join(lines_out), end='', flush=True)


def tmpcopy(file_path: Path) -> Path:
    """Create a temporary copy of a file. Create original File if it does not exist.

    Args:
        file_path (Path): The file which will be copied to a temporary location.

    Returns:
        Path: The Path where the temporary file is saved.
    """
    tmpid = ''.join(random.choice(string.ascii_letters) for _ in range(16))
    tmp_path = file_path.parent / Path(f"{file_path.name}.{tmpid}")
    if not file_path.exists():
        file_path.touch()
    shutil.copy(file_path, tmp_path)
    return tmp_path


def get_file_hash(file_path: Path) -> str:
    """Generate the Hash of a File.

    Args:
        file_path (Path): The Path of the File to be hashed.

    Returns:
        str: The Hash as a String.
    """
    hash_sha1 = hashlib.sha1()
    with open(file_path, "rb") as fhnd:
        for chunk in iter(lambda: fhnd.read(4096), b""):
            hash_sha1.update(chunk)
    return hash_sha1.hexdigest()


def install_bare_plugin(plugin_path: Path, plugin_dest: Path) -> str:
    """Install a .jar file as a Plugin on a Server.

    Args:
        plugin_path (Path): The source path of the plugin.
        plugin_dest (Path): The destination path of the plugin.

    Returns:
        str: The file name of the installed plugin
    """
    dst_file = plugin_dest / plugin_path.name
    copy(plugin_path, dst_file)
    dst_file.chmod(0o640)
    chown(dst_file, user=SERVER_USER)
    return plugin_path.name


def install_compressed_plugin(plugin_path: Path, plugin_dest: Path) -> list:
    """Install a user selection of .jar files from a compresed file as a Plugin on a Server.

    Args:
        plugin_path (Path): The source path of the archive containing plugin(s).
        plugin_dest (Path): The destination path of the plugin(s).

    Raises:
        FileNotFoundError: If no Plugins are found in the Archive.

    Returns:
        list: File names of installed plugins.
    """
    installed = []
    with zf.ZipFile(plugin_path) as zip_file:
        selection = []
        for zinfo in zip_file.infolist():
            if not zinfo.is_dir() and zinfo.filename.endswith(".jar"):
                selection.append(zinfo)
        if len(selection) < 1:
            raise FileNotFoundError("No Plugin(s) found in Archive.")
        elif len(selection) > 1:
            print(f"Multiple Plugins found in '{plugin_path}':")
            final_selection = visuals.list_selector(
                selection, display=lambda x: Path(x.filename).name)
        else:
            final_selection = selection
        for zinfo in final_selection:
            jar_name = Path(zinfo.filename).name
            dst = plugin_dest / jar_name
            with zip_file.open(zinfo) as zjar, open(dst, 'wb') as dst_file:
                shutil.copyfileobj(zjar, dst_file)
            dst.chmod(0o640)
            chown(dst, user=SERVER_USER)
            installed.append(jar_name)
    return installed


def mc_import(zip_path: Path, instance: str = None, world_only: bool = False) -> None:
    """Import a minecraft server instance from a Zip-File.

    Import a minecraft server instance from a Zip-File.
    Also, the world files can be extracted separately.

    Arguments:
        zip_path (Path): The path of the Zip-File to import from. (default: {None})

    Keyword Arguments:
        instance (str): The name of the Instance to be imported. Auto-generated from archive name if None. (default: {None})
        world_only (bool): Only import the World data without configuration files. (default: {False})
    """
    if instance is None:
        instance = zip_path.stem
        print(f"No Instance specified, importing to instance '{instance}'.")
    instance_path = get_instance_path(instance)
    if instance_path.exists() != world_only:
        if world_only:
            raise FileNotFoundError(
                f"Instance Path not found: {instance_path}.")
        raise FileExistsError("Instance already exists.")

    if not instance_path.exists():
        create_dirs(instance_path)
    filter_str = ""
    with zf.ZipFile(zip_path) as zip_file:
        if world_only:
            with zip_file.open("server.properties") as prop, tmpf.NamedTemporaryFile() as tmp_file:
                shutil.copyfileobj(prop, tmp_file)
                properties = config.get_properties(tmp_file.name)
                filter_str = properties.get("level-name", "world") + "/"
        file_list = (x for x in zip_file.infolist()
                     if x.name.startswith(filter_str))
        t_size = sum(x.file_size for x in file_list)
        written = 0
        for zpath in file_list:
            safe_zpath = zpath.filename.replace("../", "")
            dst_path = instance_path / safe_zpath
            with zip_file.open(zpath) as zfile, open(dst_path, 'wb') as dst_file:
                written += zpath.file_size
                print(f"\r[{(written * 100 / t_size):3.0f}%] Extracting: {safe_zpath}...\033[K",
                      end='', flush=True)
                shutil.copyfileobj(zfile, dst_file)
    print()
    chown(instance_path, user=SERVER_USER)
