# Packaging for redistribution

The packaging script bundles **already-built** themes; it does not compile
them. Build the Linux themes and Windows assets first, then run the relevant
packaging command.

## Linux archives

```bash
just build
just package v1.5.0
```

This writes:

- `dist/bibata-material-dark-v1.5.0.tar.gz` — 28 dark themes + Classic
- `dist/bibata-material-light-v1.5.0.tar.gz` — 28 `-Light` themes

Each Linux theme folder contains the Xcursor `cursors/` tree, Hyprland
`hyprcursors/`, and scalable `cursors_scalable/` SVGs. A single archive
supports X11 apps, Hyprland, and GNOME 51+ / KDE Plasma 6.2+.

## Windows archives

Make sure the upstream Bibata source is present, build the Windows assets,
and then package them:

```bash
just build-win
just package-win v1.5.0
```

This writes:

- `dist/bibata-material-dark-v1.5.0-win.zip` — dark themes + Classic
- `dist/bibata-material-light-v1.5.0-win.zip` — light themes

Each Windows ZIP includes theme folders with `.cur` files, animated
`wait.ani` and `left_ptr_watch.ani`, per-theme `Install.inf` files, and
Windows-specific `INSTALL.txt`.

All archives and ZIPs also include `LICENSE`, `README.md`, and
`CREDITS.txt`. The packager writes `dist/SHA256SUMS-<version>.txt` with
SHA-256 checksums for the archives produced for that version.

## Filtering themes

You can filter themes with `--only-dark`, `--only-light`, or `--exclude`:

```bash
bash scripts/package_release.sh v1.5.0 --win --only-dark
bash scripts/package_release.sh v1.5.0 --exclude Classic
```

## Automated releases

Pushing a version tag such as `v1.1.0` runs
`.github/workflows/release.yml`. It builds and validates Linux and Windows
cursor assets, packages all four archives, checks their contents, and creates
or updates the matching GitHub Release.

A failed build or validation step prevents the publish step from running.
Before tagging, follow the [release checklist](RELEASE.md).
