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

import re
import sys
import inspect
import argparse as ap
from typing import Callable
from mcctl.__config__ import write_cfg
from mcctl import proc, storage, service, web, common, CFGVARS


def get_permlevel(args: ap.Namespace) -> dict:
    """Determine the Permission Level by arguments. Returns the User with sufficient Permissions.

    Args:
        args (Namespace): Parsed Parameters.

    Returns:
        dict: The Name of the User with sufficient permissions for the Action,
              and if no further demotion is needed.
    """
    root_cmds = {
        'create': ('start',),
        'config': ('restart',),
        'update': ('restart',),
        'export': None,
        'restart': None,
        'start': None,
        'stop': None
    }

    perms = {
        'user': CFGVARS.get('system', 'server_user'),
        'needs_demote': False
    }

    if args.action in root_cmds.keys():
        triggerargs = root_cmds.get(args.action)
        dictargs = vars(args)
        if triggerargs is None:
            perms['user'] = 'root'
        else:
            for arg in triggerargs:
                if dictargs.get(arg):
                    perms['needs_demote'] = True
                    perms['user'] = 'root'
                    break

    return perms


def filter_args(unfiltered_kwargs: dict, func: Callable) -> dict:
    """Filter Keyword Arguments for a function that does not accept some.

    Args:
        unfiltered_kwargs (dict): Keyword Arguments which could cause unexpected Keywords.
        func (function): The function that should accept the Keyword Arguments.

    Returns:
        dict: A dictionary containing all Arguments safe for the supplied function.
    """
    sig = inspect.signature(func)
    filter_keys = [param.name for param in sig.parameters.values()
                   if param.kind == param.POSITIONAL_OR_KEYWORD]
    filtered_dict = {filter_key: unfiltered_kwargs.get(filter_key)
                     for filter_key in filter_keys
                     if unfiltered_kwargs.get(filter_key) is not None}

    return filtered_dict


def get_parser() -> ap.ArgumentParser:
    """Parse Arguments from the Command Line input and returns the converted Values.

    Returns:
        argparse.Namespace: All Arguments, parsed.

    Raises:
        argparse.ArgumentTypeError: Raised when the parameters given cannot be parsed correctly.
    """
    def check_type_id(value: str) -> str:
        test_type_id = re.compile(
            r'(.+:)+.+|https?: \/\/(-\.)?([ ^\s /?\.#-]+\.?)+(/[^\s]*)?$')
        if not test_type_id.search(value):
            raise ap.ArgumentTypeError(
                "must be in the form '<TYPE>:<VERSION>:<BUILD>' or URL.")
        return value

    def check_strict_type_id(value: str) -> str:
        test_type_id = re.compile(r'(.+:)+.+|all')
        if not test_type_id.search(value):
            raise ap.ArgumentTypeError(
                "must be in the form '<TYPE>:<VERSION>:<BUILD>' or 'all'.")
        return value

    def check_mem(value: str) -> str:
        test_mem = re.compile(r'^[0-9]+[KMG]$')
        if not test_mem.search(value):
            raise ap.ArgumentTypeError("Must be in Format <NUMBER>{K,M,G}.")
        return value

    action_instance_template = "{args.action} instance '{args.instance}'"

    parser = ap.ArgumentParser("mcctl", description="Manage, configure, create multiple Minecraft servers in a docker-like fashion.",
                               formatter_class=ap.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="Enable verbose/debugging output.")

    subparsers = parser.add_subparsers(title="actions", dest="action")
    subparsers.required = True

    type_id_parser = ap.ArgumentParser(
        add_help=False, formatter_class=ap.RawTextHelpFormatter)
    type_id_parser.add_argument(
        "-u", "--url", dest="literal_url", action='store_true', help="Treat the TypeID Value as a URL.")
    type_id_parser.add_argument(
        "source", metavar="TYPEID_OR_URL", type=check_type_id,
        help=("Type ID in '<TYPE>:<VERSION>:<BUILD>' format.\n"
              "'<TYPE>:latest' or '<TYPE>:latest-snap' are also allowed.\n"
              "Types: 'paper', 'spigot', 'vanilla'\n"
              "Versions: e.g. '1.15.2', 'latest'\n"
              "Build (only for paper): e.g. '122', 'latest'\n"))

    instance_name_parser = ap.ArgumentParser(add_help=False)
    instance_name_parser.add_argument(
        "instance", metavar="INSTANCE_ID", help="Instance Name of the Minecraft Server.")
    # Optional Instance Name
    instance_subfolder_parser = ap.ArgumentParser(add_help=False)
    instance_subfolder_parser.add_argument(
        "instance_subfolder", metavar="INSTANCE/SUBFOLDER", nargs="?", help="Instance Name or Subpath in Instance Files, e.g. INSTANCE/world.")

    message_parser = ap.ArgumentParser(add_help=False)
    message_parser.add_argument(
        "-m", "--message", help="Reason for the restart/stop. Informs the Players on the Server.")

    restart_parser = ap.ArgumentParser(add_help=False)
    restart_parser.add_argument(
        "-r", "--restart", action='store_true', help="Stop the Server, apply config changes, and start it again.")

    parser_attach = subparsers.add_parser(
        "attach", parents=[instance_name_parser], help="Attach to the Console of the Minecraft Instance.")
    parser_attach.set_defaults(
        func=proc.attach, err_template="attach to '{args.instance}'")

    parser_config = subparsers.add_parser(
        "config", parents=[instance_name_parser, restart_parser], help="Configure Files of a Minecraft Server Instance.")
    parser_config.add_argument(
        "-e", "--edit", dest="edit_paths", metavar="FILE", help="Edit a File in the Instance Folder interactively.")
    parser_config.add_argument(
        "-p", "--properties", nargs="+", help="Change server.properties options, e.g. server-port=25567 'motd=My new and cool Server'.")
    parser_config.set_defaults(
        func=common.configure, err_template="configure '{args.instance}'", editor=CFGVARS.get('user', 'editor'))

    parser_create = subparsers.add_parser(
        "create", parents=[instance_name_parser, type_id_parser], help="Create a new Server Instance.", formatter_class=ap.RawTextHelpFormatter)
    parser_create.add_argument(
        "-s", "--start", action='store_true', help="Start the Server after creation, persistent enabled.")
    parser_create.add_argument(
        "-m", "--memory", type=check_mem, help="Memory Allocation for the Server in {K,M,G}Bytes, e.g. 2G, 1024M.")
    parser_create.add_argument(
        "-p", "--properties", nargs="+", help="server.properties options in 'KEY1=VALUE1 KEY2=VALUE2' Format.")
    parser_create.set_defaults(
        func=common.create, err_template=action_instance_template)

    parser_exec = subparsers.add_parser(
        "exec", parents=[instance_name_parser], help="Execute a command in the Console of the Instance.")
    parser_exec.add_argument("command", nargs="+",
                             help="Command to execute in the Server Console.")
    parser_exec.set_defaults(
        func=proc.mc_exec, err_template=action_instance_template)

    parser_export = subparsers.add_parser(
        "export", parents=[instance_name_parser], help="Export an Instance to a zip File.")
    parser_export.add_argument(
        "-c", "--compress", action='store_true', help="Compress the Archive.")
    parser_export.add_argument(
        "-w", "--world-only", action='store_true', help="Only export World Data.")
    parser_export.set_defaults(
        func=storage.export, err_template=action_instance_template)

    parser_inspect = subparsers.add_parser(
        "inspect", parents=[instance_name_parser], help="Inspect the Log of a Server.")
    parser_inspect.add_argument(
        "-n", "--lines", dest="limit", type=int, default=0, help="Limit the line output count to n.")
    parser_inspect.set_defaults(
        func=storage.inspect, err_template="{args.action} logs of '{args.instance}'")

    parser_list = subparsers.add_parser(
        "ls", help="List Instances, installed Versions, etc.")
    parser_list.add_argument("what", metavar="WHAT", nargs="?", choices=[
        "instances", "jars"], default="instances", help="What Type (instnaces/jars) return.")
    parser_list.add_argument("-f", "--filter", dest="filter_str",
                             default='', help="Filter by Version or Instance Name, etc.")
    parser_list.set_defaults(
        func=common.mc_ls, err_template="list {args.what}")

    parser_pull = subparsers.add_parser(
        "pull", parents=[type_id_parser], help="Pull a Server .jar-File from the Internet.")
    parser_pull.set_defaults(
        func=web.pull, err_template="{args.action} {args.source}")

    parser_rename = subparsers.add_parser(
        "rename", parents=[instance_name_parser], help="Rename a Server Instance.")
    parser_rename.add_argument(
        "new_name", metavar="NEW_NAME", help="The new Name of the Server Instance.")
    parser_rename.set_defaults(
        func=common.rename, err_template=action_instance_template)

    parser_restart = subparsers.add_parser(
        "restart", parents=[instance_name_parser, message_parser], help="Restart a Server Instance.")
    parser_restart.set_defaults(
        func=service.notified_set_status, err_template=action_instance_template)

    parser_remove = subparsers.add_parser(
        "rm", parents=[instance_name_parser], help="Remove a Server Instance.")
    parser_remove.set_defaults(
        func=storage.remove, err_template="remove '{args.instance}'")

    parser_remove_jar = subparsers.add_parser(
        "rmj", help="Remove a cached Server Binary.")
    parser_remove_jar.add_argument(
        "source", metavar="TYPEID", type=check_strict_type_id,
        help=("Type ID in '<TYPE>:<VERSION>:<BUILD>' format.\n"
              "'<TYPE>:latest' or '<TYPE>:latest-snap' are NOT allowed.\n"
              "'all' removes all cached Files.\n"))
    parser_remove_jar.set_defaults(
        func=storage.remove_jar, err_template="remove .jar File '{args.source}'")

    parser_start = subparsers.add_parser(
        "start", parents=[instance_name_parser], help="Start a Server Instance.")
    parser_start.add_argument("-p", "--persistent", action='store_true',
                              help="Start even after Reboot.")
    parser_start.set_defaults(
        func=service.notified_set_status, err_template=action_instance_template)

    parser_stop = subparsers.add_parser(
        "stop", parents=[instance_name_parser, message_parser], help="Stop a Server Instance.")
    parser_stop.add_argument("-p", "--persistent", action='store_true',
                             help="Do not start again after Reboot.")
    parser_stop.set_defaults(
        func=service.notified_set_status, err_template=action_instance_template)

    parser_update = subparsers.add_parser(
        "update", parents=[instance_name_parser, type_id_parser, restart_parser], help="Update a Server Instance.")
    parser_update.set_defaults(
        func=common.update, err_template=action_instance_template)

    parser_shell = subparsers.add_parser(
        "shell", parents=[instance_subfolder_parser], help="Use a Shell to interactively edit a Server Instance.")
    parser_shell.set_defaults(func=proc.shell, err_template="invoke a Shell",
                              shell_path=CFGVARS.get('user', 'shell'))

    return parser


def main():
    """Start mcctl.

    This function handles all arguments, elevation and parameters for functions.
    The logic is moved into the other files as much as possible.
    """
    # Determine needed Permission Level and restart with sudo.
    args = get_parser().parse_args()
    plvl = get_permlevel(args)

    try:
        proc.elevate(plvl.get('user'))
        if plvl.get('needs_demote'):
            user = CFGVARS.get('system', 'server_user')
            user_ids = proc.get_ids(user)
            proc.run_as(*user_ids)
    except (KeyError, OSError) as ex:
        if args.verbose:
            raise
        print(f"Process Elevation failed: {ex}")
        sys.exit(1)

    # Write Config if the Package is not imported.
    write_cfg()

    safe_kwargs = filter_args(vars(args), args.func)

    try:
        args.func(**safe_kwargs)
    except Exception as ex:  # pylint: disable=broad-except
        if args.verbose:
            raise
        err_msg = args.err_template.format(args=args)
        print(f"Unable to {err_msg}: {ex}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted by User")
        sys.exit(130)


if __name__ == "__main__":
    main()
