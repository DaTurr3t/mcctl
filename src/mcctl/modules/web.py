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
from modules import visuals, storage

downloadUrls = {
    "vanilla": "https://launchermeta.mojang.com/mc/game/version_manifest.json",
    "paper": "https://papermc.io/api/v1/paper"
}


def restGet(url: str) -> dict:
    header = {'User-Agent': 'curl/7.4'}
    request = req.Request(url=url, headers=header)
    with req.urlopen(request, timeout=5) as response:
        data = response.read()
    return json.loads(data)


def download(url: str, dest: Path) -> tuple:
    storeData = req.urlretrieve(url, dest, reporthook)
    print()
    return storeData


def reporthook(blockcount: int, blocksize: int, total):
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
    path = "/".join(list([x.strip("/") for x in parts]))
    return "{}/{}".format(base.rstrip("/"), path)


def getVanillaDownloadUrl(manifestUrl: str, versionTag: str) -> tuple:
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


def getPaperDownloadUrl(baseUrl: str, versionTag: str) -> tuple:
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
    assert ":" in serverTag, "Invalid Server Tag '{}'".format(serverTag)
    global downloadUrls
    typeTag, versionTag = serverTag.split(":", 1)
    if typeTag == "paper":
        url, resolvedTag = getPaperDownloadUrl(
            downloadUrls[typeTag], versionTag)
    elif typeTag == "vanilla":
        url, resolvedTag = getVanillaDownloadUrl(
            downloadUrls[typeTag], versionTag)
    else:
        raise Exception("Unsupported server type: '{}'".format(typeTag))
    return url, resolvedTag


def pull(source: str, literalUrl: bool=False) -> Path:
    baseDest = storage.getHomePath() / "jars"
    if literalUrl:
        url = source

        print("Pulling from '{}'".format(url))
        # Generating artificial Version Tag
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
