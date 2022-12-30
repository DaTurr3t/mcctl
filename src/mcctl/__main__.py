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

import argparse as ap
import inspect
import re
import sys
from typing import Callable

from . import __version__, common, perms, plugin, proc, storage, web
from .__config__ import CFGVARS, LOGIN_USER, read_cfg, write_cfg


def get_permlevel(args: ap.Namespace, elevation: dict) -> dict:
    """Determine the Permission Level by arguments. Returns the User with sufficient Permissions.

    Args:
        args (Namespace): Parsed Parameters.
        elevation (dict): a dict containing the following keys:
            - default (required): The default user for which the app runs (can be "login_user", "server_user", or "root").
            - change_to: Which User to change to (can be "login_user", "server_user", or "root"). Applied if on_cond is omitted or a Condition of it was met.
            - on_cond: a dict containing "name of a parameter: desired value". At least one must apply to trigger a change_to user change.
            - change_fully: Determines if the Process is demoted internally, only applies if change_to is "root".

    Returns:
        dict: The Name of the User with sufficient permissions for the Action,
              and if no further demotion is needed.
    """
    users = {
        "login_user": LOGIN_USER,
        "server_user": CFGVARS.get('system', 'server_user'),
        "root": "root"
    }

    permissions = {"usr": users.get(elevation.get("default"))}
    conditions = elevation.get("on_cond")
    cond_match = not bool(conditions)
    if conditions:
        kwargs = vars(args)
        for key, val in conditions.items():
            if key in kwargs and kwargs[key] == val:
                cond_match = True
                break

    change_to = elevation.get("change_to")
    if cond_match and change_to:
        permissions["usr"] = users.get(change_to)
        if not elevation.get("change_fully", False):
            permissions["eusr"] = users.get(elevation.get("default"))
    return permissions


def apply_permlevel(permlevel: dict) -> None:
    """Apply Permlevel to the process, and restart the application if needed.

    Args:
        permlevel (dict): A dict containing
            - "usr": The user to elevate to via sudo.
            - "eusr" (optional): The user of which the EIDs are set.
    """
    perms.elevate(permlevel.get('usr'))
    demote_user = permlevel.get('eusr')
    if demote_user:
        user_ids = proc.get_ids(demote_user)
        perms.set_eids(*user_ids)


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

    filtered_dict = {}
    for filter_key in filter_keys:
        try:
            filtered_dict[filter_key] = unfiltered_kwargs[filter_key]
        except KeyError:
            pass

    return filtered_dict


def get_parser() -> ap.ArgumentParser:
    """Parse Arguments from the Command Line input and returns the converted Values.

    Returns:
        ArgumentParser: A parser with all arguments.

    Raises:
        argparse.ArgumentTypeError: Raised when the parameters given cannot be parsed correctly.
    """
    def check_type_id(value: str) -> str:
        if not (re.search(r'^[a-z0-9\._-]+(:[a-z0-9\._-]+){1,2}$', value) or web.is_url(value)):
            raise ap.ArgumentTypeError(
                "must be in the form '<TYPE>:<VERSION>:<BUILD>' or URL.")
        return value

    def check_strict_type_id(value: str) -> str:
        if not re.search(r'^[a-z0-9\._-]+(:[a-z0-9\._-]+){1,2}$|^all$', value):
            raise ap.ArgumentTypeError(
                "must be in the form '<TYPE>:<VERSION>:<BUILD>' or 'all'.")
        return value

    def check_mem(value: str) -> str:
        if not re.search(r'^[0-9]*[1-9]+[0-9]*[KMG]$', value):
            raise ap.ArgumentTypeError("Must be in Format <NUMBER>{K,M,G}.")
        return value

    def autocomplete_instance(value: str) -> str:
        base = storage.get_instance_path(bare=True)
        try:
            matches = [x.name for x in base.iterdir() if x.name.startswith(value)]
        except OSError:
            return value
        if len(matches) > 1:
            raise ap.ArgumentTypeError(f"Instance Name '{value}' is ambiguous.")
        elif len(matches) < 1:
            return value
        return matches[0]

    default_err_template = "{args.action} instance '{args.instance}'"
    no_elev = {"default": "server_user"}
    semi_elev = {"default": "server_user", "change_to": "root"}
    root_elev = {"default": "login_user", "change_to": "root", "change_fully": True}
    re_start_elev = {"default": "server_user",
                     "change_to": "root",
                     "on_cond": {'restart': True, 'start': True}}

    parser = ap.ArgumentParser("mcctl", description="Manage, configure, and create multiple Minecraft servers easily with a command-line interface.\n"
                               f"Version: {__version__}",
                               formatter_class=ap.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="Enable verbose/debugging output.")
    parser.set_defaults(err_template=default_err_template,
                        elevation=no_elev)

    subparsers = parser.add_subparsers(title="actions", dest="action")
    subparsers.required = True

    force_parser = ap.ArgumentParser(add_help=False)
    force_parser.add_argument("-f", "--force", action="store_true",
                              help="Proceed without a prompt.")

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

    # Auto-Completing Instance Name
    existing_instance_parser = ap.ArgumentParser(add_help=False)
    existing_instance_parser.add_argument(
        "instance", metavar="INSTANCE_ID", type=autocomplete_instance,
        help="Instance Name of the Minecraft Server.")
    # New Instance Name
    instance_parser = ap.ArgumentParser(add_help=False)
    instance_parser.add_argument(
        "instance", metavar="INSTANCE_ID",
        help="Instance Name of the Minecraft Server.")
    # Optional Instance Name
    instance_subfolder_parser = ap.ArgumentParser(add_help=False)
    instance_subfolder_parser.add_argument(
        "instance_subfolder", metavar="INSTANCE/SUBFOLDER", nargs="?", type=autocomplete_instance,
        help="Instance Name or Subpath in Instance Files, e.g. INSTANCE/world.")

    message_parser = ap.ArgumentParser(add_help=False)
    message_parser.add_argument(
        "-m", "--message", help="Reason for the restart/stop. Informs the Players on the Server.")

    restart_parser = ap.ArgumentParser(add_help=False)
    restart_parser.add_argument(
        "-r", "--restart", action='store_true', help="Stop the Server, apply config changes, and start it again.")

    memory_parser = ap.ArgumentParser(add_help=False)
    memory_parser.add_argument(
        "-m", "--memory", type=check_mem, help="Memory Allocation for the Server in {K,M,G}Bytes, e.g. 2G, 1024M.")

    parser_attach = subparsers.add_parser(
        "attach", parents=[existing_instance_parser], help="Attach to the Console of the Minecraft Instance.")
    parser_attach.set_defaults(
        func=proc.attach, err_template="attach to '{args.instance}'")

    parser_config = subparsers.add_parser(
        "config", parents=[existing_instance_parser, restart_parser, memory_parser], help="Configure/Change Files of a Minecraft Server Instance.")
    parser_config.add_argument(
        "-e", "--edit", nargs="+", dest="edit_paths", metavar="FILE", help="Edit a File in the Instance Folder interactively.")
    parser_config.add_argument(
        "-p", "--properties", nargs="+", help="Change server.properties options, e.g. server-port=25567 'motd=My new and cool Server'.")
    parser_config.set_defaults(func=common.configure, err_template="configure '{args.instance}'",
                               editor=CFGVARS.get('user', 'editor'), elevation=re_start_elev)

    parser_create = subparsers.add_parser(
        "create", parents=[instance_parser, type_id_parser, memory_parser], help="Create a new Server Instance.")
    parser_create.add_argument(
        "-s", "--start", action='store_true', help="Start the Server after creation, persistent enabled.")
    parser_create.add_argument(
        "-p", "--properties", nargs="+", help="server.properties options in 'KEY1=VALUE1 KEY2=VALUE2' Format.")
    parser_create.set_defaults(
        func=common.create,
        elevation={
            "default": "server_user",
            "change_to": "root",
            "on_cond": {'start': True}
        })

    parser_exec = subparsers.add_parser(
        "exec", parents=[existing_instance_parser], help="Execute a command in the Console of the Instance.")
    parser_exec.add_argument("command", nargs="+",
                             help="Command to execute in the Server Console.")
    parser_exec.set_defaults(
        func=proc.mc_exec, err_template="execute command on {args.instance}")

    parser_export = subparsers.add_parser(
        "export", parents=[existing_instance_parser], help="Export an Instance to a zip File.")
    parser_export.add_argument(
        "-c", "--compress", action='store_true', help="Compress the Archive.")
    parser_export.add_argument(
        "-w", "--world-only", action='store_true', help="Only export World Data.")
    parser_export.set_defaults(func=storage.export, elevation=semi_elev)

    parser_import = subparsers.add_parser(
        "import", help="Import an Instance from a zip File.")
    parser_import.add_argument(
        "zip_path", metavar="ZIPFILE", help="The Path of the archived Server.")
    parser_import.add_argument(
        "-i", "--instance", help="Instance Name of the Minecraft Server.")
    parser_import.add_argument(
        "-w", "--world-only", action='store_true', help="Only import World Data (the instance must already exist).")
    parser_import.set_defaults(err_template="{args.action} '{args.zip_path}'",
                               func=storage.mc_import, elevation=root_elev)

    parser_logs = subparsers.add_parser(
        "logs", parents=[existing_instance_parser], help="Read the Logs of a Server.")
    parser_logs.add_argument(
        "-n", "--lines", dest="limit", type=int, default=0, help="Limit the line output count to n.")
    parser_logs.set_defaults(
        func=storage.logs, err_template="read logs of '{args.instance}'")

    parser_inspect = subparsers.add_parser(
        "inspect", parents=[existing_instance_parser],
        help="Get any information you can think of about the server in json format.")
    parser_inspect.set_defaults(
        func=common.inspect, err_template="{args.action} {args.instance}")

    parser_install = subparsers.add_parser(
        "install", parents=[existing_instance_parser, restart_parser], formatter_class=ap.RawTextHelpFormatter,
        help="Install or update a server Plugin from a local Path/URL/Zip File.\n"
             "Old plugins closely matching the new name can optionally be deleted."
    )
    parser_install.add_argument("sources", metavar="LOCAL_PATH_OR_URL", nargs="+",
                                help="Paths or URLs which point to Plugins or zip Files.")
    parser_install.add_argument("-a", "--autoupgrade", action='store_true',
                                help="Upgrade plugin and remove previous versions by name (interactive).")
    parser_install.set_defaults(func=plugin.install, elevation=root_elev,
                                err_template="{args.action} plugins on {args.instance}")

    parser_list = subparsers.add_parser(
        "ls", help="List Instances, installed Versions, Plugins, etc.")
    parser_list.add_argument("what", metavar="WHAT", nargs="?", choices=("plugins", "instances", "jars"),
                             default="instances", help="What Type (instnaces/jars) to return.")
    parser_list.add_argument("-f", "--filter", dest="filter_str",
                             default='', help="Filter by Version or Instance Name, etc.")
    parser_list.set_defaults(
        func=common.mc_ls, err_template="{args.action} {args.what}")

    parser_pull = subparsers.add_parser(
        "pull", parents=[type_id_parser], help="Pull a Server .jar-File from the Internet.")
    parser_pull.set_defaults(
        func=web.pull, err_template="{args.action} Server Type '{args.source}'")

    parser_rename = subparsers.add_parser(
        "rename", parents=[existing_instance_parser], help="Rename a Server Instance.")
    parser_rename.add_argument(
        "new_name", metavar="NEW_NAME", help="The new Name of the Server Instance.")
    parser_rename.set_defaults(func=common.rename)

    parser_restart = subparsers.add_parser(
        "restart", parents=[existing_instance_parser, message_parser], help="Restart a Server Instance.")
    parser_restart.set_defaults(
        func=common.notified_set_status, elevation=semi_elev)

    parser_remove = subparsers.add_parser(
        "rm", parents=[existing_instance_parser, force_parser], help="Remove a Server Instance.")
    parser_remove.set_defaults(
        func=storage.remove, err_template="remove '{args.instance}'")

    parser_remove_jar = subparsers.add_parser(
        "rmj", parents=[force_parser], help="Remove a cached Server Binary.")
    parser_remove_jar.add_argument(
        "source", metavar="TYPEID", type=check_strict_type_id,
        help=("Type ID in '<TYPE>:<VERSION>:<BUILD>' format.\n"
              "'<TYPE>:latest' or '<TYPE>:latest-snap' are NOT allowed.\n"
              "'all' removes all cached Files.\n"))
    parser_remove_jar.set_defaults(
        func=storage.remove_jar, err_template="remove .jar File '{args.source}'")

    parser_start = subparsers.add_parser(
        "start", parents=[existing_instance_parser], help="Start a Server Instance.")
    parser_start.add_argument("-p", "--persistent", action='store_true',
                              help="Start even after Reboot.")
    parser_start.set_defaults(
        func=common.notified_set_status, elevation=semi_elev)

    parser_status = subparsers.add_parser(
        "status", parents=[existing_instance_parser], help="Get extensive Information about the Server Instance.")
    parser_status.set_defaults(
        func=common.mc_status, err_template="retrieve {args.action} of '{args.instance}'", elevation=semi_elev)

    parser_stop = subparsers.add_parser(
        "stop", parents=[existing_instance_parser, message_parser], help="Stop a Server Instance.")
    parser_stop.add_argument("-p", "--persistent", action='store_true',
                             help="Do not start again after Reboot.")
    parser_stop.set_defaults(
        func=common.notified_set_status, elevation=semi_elev)

    parser_uninstall = subparsers.add_parser(
        "uninstall", parents=[existing_instance_parser, restart_parser, force_parser],
        help="Uninstall a server Plugin by File Name."
    )
    parser_uninstall.add_argument("plugins", metavar="PLUGIN_NAME", nargs="+",
                                  help="Plugin File names in the plugins folder of the instance.")
    parser_uninstall.set_defaults(func=plugin.uninstall, elevation=re_start_elev,
                                  err_template="{args.action} plugins on {args.instance}")

    parser_update = subparsers.add_parser(
        "update", parents=[existing_instance_parser, type_id_parser, restart_parser], help="Update a Server Instance.")
    parser_update.set_defaults(func=common.update, elevation=re_start_elev)

    parser_shell = subparsers.add_parser(
        "shell", parents=[instance_subfolder_parser], help="Use a Shell to interactively edit a Server Instance.")
    parser_shell.set_defaults(func=proc.shell, err_template="invoke a Shell",
                              shell_path=CFGVARS.get('user', 'shell'))

    parser_wcfg = subparsers.add_parser(
        "write-cfg", help="Write mcctl configuration and exit.")
    parser_wcfg.add_argument("-u", "--user", action="store_true",
                             help="Write the Configuration in the Home of the user logged in instead of /etc.")
    parser_wcfg.set_defaults(
        func=write_cfg, err_template="write Configuration File",
        elevation={
            "default": "login_user",
            "change_to": "root",
            "change_fully": True,
            "on_cond": {'user': False}
        })

    return parser


def main() -> None:
    """Start mcctl.

    This function handles all arguments, elevation and parameters for functions.
    The logic is moved into the other files as much as possible.
    """
    read_cfg()
    # Determine needed Permission Level and restart with sudo.
    args = get_parser().parse_args()
    plvl = get_permlevel(args, args.elevation)
    try:
        apply_permlevel(plvl)
    except (KeyError, OSError) as ex:
        if args.verbose:
            raise
        print(f"Process Elevation failed: {ex}")
        sys.exit(1)
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
