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
import sys
import argparse as ap
from mcctl import proc, storage, service, web, common, settings


def coming_soon():
    """Returns an info to the user that command X is not correctly implemented yet.
    """

    print("Not yet implemented!")


def main():
    """The main function of mcctl.

    This function handles all arguments.
    The logic is moved into the other files as much as possible, except for input checking.

    Raises:
        ap.ArgumentTypeError: Raised when the parameters given cannot be parsed correctly.
    """

    def type_id(value):
        test_type_id = re.compile(
            r'(.+:)+.+|https?: \/\/(-\.)?([ ^\s /?\.#-]+\.?)+(/[^\s]*)?$')
        if test_type_id.search(value) is None:
            raise ap.ArgumentTypeError(
                "must be in the form '<TYPE>:<VERSION>:<BUILD>' or URL")
        return value

    def strict_type_id(value):
        test_type_id = re.compile(r'(.+:)+.+|all')
        if test_type_id.search(value) is None:
            raise ap.ArgumentTypeError(
                "must be in the form '<TYPE>:<VERSION>:<BUILD>' or 'all'")
        return value

    def mem(value):
        test_mem = re.compile(r'^[0-9]+[KMG]$')
        if test_mem.search(value) is None:
            raise ap.ArgumentTypeError("Must be in Format <NUMBER>{K,M,G}")
        return value

    parser = ap.ArgumentParser("mcctl", description="Management Utility for Minecraft Server Instances",
                               formatter_class=ap.ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers(title="actions", dest="action")
    subparsers.required = True

    type_id_parser = ap.ArgumentParser(
        add_help=False, formatter_class=ap.RawTextHelpFormatter)
    type_id_parser.add_argument(
        "-u", "--url", action='store_true', help="Use URL instead of TypeID.")
    type_id_parser.add_argument(
        "source", metavar="TYPEID_OR_URL", type=type_id,
        help=("Type ID in '<TYPE>:<VERSION>:<BUILD>' format.\n"
              "'<TYPE>:latest' or '<TYPE>:latest-snap' are also allowed.\n"
              "Types: 'paper', 'vanilla'\n"
              "Versions: e.g. '1.15.2', 'latest'\n"
              "Build (only for paper): e.g. '122', 'latest'\n"))

    instance_name_parser = ap.ArgumentParser(add_help=False)
    instance_name_parser.add_argument(
        "instance", metavar="INSTANCE_ID", help="Instance Name of the Minecraft Server")

    reason_parser = ap.ArgumentParser(add_help=False)
    reason_parser.add_argument(
        "reason", nargs="+", help="Reason to be appended to the 'say' Command."
    )

    parser_attach = subparsers.add_parser(
        "attach", parents=[instance_name_parser], help="Attach to the Console of the Instance")

    parser_create = subparsers.add_parser(
        "create", parents=[instance_name_parser, type_id_parser], help="Add a new Minecraft Server Instance", formatter_class=ap.RawTextHelpFormatter)
    parser_create.add_argument(
        "-s", "--start", action='store_true', help="Start the Server after creation, persistent enabled")
    parser_create.add_argument(
        "-m", "--memory", type=mem, help="Memory Allocation for the Server in {K,M,G}Bytes, e.g. 2G, 1024M")
    parser_create.add_argument(
        "-p", "--properties", nargs="+", help="server.properties options in 'KEY1=VALUE1 KEY2=VALUE2' Format")

    parser_exec = subparsers.add_parser(
        "exec", parents=[instance_name_parser], help="Execute a command in the Console of the Instance")
    parser_exec.add_argument("command", nargs="+",
                             help="Command to execute")

    parser_export = subparsers.add_parser(
        "export", parents=[instance_name_parser], help="Export an Instance to a zip File.")
    parser_export.add_argument(
        "-c", "--compress", action='store_true', help="Compress the Archive.")
    parser_export.add_argument(
        "-w", "--world-only", action='store_true', help="Only export World Data")

    parser_inspect = subparsers.add_parser(
        "inspect", parents=[instance_name_parser], help="Inspect the Log of a Server")
    parser_inspect.add_argument(
        "-n", "--lines", type=int, default=0, help="Limit the line output count to n.")

    parser_list = subparsers.add_parser(
        "ls", help="List Instances, installed Versions, etc.")
    parser_list.add_argument("what", nargs="?", choices=[
        "instances", "jars"], default="instances")
    parser_list.add_argument("-f", "--filter", default='')

    parser_pull = subparsers.add_parser(
        "pull", parents=[type_id_parser], help="Pull a Minecraft Server Binary from the Internet")

    parser_rename = subparsers.add_parser(
        "rename", parents=[instance_name_parser], help="Rename a Minecraft Server Instance")
    parser_rename.add_argument("new_name")

    parser_restart = subparsers.add_parser(
        "restart", parents=[instance_name_parser, reason_parser], help="Restart a Minecraft Server Instance")

    parser_remove = subparsers.add_parser(
        "rm", parents=[instance_name_parser], help="Remove an Instance.")

    parser_remove_jar = subparsers.add_parser(
        "rmj", help="Remove a Server Version.")
    parser_remove_jar.add_argument(
        "source", metavar="TYPEID", type=strict_type_id,
        help=("Type ID in '<TYPE>:<VERSION>:<BUILD>' format.\n"
              "'<TYPE>:latest' or '<TYPE>:latest-snap' are NOT allowed.\n"
              "'all' removes all cached Files.\n"))

    parser_start = subparsers.add_parser(
        "start", parents=[instance_name_parser], help="Start a Minecraft Server Instance")
    parser_start.add_argument("-p", "--persistent", action='store_true',
                              help="Start even after Reboot")

    parser_stop = subparsers.add_parser(
        "stop", parents=[instance_name_parser, reason_parser], help="Stop a Minecraft Server Instance")
    parser_stop.add_argument("-p", "--persistent", action='store_true',
                             help="Do not start again after Reboot")

    parser_update = subparsers.add_parser(
        "update", parents=[instance_name_parser, type_id_parser], help="Update a Minecraft Server Instance")

    args = parser.parse_args()

    if os.geteuid() != 0:
        print("Must be root.")
        sys.exit(1)

    # Starts Program as server_user
    user = settings.CFG_DICT['server_user']
    user_ids = proc.get_ids(user)
    proc.run_as(*user_ids)

    if args.action == 'create':
        try:
            common.create(args.instance, args.source,
                          args.memory, args.properties, args.start)
        except (AssertionError, FileNotFoundError, ValueError) as ex:
            print("Unable to create instance '{0}': {1}".format(
                args.instance, ex))

    elif args.action == 'rm':
        try:
            storage.remove(args.instance)
        except (FileNotFoundError, AssertionError) as ex:
            print("Unable to remove instance '{0}': {1}".format(
                args.instance, ex))

    elif args.action == 'rmj':
        try:
            storage.remove_jar(args.source)
        except (FileNotFoundError, AssertionError) as ex:
            print("Unable to remove .jar-File '{0}': {1}".format(
                args.source, ex))

    elif args.action == 'export':
        proc.run_as(0, 0)
        dest = storage.export(
            args.instance, compress=args.compress, world_only=args.world_only)
        storage.chown(dest, os.getlogin())
        print("Archive saved in '{}'".format(dest))

    elif args.action == 'pull':
        try:
            web.pull(args.source, args.url)
        except ValueError as ex:
            print("Unable to pull '{0}': {1}".format(args.source, ex))

    elif args.action == 'ls':
        if args.what == 'instances':
            common.get_instance_list(args.filter)
        elif args.what == 'jars':
            storage.get_jar_list(args.filter)

    elif args.action == 'start':
        if args.persistent:
            service.set_status(args.instance, "enable")
        try:
            service.set_status(args.instance, args.action)
        except AssertionError as ex:
            print(ex)

    elif args.action == 'stop':
        try:
            service.notified_stop(args.instance, args.reason, args.persistent)
        except AssertionError as ex:
            print(ex)

    elif args.action == 'restart':
        try:
            service.notified_stop(
                args.instance, args.reason, restart=True)
        except AssertionError as ex:
            print(ex)

    elif args.action == 'attach':
        try:
            proc.attach(args.instance)
        except AssertionError as ex:
            print("Unable to attach to '{0}': {1}".format(args.instance, ex))

    elif args.action == 'exec':
        try:
            proc.mc_exec(args.instance, args.command)
        except AssertionError as ex:
            print("Unable to pass command to '{0}': {1}".format(
                args.instance, ex))

    elif args.action == 'rename':
        try:
            common.rename(args.instance, args.new_name)
        except (AssertionError, FileExistsError) as ex:
            print("Unable to rename '{0}': {1}".format(
                args.instance, str(ex).split(":")[0]))

    elif args.action == 'update':
        try:
            common.update(args.instance, args.source)
        except (AssertionError, FileNotFoundError, ValueError) as ex:
            print("Unable to update '{0}': {1}".format(args.instance, ex))

    elif args.action == 'inspect':
        try:
            storage.inspect(args.instance, args.lines)
        except (AssertionError, OSError) as ex:
            print("Unable to inspect '{0}': {1}".format(args.instance, ex))
    else:
        coming_soon()


if __name__ == "__main__":
    main()
