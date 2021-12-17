# mcctl

A Minecraft Server Management Utility written in Python.

[![forthebadge made-with-python](https://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/) [![forthebadge for-sharks](https://ForTheBadge.com/images/badges/for-sharks.svg)](https://www.reddit.com/r/BLAHAJ/)

[![GitHub license from shields.io](https://img.shields.io/github/license/DaTurret/mcctl.svg?style=for-the-badge)](https://github.com/DaTurret/mcctl/blob/master/LICENSE) [![Python Versions](https://img.shields.io/pypi/pyversions/mcctl?style=for-the-badge)](https://pypi.python.org/pypi/mcctl/) [![PyPI - Wheel](https://img.shields.io/pypi/format/mcctl?style=for-the-badge)](https://pypi.python.org/pypi/mcctl/)

## Prerequisites

To use mcctl, your server setup should look something like [this](https://gist.github.com/DaTurret/edc02105a0d85d603d322bf529057216).

Starting from Version 0.4.0, a compiler (e.g. `gcc`), the Python3 Headers (`python-dev` or `python3-devel`) and systemd Headers (`libsystemd-dev` or `systemd-devel`) must be installed on your System before attempting Installation via pip.

## Installation

The easiest way to install mcctl is via pip:

```sh
sudo pip install mcctl
```

Or even better: use pipx!

```sh
sudo -i
pip install --user pipx
echo "export PIPX_HOME=/usr/local/lib/pipx" >> ./bash_profile
echo "export PIPX_BIN_DIR=/usr/local/bin" >> ./bash_profile
exit
# Reload environment variables
sudo -i 
pipx install mcctl
```

In some cases, the `secure_path` of `sudo` must be changed. If `sudo mcctl` returns "Command not found", add `/usr/local/bin` to your `secure_path`.

## Getting started

As soon as mcctl is installed, you can create a new server:

```sh
sudo mcctl create myserver vanilla:latest -m 3G -p server-port=25566 "motd=My new fancy Minecraft Server!"
```

- create: Sets up a new server and configures it accordingly.
- Instance ID: gives the server a specific name (ID) which can be used in other commands.
- Type ID: Specifies the Minecraft server type. Automatically downloads the "jar"-File if not cached.
- Memory (`-m`): The amount of memory a server gets. Defaults are set via the systemd unit explained in [Prerequisites](#prerequisites).
- Properties (`-p`): Options for the `server.properties`-File. Values with spaces can be quoted as shown above.

The server is now created, but not running. For that, you can use the `start` command:

```sh
sudo mcctl start myserver -p
```

- start: Starts a server.
- Instance ID: The name of the server to start.
- Persistent (`-p`): Sets up the server to be started after a reboot of the OS.

We can check if the server runs using the Command `ls`:

```sh
sudo mcctl ls -f myserver

Name           Server Version      Status      Persistent  
myserver       1.15.2              Active      True
```

## Configuration

In case you need to change the Unit Name or the Server User, it can be changed in `/etc/mcctl.conf`. The Config File can be created with the `write-cfg`-Subcommand.

### [system]

- `systemd_service`: The Service Prefix before "@INSTANCE_NAME". Default: 'mcserver'.
- `server_user`: The User under which Servers can be managed and are run. Default: 'mcserver'.
- `env_file`: The File in which Systemd Starting Options are specified. Default: 'jvm-env'.

### [user]

- `editor` The default Editor for interactive config editing. Default: 'vim'.
- `shell` The default Shell for fully interactive configuration. Default: '/bin/bash'

## Documentation

mcctl is not well documented (yet). However, you should be able to answer a lot of your questions with the help parameter:

```sh
mcctl -h
```

Or for each Subcommand (e.g. create):

```sh
mcctl create -h
```

## Suggestions/Issues

If you have suggestions, questions or issues, feel free to report them as an Issue [here](https://github.com/DaTurret/mcctl/issues). Insights and Ideas of others are always welcome.

## License

This Project is licensed under the GPLv3. Please see [LICENSE](https://github.com/DaTurret/mcctl/blob/master/LICENSE) for details.
