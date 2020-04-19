# Changelog

## 0.2.0 - 19.04.2020

### Added

- Command `inspect`: Look at Logs of the Server and limit line Count.
- Command `update`: Change the Server Jar Version.
- Command `rmj`: Removal of cached Jars.

### Changed

#### Features

- Create has now a parameter `--start` that allows to start the server directly after creation.

#### Under the hood

- The naming scheme of variables and functions now follows the python standard.
- UIDs and GIDs are only set if necessary, EUID and EGID is used where possible.

## 0.1.2 - 13.04.2020

The initial release.
