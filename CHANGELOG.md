# Changelog

## 0.4.3 - 30.12.2022

### Changed

- Various Bug Fixes.
- Fixed dependency drift.

## 0.4.2 - 18.12.2021

### Changed

- Various Bug Fixes.

## 0.4.1 - 30.05.2021

### Changed

#### Under the hood

Moved to Paper API v2 for Downloads.

## 0.4.0 - 29.05.2020

### Added 

- Command `import`: Import an Instance from a zip File.
- Command `install`: Install or update a server Plugin from a local Path/URL/Zip File. Old plugins closely matching the new name can optionally be deleted.
- Command `uninstall`: Uninstall a server Plugin by File Name.
- Command `status`: Get extensive Information about the Server Instance.
- Command `inspect`: Get any information you can think of about the server in json format.

### Changed

#### Features

- The instance name is now autocompleted (except for when using create, for obvious reasons), as long as it is unambiguous.
- Command `ls plugins` can now list plugins.
- Command `ls` now lists ports too.
- Changed name of inspect to logs.
- Added "force" to deletion subcommands.
- Added screen clear after closing a screen.

#### Under the hood

- Jar files are now symlinked instead of copied to the Server.
- Corrected artificial Version Tag Format
- Instead of running commands, mcctl now interacts with the System via pystemd.
- The Paper Downloader should now more accurate errors.
- Various Bug Fixes.

## 0.3.1 - 22.11.2020

### Changed

#### Features

- Added memory setting `-m` to `config`.
- Added `env_file` to Settings.

#### Under the hood

- Various Bug Fixes.
- Removed Tests as module from Package.
- Fixed encoding of special characters in server.properties.
- Fixed silently not deleting Instance.
- Fixed Errors when inputting invalid Server Version.

## 0.3.0 - 19.11.2020

### Added

- Command `shell`: Invoke an interactive Shell to configure a Server.
- Command `edit`: Configure a Server by editing files or specifying Files.
- Command `write-cfg`: Write mcctl Configuration to File. Specify `-u` for a User Config.

### Changed

#### Features

- Changed Message in restart/stop to optional.
- Update now has a parameter `--restart` that allows to restart the server directly after Update.
- Update now has a parameter `--url` that allows to pull the Jar File directly from the Internet.
- Spigot is now supported as a Type-ID.
- You can now create User-specific configurations in ~/.local/mcctl.conf.

#### Under the hood

- Various Bug Fixes
- Fixed silently not deleting Instance.
- Mapping Parsers to Functions is directly done in ArgParse.
- The App is Permission-Aware. It knows when to request which Permissions (root/server user, etc).

## 0.2.1 - 19.04.2020

### Added

- Command `inspect`: Look at Logs of the Server and limit line Count.
- Command `update`: Change the Server Jar Version.
- Command `rmj`: Removal of cached Jars.

### Changed

#### Features

- Create has now a parameter `--start` that allows to start the server directly after creation.
- Settings can be changed in the File `/etc/mcctl.conf`.

#### Under the hood

- The naming scheme of variables and functions now follows the python standard.
- UIDs and GIDs are only set if necessary, EUID and EGID is used where possible.

## 0.1.2 - 13.04.2020

The initial release.
