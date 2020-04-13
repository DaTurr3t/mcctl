#!/bin/env python3

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

import os
import re
import argparse as ap
from mcctl import proc, storage, service, web, config, common, settings


def comingSoon():
    """Returns an info to the user that command X is not correctly implemented yet.
    """

    print("Not yet implemented!")


def main():
    """The main function of mcctl.

    This function handles all arguments. The logic is moved into the other files as much as possible, except for input checking.

    Raises:
        ap.ArgumentTypeError: Raised when the parameters given cannot be parsed correctly.
    """

    def typeID(value):
        testTypeID = re.compile(
            r'(.+:)+.+|https?: \/\/(-\.)?([ ^\s /?\.#-]+\.?)+(/[^\s]*)?$')
        if testTypeID.search(value) is None:
            raise ap.ArgumentTypeError(
                "must be in the form '<TYPE>:<VERSION>:<BUILD>' or URL")
        return value

    def mem(value):
        testMem = re.compile(r'^[0-9]+[KMG]$')
        if testMem.search(value) is None:
            raise ap.ArgumentTypeError("Must be in Format <NUMBER>{K,M,G}")
        return value

    parser = ap.ArgumentParser("mcctl", description="Management Utility for Minecraft Server Instances",
                               formatter_class=ap.ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers(
        title="actions", dest="action")
    subparsers.required = True

    instanceNameParser = ap.ArgumentParser(add_help=False)
    instanceNameParser.add_argument("instance", metavar="INSTANCE_ID",
                                    help="Instance Name of the Minecraft Server")

    parserAttach = subparsers.add_parser(
        "attach", parents=[instanceNameParser], help="Attach to the Console of the Instance")

    parserCreate = subparsers.add_parser(
        "create", parents=[instanceNameParser], help="Add a new Minecraft Server Instance", formatter_class=ap.RawTextHelpFormatter)
    parserCreate.add_argument(
        "-u" "--url", action='store_true', help="Use URL instead of TypeID.")
    parserCreate.add_argument(
        "source", metavar="TYPEID_OR_URL", type=typeID,
        help="Type ID in '<TYPE>:<VERSION>:<BUILD>' format. '<TYPE>:latest' or '<TYPE>:latest-snap' are also allowed.\nTypes: 'paper', 'vanilla'\nVersions: e.g. '1.15.2', 'latest'\nBuild (only for paper): e.g. '122', 'latest'")
    parserCreate.add_argument(
        "-m", "--memory", type=mem, help="Memory Allocation for the Server in {K,M,G}Bytes, e.g. 2G, 1024M")
    parserCreate.add_argument(
        "-p", "--properties", nargs="+", help="server.properties options in 'KEY1=VALUE1 KEY2=VALUE2' Format")

    parserRemove = subparsers.add_parser(
        "rm", parents=[instanceNameParser], help="Remove an Instance or Server Version.")

    parserExec = subparsers.add_parser(
        "exec", parents=[instanceNameParser], help="Execute a command in the Console of the Instance")
    parserExec.add_argument("command", metavar="COMMAND", nargs="+",
                            help="Command to execute")

    parserExport = subparsers.add_parser(
        "export", parents=[instanceNameParser], help="Export an Instance to a zip File.")
    parserExport.add_argument(
        "-c", "--compress", action='store_true', help="Compress the Archive.")
    parserExport.add_argument(
        "-w", "--world-only", action='store_true', help="Only export World Data")

    parserList = subparsers.add_parser(
        "ls", help="List Instances, installed Versions, etc.")
    parserList.add_argument("what", metavar="WHAT",  nargs="?", choices=[
                            "instances", "jars"], default="instances")
    parserList.add_argument("-f", "--filter",  default='')

    parserPull = subparsers.add_parser(
        "pull", help="Pull a Minecraft Server Binary from the Internet", formatter_class=ap.RawTextHelpFormatter)
    parserPull.add_argument(
        "--url", "-u", action='store_true', help="Pull a Minecraft Server from a direct URL instead of Type ID")
    parserPull.add_argument("source", metavar="TYPEID_OR_URL", type=typeID,
                            help="Type ID in '<TYPE>:<VERSION>:<BUILD>' format. '<TYPE>:latest' or '<TYPE>:latest-snap' are also allowed.\nTypes: 'paper', 'vanilla'\nVersions: e.g. '1.15.2', 'latest'\nBuild (only for paper): e.g. '122', 'latest'")

    parserRename = subparsers.add_parser(
        "rename", parents=[instanceNameParser], help="Rename a Minecraft Server Instance")
    parserRename.add_argument("newName", metavar="NEW_NAME")

    parserRestart = subparsers.add_parser(
        "restart", parents=[instanceNameParser], help="Restart a Minecraft Server Instance")

    parserStart = subparsers.add_parser(
        "start", parents=[instanceNameParser], help="Start a Minecraft Server Instance")
    parserStart.add_argument("-p", "--persistent", action='store_true',
                             help="Start even after Reboot")

    parserStop = subparsers.add_parser(
        "stop", parents=[instanceNameParser], help="Stop a Minecraft Server Instance")
    parserStop.add_argument("-p", "--persistent", action='store_true',
                            help="Do not start again after Reboot")

    # parser.add_argument("-v", help="Verbose Output", action="count", default=0)

    args = parser.parse_args()

    # TODO
    # Update command

    if os.geteuid() != 0:
        print("Must be root.")
        exit(1)

    if not args.action in ["start", "stop", "restart", "export"]:
        user = settings.cfgDict['server_user']
        proc.demote(user)

    if args.action == 'create':
        try:
            common.create(args.instance, args.source,
                          args.memory, args.properties)
        except Exception as e:
            print("Unable to create instance '{0}': {1}".format(
                args.instance, e))

    elif args.action == 'rm':
        try:
            storage.remove(args.instance)
        except Exception as e:
            print("Unable to remove instance '{0}': {1}".format(
                args.instance, e))

    elif args.action == 'export':
        dest = storage.export(
            args.instance, compress=args.compress, worldOnly=args.world_only)
        storage.chown(dest, os.getlogin())
        print("Archive saved in '{}'".format(dest))

    elif args.action == 'pull':
        try:
            web.pull(args.source, args.url)
        except Exception as e:
            print("Unable to pull '{0}': {1}".format(args.source, e))

    elif args.action == 'ls':
        if args.what == 'instances':
            common.getInstanceList(args.filter)
        elif args.what == 'jars':
            storage.getJarList(args.filter)

    elif args.action == 'start':
        if args.persistent:
            service.setStatus(args.instance, "enable")
        try:
            service.setStatus(args.instance, args.action)
        except AssertionError:
            print(e)

    elif args.action == 'stop':
        if args.persistent:
            service.setStatus(args.instance, "disable")
        try:
            service.setStatus(args.instance, args.action)
        except AssertionError:
            print(e)

    elif args.action == 'restart':
        try:
            service.setStatus(args.instance, args.action)
        except AssertionError:
            print(e)

    elif args.action == 'attach':
        try:
            proc.attach(args.instance)
        except AssertionError as e:
            print("Unable to attach to '{0}': {1}".format(
                args.instance, e))

    elif args.action == 'exec':
        try:
            proc.exec(args.instance, args.command)
        except AssertionError as e:
            print("Unable to pass command to '{0}': {1}".format(
                args.instance, e))

    elif args.action == 'rename':
        try:
            common.rename(args.instance, args.newName)
        except (AssertionError, FileExistsError, FileNotFoundError) as e:
            print("Unable to rename '{0}': {1}".format(
                args.instance, str(e).split(":")[0]))

    else:
        comingSoon()


if __name__ == "__main__":
    main()
