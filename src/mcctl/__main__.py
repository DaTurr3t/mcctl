#!/bin/env python3

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

import argparse as ap
from pathlib import Path
from modules import interact, storage, service, web


def create():
    pass


def comingSoon():
    print("Not yet implemented!")


if __name__ == "__main__":
    versionDataUrl = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

    parser = ap.ArgumentParser(
        description="Management Utility for Minecraft Server Instances", formatter_class=ap.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(
        title="actions", help="Action to Execute on a Minecraft Server Instance", dest="action")

    parserAttach = subparsers.add_parser(
        "attach", description="Attach to the Console of the Instance")

    parserCreate = subparsers.add_parser(
        "create", description="Add a new Minecraft Server Instance")
    parserCreate.add_argument(
        "--properties", help="server.properties options in KEY1=VALUE1,KEY2=VALUE2 form")
    parserCreate.add_argument(
        "--jvm-args", help="Values for the jvm-env File. Accepted are 'MEM' and 'JARFILE' in KEY1=VALUE1,KEY2=VALUE2 form")

    parserDelete = subparsers.add_parser(
        "delete", description="Delete an Instance or Server Version.")

    parserExec = subparsers.add_parser(
        "exec", description="Execute a command in the Console of the Instance")
    parserExec.add_argument("command", metavar="COMMAND",
                            help="Command to execute", nargs=ap.REMAINDER)

    parserExport = subparsers.add_parser("export", help="Export an Instance.")
    parserExport.add_argument("--world-only", help="Only export World Data")

    parserList = subparsers.add_parser(
        "list", description="List Instances, installed Versions, etc.")

    parserPull = subparsers.add_parser(
        "pull", description="Pull a Minecraft Server Binary from the Internet", formatter_class=ap.RawTextHelpFormatter)
    parserPull.add_argument(
        "--url", action='store_true', help="Pull a Minecraft Server from a direct URL instead of Type ID")
    parserPull.add_argument("source", metavar="TYPEID_OR_URL",
                            help="Type ID in '<TYPE>:<VERSION>:<BUILD>' format. '<TYPE>:latest' or '<TYPE>:latest-snap' are also allowed.\nTypes: 'paper', 'vanilla'\nVersions: e.g. '1.15.2', 'latest'\nBuild (only for paper): e.g. '122', 'latest'")

    parserRename = subparsers.add_parser(
        "rename", description="Rename a Minecraft Server Instance")
    parserRename.add_argument("newName", metavar="NEW_NAME")

    parserRestart = subparsers.add_parser(
        "restart", description="Restart a Minecraft Server Instance")

    parserStart = subparsers.add_parser(
        "start", description="Start a Minecraft Server> Instance")
    parserStart.add_argument("--persistent", help="Start even after Reboot")

    parserStop = subparsers.add_parser(
        "stop", description="Stop a Minecraft Server Instance")
    parserStop.add_argument("--persistent", help="Stop even after Reboot")

    parser.add_argument("instance", metavar="INSTANCE_ID",
                        help="Instance Name of the Minecraft Server")

    #parser.add_argument("-v", help="Verbose Output", action="count", default=0)

    args = parser.parse_args()

    # TODO
    # Create new instances
    # download versions
    # Stop/Start/restart
    # Push commands to Screeen
    # Update command

if args.action == 'create':
    comingSoon()
elif args.action == 'delete':
    storage.delete(args.instance)

elif args.action == 'export':
    storage.export(args.instance)

elif args.action == 'pull':
    destPath = web.pull(args.source, args.url)
    print("Done.")

elif args.action == 'list':
    service.getInstanceList(args.instance)

elif args.action == 'start':
    if args.persistent:
        service.setStatus(args.instance, "enable")
    service.setStatus(args.instance, args.action)

elif args.action == 'stop':
    if args.persistent:
        service.setStatus(args.instance, "disable")
    service.setStatus(args.instance, args.action)

elif args.action == 'restart':
    service.setStatus(args.instance, args.action)

elif args.action == 'attach':
    interact.attach(args.instance)

elif args.action == 'exec':
    interact.exec(args.instance, args.command)

elif args.action == 'rename':
    storage.rename(args.instance, args.newName)

else:
    comingSoon()
