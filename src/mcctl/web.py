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

import urllib.request as req
from pathlib import Path
import json
import hashlib
from mcctl import visuals, storage

DOWNLOAD_URLS = {
    "vanilla": "https://launchermeta.mojang.com/mc/game/version_manifest.json",
    "paper": "https://papermc.io/api/v1/paper"
}


def rest_get(url: str) -> dict:
    """Send a get request and parse response form JSON.

    A HTTP GET request is sent to the specified URL. The response is parsed into a dict.

    Arguments:
        url {str} -- The target to query

    Returns:
        dict -- Deserialized JSON Data
    """

    header = {'User-Agent': 'curl/7.4'}
    request = req.Request(url=url, headers=header)
    with req.urlopen(request, timeout=5) as response:
        data = response.read()
    return json.loads(data)


def download(url: str, dest: Path) -> tuple:
    """Download a file with progress report.

    A file is downloaded from a webserver, progress is shown via the reporthook-Parameter.

    Arguments:
        url {str} -- The target to query
        dest {Path} -- The path where to save the recieved file to

    Returns:
        tuple -- data about the downloaded file, from urllib.urlretrieve()
    """

    store_data = req.urlretrieve(url, dest, reporthook)
    print()
    return store_data


def reporthook(blockcount: int, blocksize: int, total: int):
    """Print Progress

    Output the progress of the download given blockcount, blocksize and total bytes.

    Arguments:
        blockcount {int} -- The number of the recieved block.
        blocksize {int} -- The size of the recieved blocks.
        total {int} -- The size of the complete File.
    """

    current = blockcount * blocksize
    if total > 0:
        percent = current * 100 / total
        out = "\r%s %3.0f%% %*dkB / %dkB" % (
            visuals.spinner(int(percent), 1), percent, len(str(total//1024)), current/1024, total/1024)
    else:
        out = "\r%s %dkB / %skB" % (visuals.spinner(blockcount),
                                    current/1024, "???")
    print(out, end="")


def join_url(base: str, *parts: str) -> str:
    """Join an URL and its segments.

    Arguments:
        base {str} -- The base of the url, containing the protocol and hostname.
        *parts {str} -- The path parts of the URL.

    Returns:
        str -- The complete, joined URL
    """

    path = "/".join(list([x.strip("/") for x in parts]))
    return "{}/{}".format(base.rstrip("/"), path)


def get_vanilla_download_url(version_tag: str, manifest_url: str = DOWNLOAD_URLS['vanilla']) -> tuple:
    """Get the download URL of a vanilla server

    Find the download URL of a vanilla server using Mojangs Launcher-Meta API.

    Keyword Arguments:
        manifest_url {str} -- The URL of version_manifest.json (default: {downloadUrls['vanilla']})
        version_tag {str} -- The Tag of the server without the type (vanilla/paper).

    Returns:
        tuple -- A tuple with the download URL and the complete, resolved Tag
    """

    version_manifest = rest_get(manifest_url)
    if version_tag == "latest":
        version_tag = version_manifest["latest"]["release"]
    elif version_tag == "latest-snap":
        version_tag = version_manifest["latest"]["snapshot"]

    for version in version_manifest["versions"]:
        if version["id"] == version_tag:
            download_url = version["url"]
            break
    version_data = rest_get(download_url)
    resolved_tag = "vanilla:{}".format(version_tag)
    return version_data["downloads"]["server"]["url"], resolved_tag


def get_paper_download_url(version_tag: str, base_url: str = DOWNLOAD_URLS['paper']) -> tuple:
    """Get the download URL of a paper server

    Find the download URL of a paper server using PaperMCs Version API.

    Arguments:
        version_tag {str} -- The Tag of the server without the type (vanilla/paper).

    Keyword Arguments:
        base_url {str} --  The API URL for paper. (default: {downloadUrls['vanilla']})

    Returns:
        tuple -- A tuple with the download URL and the complete, resolved Tag
    """

    if version_tag == "latest":
        versions = rest_get(base_url)
        major = versions["versions"][0]
        minor = version_tag
    else:
        major, minor = version_tag.split(":", 1)
    test_url = join_url(base_url, major, minor)
    try:
        resolved_data = rest_get(test_url)
        resolved_tag = ":".join(list(resolved_data.values()))
    except Exception as ex:
        raise ValueError(
            "Server version not found for type 'paper'", version_tag, str(ex))
    return join_url(test_url, "download"), resolved_tag


def get_download_url(server_tag: str) -> tuple:
    """Get the download URL of any minecraft server

    Arguments:
        server_tag {str} -- The Tag of the server (e.g. vanilla:latest).

    Raises:
        Exception: If an unsupported Server type is used, an Exception is raised.

    Returns:
        tuple -- A tuple with the download URL and the complete, resolved Tag
    """

    assert ":" in server_tag, "Invalid Server Tag '{}'".format(server_tag)
    type_tag, version_tag = server_tag.split(":", 1)
    if type_tag == "paper":
        url, resolved_tag = get_paper_download_url(version_tag)
    elif type_tag == "vanilla":
        url, resolved_tag = get_vanilla_download_url(version_tag)
    else:
        raise ValueError("Unsupported server type: '{}'".format(type_tag))
    return url, resolved_tag


def pull(source: str, literal_url: bool = False) -> Path:
    """Download a minecraft server jar by type tag

    A .jar-file is determined by the type tag and saved to disk.

    Arguments:
        source {str} -- The type tag of a server or a URL.

    Keyword Arguments:
        literal_url {bool} -- Specifies if the source variable contains an URL or a type tag. (default: {False})

    Returns:
        Path -- The path of the saved .jar-file.
    """

    base_dest = storage.get_home_path() / "jars"
    if literal_url:
        url = source
        # Generate artificial Version Tag
        url_hash = hashlib.sha1(url.encode()).hexdigest()
        tag = "other/{}".format(url_hash[:12])
    else:
        url, tag = get_download_url(source)

    print("Pulling version '{}'".format(tag))
    dest = base_dest / "{}.jar".format(tag.replace(":", "/"))

    if not dest.is_file():
        storage.create_dirs(dest.parent)
        download(url, dest)
    else:
        print("Already cached, no download required.")

    return dest, tag
 