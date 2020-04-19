# mcctl

A Minecraft Server Management Utility written in Python.

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/) [![forthebadge made-with-python](http://ForTheBadge.com/images/badges/for-sharks.svg)](https://www.reddit.com/r/BLAHAJ/)

[![GitHub license from shields.io](https://img.shields.io/github/license/DaTurret/mcctl.svg?style=for-the-badge)](https://github.com/DaTurret/mcctl/blob/master/LICENSE) [![Python Versions](https://img.shields.io/pypi/pyversions/mcctl?style=for-the-badge)](https://pypi.python.org/pypi/mcctl/) [![PyPI - Wheel](https://img.shields.io/pypi/format/mcctl?style=for-the-badge)](https://pypi.python.org/pypi/mcctl/)

## Prerequisites

To use mcctl, your server setup should look something like [this](https://gist.github.com/DaTurret/edc02105a0d85d603d322bf529057216).

## Installation

The easiest way to install mcctl is via pip:

```sh
sudo pip install mcctl
```

## Getting started

As soon as mcctl is installed, you can create a new server:

```sh
sudo mcctl create myserver vanilla:latest -m 3G -p server-port=25566 "motd=My new and fancy Minecraft Server!"
```

- create: Sets up a new server and configures it accordingly.
- Instance ID: gives the server a specific name (ID) which can be used in other commands.
- Type ID: Specifies the Minecraft server type. Automatically downloads the "jar"-File.
- Memory (`-m`): The amount of memory a server gets. Defaults are set via the systemd unit explained in [Prerequisites](#prerequisites).
- Properties (`-p`): Options for the `server.pproperties`-File. Values with spaces can be quoted.

The server is now created, but not running. For that, you can use the `start` command:

```sh
sudo mcctl start myserver -p
```

- start: Starts a server.
- Instance ID: The name of the server to start.
- Persistent (`-p`): Sets up the server to be started after a reboot.

We can check if the server runs using the Command `ls`:

```sh
sudo mcctl ls

Name           Server Version      Status      Persistent  
myserver       1.15.2              Active      True
```

## Documentation

mcctl is not well documented (yet). However, you should be able to answer a lot of your questions with the help in the package:

```sh
mcctl -h
```

## Suggestions/Issues

If you have suggestions, questions or issues, feel free to report it as an Issue [here](https://github.com/DaTurret/mcctl/issues). Insights and Ideas of others are always welcome.

## License

This Project is Licensed under the GPLv3. Please see [LICENSE](https://github.com/DaTurret/mcctl/blob/master/LICENSE) for details.
