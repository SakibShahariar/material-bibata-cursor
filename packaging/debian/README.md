# Debian and Ubuntu package

This directory builds a system-wide `.deb` from the project's published Linux release archives. It does not compile cursor artwork or fetch an unpinned source tree.

## Build

Install the builder prerequisites:

```bash
sudo apt install dpkg curl tar coreutils grep findutils python3
```

Then run from the repository root:

```bash
bash packaging/debian/build-deb.sh v1.5.0
```

The script downloads the dark and light Linux archives, reads their SHA-256 digests from the GitHub Release API metadata, verifies both archives, and builds `dist/material-bibata-cursor_1.5.0_all.deb`. A separate checksum-manifest asset is not required. To build from already-downloaded release archives plus a fixture checksum manifest (also used by CI):

```bash
bash packaging/debian/build-deb.sh 1.5.0 --archive-tag ci --archives-dir dist --output-dir dist
```

Use the version of an existing GitHub Release; the example is illustrative. The package contains all 57 theme directories and their Xcursor, Hyprcursor, and scalable SVG assets.

## Install and remove

```bash
sudo apt install ./dist/material-bibata-cursor_1.5.0_all.deb
sudo apt remove material-bibata-cursor
```

Theme files are installed under `/usr/share/icons/Bibata-Material-*` and listed in the package file manifest. The package has no maintainer scripts and does not modify cursor settings, user files, or unrelated theme directories. APT/dpkg removes only paths owned by this package.

The artwork is GPL-3.0-or-later; the included `LICENSE` and `CREDITS.txt` preserve project and upstream notices. The package depends on `hicolor-icon-theme`.

## Scope

This builds a local binary package; repository hosting, signed APT metadata, and upgrade/removal testing on each supported Debian/Ubuntu release remain distribution-maintenance tasks.