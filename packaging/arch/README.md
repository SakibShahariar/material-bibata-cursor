# Arch Linux package

This directory contains the PKGBUILD and generated `.SRCINFO` for a system-wide
package. It installs the compiled Xcursor, Hyprcursor, and scalable SVG theme
trees under `/usr/share/icons`; it does not run a post-install script or touch
other themes. Pacman therefore owns the installed files and removes only this
package's files on uninstall.

## Build and install

The PKGBUILD currently targets release `v1.5.0` (`pkgver=1.5.0`). From an
Arch Linux system with `base-devel` installed, run:

```bash
cd packaging/arch
makepkg -si
```

The build uses the main repository at the version tag and a separate pinned
upstream Bibata checkout. Required native tools and Python are declared as
build dependencies. The package includes both the MIT license for this
repository's tooling and the GPL-3 license for the derived cursor artwork.

## Updating for a new release

1. Set `pkgver` to the new main-repository version tag and reset `pkgrel=1`.
2. Regenerate metadata with `makepkg --printsrcinfo > .SRCINFO`.
3. Build and inspect the package with `makepkg -s` and `namcap`.
4. Copy `PKGBUILD` and `.SRCINFO` into the AUR package repository and publish
   the update only after the tagged release and package build are available.

The package has not yet been built in an Arch Linux environment. Keep issue
#11 open until a real `makepkg` build and install/upgrade/removal checks pass.
