# Changelog

## 0.3.0 - 19.11.2020

### Added

- Command `shell`: Invoke an interactive Shell to configure a Server.
- Command `edit`: Configure a Server by editing files or specifying Files.
- Command `write-cfg`: Write mcctl Configuration to File. Specify `-u` for a User Config.

### Changed

- Changed Reason/Message in restart/stop to optional.

#### Features

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
