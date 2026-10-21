# Fedora RPM packaging

This spec packages the prebuilt Linux release archives into a noarch RPM.
It installs only `Bibata-Material-*` theme directories under
`/usr/share/icons`; RPM owns those paths, so uninstalling the package does
not remove or overwrite unrelated themes. The upstream archives contain the
Xcursor, scalable SVG, and Hyprcursor assets.

## Build locally

Use a Fedora environment with RPM build tools and `spectool` installed:

```bash
sudo dnf install rpm-build rpmdevtools spectool
rpmdev-setuptree
spectool -g -R packaging/fedora/material-bibata-cursor.spec
rpmbuild -ba packaging/fedora/material-bibata-cursor.spec
```

The spec tracks the upstream release version in `Version:` and downloads
the matching dark and light archives. When a new release is published,
update the version and changelog, then build and inspect the resulting RPM.

## Install and remove

After building, install the RPM produced under `~/rpmbuild/RPMS/noarch/`
with `sudo dnf install ./material-bibata-cursor-*.noarch.rpm`. Remove it with
`sudo dnf remove material-bibata-cursor`. Check the transaction summary
before confirming either operation.

## COPR publication and verification

Create a COPR project, configure its supported Fedora chroots, and upload
this spec plus the matching release sources using the project's documented
build workflow. Before announcing availability, verify a successful COPR
build and test install, upgrade between two package versions, and removal on
a clean Fedora system. Those COPR and native DNF checks have not been run by
this repository change; do not treat the package as published until they pass.

The package includes MIT-licensed project tooling/documentation and GPL-3.0-or-later
cursor artwork. Review the installed license files and the upstream README
before redistributing.
