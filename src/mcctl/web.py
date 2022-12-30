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

import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests as req

from . import storage, visuals


def rest_get(url: str) -> dict:
    """Send a get request and parse response from JSON.

    A HTTP GET request is sent to the specified URL. The response is parsed into a dict.

    Arguments:
        url (str): The target to query.

    Returns:
        dict: Deserialized JSON Data.
    """
    response = req.get(url, timeout=5)
    response.raise_for_status()
    return response.json()


def scrape_get(url: str, expr: str) -> list:
    """Send a get request and filter response with regex.

    A HTTP GET request is sent to the specified URL. The regex matches are returned.

    Arguments:
        url (str): The target to query.
        expr (str): A regular expression to scrape the page.

    Returns:
        list: List of matches
    """
    response = req.get(url, timeout=5)
    response.raise_for_status()
    return re.findall(expr, response.text)


def get_vanilla_download_url(version_tag: str, manifest_url: str) -> tuple:
    """Get the download URL of a vanilla server.

    Find the download URL of a vanilla server using Mojangs Launcher-Meta API.

    Keyword Arguments:
        version_tag (str): The Tag of the server without the type (vanilla/paper).
        manifest_url (str): The URL of version_manifest.json

    Raises:
        LookupError: If the Download URL of the specified Version was not found.

    Returns:
        tuple: A tuple with the download URL and the complete, resolved Tag
    """
    version_manifest = rest_get(manifest_url)
    if version_tag == "latest":
        version_tag = version_manifest.get("latest", {}).get("release")
    elif version_tag == "latest-snap":
        version_tag = version_manifest.get("latest", {}).get("snapshot")

    download_url = None
    for version in version_manifest.get("versions", []):
        if version.get("id") == version_tag:
            download_url = version.get("url")
            break
    if download_url is None:
        raise LookupError("Server Version not found")
    version_data = rest_get(download_url)
    url = version_data.get("downloads", {}).get("server", {}).get("url")
    return url, version_tag


def get_paper_download_url(version_tag: str, base_url: str) -> tuple:
    """Get the download URL of a paper server.

    Find the download URL of a paper server using PaperMCs Version API.

    Arguments:
        version_tag (str): The Tag of the server without the type (vanilla/paper).
        base_url (str): The API URL for Paper.

    Returns:
        tuple: A tuple with the download URL and the complete, resolved Tag
    """
    if version_tag == "latest":
        project = rest_get(base_url)
        try:
            major = project["versions"][-1]
        except (IndexError, KeyError) as ex:
            raise LookupError(f"Unable to determine latest Version: {ex}") from ex
        minor = version_tag
    elif ":" in version_tag:
        major, minor = version_tag.split(":", 1)
    else:
        raise ValueError("Not enough Segments for Paper Version Tag.")

    if minor == "latest":
        version_url = join_url(base_url, "versions", major)
        version = rest_get(version_url)
        try:
            minor = str(version["builds"][-1])
        except (IndexError, KeyError) as ex:
            raise LookupError(f"Unable to determine latest Build: {ex}") from ex

    build_url = join_url(base_url, "versions", major, "builds", minor)
    try:
        download_file = rest_get(build_url)["downloads"]["application"]["name"]
    except (req.exceptions.HTTPError, KeyError) as ex:
        raise OSError("Unable to determine Download File Name.") from ex

    resolved_tag = ":".join((major, minor))
    return join_url(build_url, "downloads", download_file), resolved_tag


def get_spigot_download_url(version_tag: str, base_url: str, download_url: str) -> tuple:
    """Get the download URL of a paper server.

    Find the download URL of a paper server using PaperMCs Version API.

    Arguments:
        version_tag (str): The Tag of the server without the type (vanilla/paper/spigot).
        base_url (str):  The API URL for spigot.
        download_url: (str): The Download Base URL for Spigot.

    Returns:
        tuple: A tuple with the download URL and the complete, resolved Tag
    """
    expr = re.compile(r"<.*>Version</.*>\n?<.*>(.*)</.*>")
    versions = scrape_get(base_url, expr)
    if version_tag == "latest":
        resolved_version = versions[0]
    elif version_tag in versions:
        resolved_version = version_tag
    else:
        raise LookupError("Server Version not found")

    return f"{download_url}{resolved_version}.jar", resolved_version


SOURCES = {
    "vanilla": {
        "func": get_vanilla_download_url,
        "kwargs": {
            "manifest_url": "https://launchermeta.mojang.com/mc/game/version_manifest.json",
        },
    },
    "spigot": {
        "func": get_spigot_download_url,
        "kwargs": {
            "base_url": "https://getbukkit.org/download/spigot",
            "download_url": "https://cdn.getbukkit.org/spigot/spigot-",
        }
    },
    "paper": {
        "func": get_paper_download_url,
        "kwargs": {
            "base_url": "https://papermc.io/api/v2/projects/paper",
        },
    }
}


def get_download_url(server_tag: str) -> tuple:
    """Get the download URL of any minecraft server.

    Arguments:
        server_tag (str): The Tag of the server (e.g. vanilla:latest).

    Raises:
        Exception: If an unsupported Server type is used, an Exception is raised.

    Returns:
        tuple: A tuple with the download URL and the complete, resolved Tag
    """
    if ":" not in server_tag:
        raise ValueError(f"Invalid Server Tag '{server_tag}'")
    type_tag, version_tag = server_tag.split(":", 1)
    source_func = SOURCES.get(type_tag)
    if source_func is None:
        raise ValueError("Unsupported server type.")

    func = source_func['func']
    kwargs = source_func["kwargs"]
    url, resolved_tag = func(version_tag, **kwargs)

    return url, ":".join((type_tag, resolved_tag))


def download(url: str, dest: Path) -> None:
    """Download a file with progress report.

    A file is downloaded from a webserver, progress is shown via the reporthook-Parameter.

    Arguments:
        url (str): The target to query.
        dest (Path): The path where to save the recieved file to.
    Returns:
        Path: The absolute destination Path, filename included.
    """
    dest = Path(dest)
    response = req.get(url, stream=True, timeout=10)
    if dest.is_dir():
        fdisp = response.headers.get('content-disposition')
        if fdisp is not None:
            fname = re.findall(r"filename\*?=(?:.+'')?(.+)", fdisp)[-1]
            file_dest = dest / fname
        else:
            file_dest = dest / url.split("/")[-1]
    else:
        file_dest = dest

    with open(file_dest, "wb") as dest_hnd:
        total_length = int(response.headers.get('content-length', 0))

        if not total_length:
            dest_hnd.write(response.content)
        else:
            chunk_size = 4096
            loaded = 0
            inital = time.time()
            for data in response.iter_content(chunk_size):
                loaded += len(data)
                dest_hnd.write(data)
                elapsed = time.time() - inital
                visuals.progress(loaded, elapsed, total_length)
        print()
    return file_dest.absolute()


def is_url(url: str) -> bool:
    """Test if the string is a valid URL.

    Args:
        url (str): A string that is potentially a URL

    Returns:
        bool: True if the submitted String is a valid URL.
    """
    try:
        seg = urlparse(url)
    except ValueError:
        return False
    return all((seg.scheme, seg.netloc, seg.path))


def join_url(base: str, *parts: str) -> str:
    """Join an URL and its segments.

    Arguments:
        base (str): The base of the url, containing the protocol and hostname.
        *parts (str): The path parts of the URL.

    Returns:
        str: The complete, joined URL
    """
    path = "/".join([x.strip("/") for x in parts])
    return f"{base.rstrip('/')}/{path}"


def pull(source: str, literal_url: bool = False) -> tuple:
    """Download a minecraft server jar by type tag.

    A .jar-file is determined by the type tag and saved to disk.

    Arguments:
        source (str): The type tag of a server or a URL.

    Keyword Arguments:
        literal_url (bool): Specifies if the source variable contains an URL or a type tag. (default: {False})

    Returns:
        Path: The path of the saved .jar-file.
    """
    url = None
    if literal_url:
        url = source
        # Generate artificial Version Tag
        url_hash = hashlib.sha1(url.encode()).hexdigest()
        tag = f"other:{url_hash[:16]}"
    else:
        try:
            url, tag = get_download_url(source)
        except LookupError:
            print("Resolving Tag failed, looking in local cache...")
            tag = source

    print(f"Pulling version '{tag}'...")
    dest = storage.get_jar_path(tag)

    if not dest.is_file():
        if url:
            storage.create_dirs(dest.parent)
            download(url, dest)
        else:
            raise FileNotFoundError("No matching File found in local cache.")
    else:
        print("Already cached, no download required.")

    return dest, tag
