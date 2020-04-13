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

downloadUrls = {
    "vanilla": "https://launchermeta.mojang.com/mc/game/version_manifest.json",
    "paper": "https://papermc.io/api/v1/paper"
}


def restGet(url: str) -> dict:
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

    storeData = req.urlretrieve(url, dest, reporthook)
    print()
    return storeData


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
        s = "\r%s %3.0f%% %*dkB / %dkB" % (
            visuals.spinner(int(percent), 1), percent, len(str(total//1024)), current/1024, total/1024)
    else:
        s = "\r%s %dkB / %skB" % (visuals.spinner(blockcount),
                                  current/1024, "???")
    print(s, end="")


def joinUrl(base: str, *parts: str) -> str:
    """Join an URL and its segments.

    Arguments:
        base {str} -- The base of the url, containing the protocol and hostname.
        *parts {str} -- The path parts of the URL.

    Returns:
        str -- The complete, joined URL
    """

    path = "/".join(list([x.strip("/") for x in parts]))
    return "{}/{}".format(base.rstrip("/"), path)


def getVanillaDownloadUrl(versionTag: str, manifestUrl: str = downloadUrls['vanilla']) -> tuple:
    """Get the download URL of a vanilla server

    Find the download URL of a vanilla server using Mojangs Launcher-Meta API.

    Arguments:
        manifestUrl {str} -- The URL of version_manifest.json

    Keyword Arguments:
        manifestUrl {str} -- The URL of version_manifest.json (default: {downloadUrls['vanilla']})

    Returns:
        tuple -- A tuple with the download URL and the complete, resolved Tag
    """

    versionManifest = restGet(manifestUrl)
    if versionTag == "latest":
        versionTag = versionManifest["latest"]["release"]
    elif versionTag == "latest-snap":
        versionTag = versionManifest["latest"]["snapshot"]

    for version in versionManifest["versions"]:
        if version["id"] == versionTag:
            downloadUrl = version["url"]
            break
    versionData = restGet(downloadUrl)
    resolvedTag = "vanilla:{}".format(versionTag)
    return versionData["downloads"]["server"]["url"], resolvedTag


def getPaperDownloadUrl(versionTag: str, baseUrl: str = downloadUrls['paper']) -> tuple:
    """Get the download URL of a paper server

    Find the download URL of a paper server using PaperMCs Version API.

    Arguments:
        baseUrl {str} -- The API URL for paper.
        versionTag {str} -- The Tag of the server without the type (vanilla/paper).

    Keyword Arguments:
        baseUrl {str} --  The API URL for paper. (default: {downloadUrls['vanilla']})

    Returns:
        tuple -- A tuple with the download URL and the complete, resolved Tag
    """

    if versionTag == "latest":
        versions = restGet(baseUrl)
        major = versions["versions"][0]
        minor = versionTag
    else:
        major, minor = versionTag.split(":", 1)
    testUrl = joinUrl(baseUrl, major, minor)
    try:
        resolvedData = restGet(testUrl)
        resolvedTag = ":".join(list(resolvedData.values()))
    except Exception as e:
        raise Exception(
            "Server version not found for type 'paper'", versionTag, str(e))
    return joinUrl(testUrl, "download"), resolvedTag


def getDownloadUrl(serverTag: str) -> tuple:
    """Get the download URL of any minecraft server

    Arguments:
        serverTag {str} -- The Tag of the server (e.g. vanilla:latest).

    Raises:
        Exception: If an unsupported Server type is used, an Exception is raised.

    Returns:
        tuple -- A tuple with the download URL and the complete, resolved Tag
    """

    assert ":" in serverTag, "Invalid Server Tag '{}'".format(serverTag)
    global downloadUrls
    typeTag, versionTag = serverTag.split(":", 1)
    if typeTag == "paper":
        url, resolvedTag = getPaperDownloadUrl(versionTag)
    elif typeTag == "vanilla":
        url, resolvedTag = getVanillaDownloadUrl(versionTag)
    else:
        raise Exception("Unsupported server type: '{}'".format(typeTag))
    return url, resolvedTag


def pull(source: str, literalUrl: bool = False) -> Path:
    """Download a minecraft server jar by type tag

    A .jar-file is determined by the type tag and saved to disk.

    Arguments:
        source {str} -- The type tag of a server or a URL.

    Keyword Arguments:
        literalUrl {bool} -- Specifies if the source variable contains an URL or a type tag. (default: {False})

    Returns:
        Path -- The path of the saved .jar-file.
    """

    baseDest = storage.getHomePath() / "jars"
    if literalUrl:
        url = source
        # Generate artificial Version Tag
        hash = hashlib.sha1(url.encode()).hexdigest()
        tag = "other/{}".format(hash[:12])
    else:
        url, tag = getDownloadUrl(source)

    print("Pulling version '{}'".format(tag))
    dest = baseDest / "{}.jar".format(tag.replace(":", "/"))

    if not dest.is_file():
        storage.createDirs(dest.parent)
        download(url, dest)
    else:
        print("Already cached, no download required.")

    return dest
