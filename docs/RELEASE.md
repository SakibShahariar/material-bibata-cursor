# Release checklist

Use this checklist before tagging and publishing a Material Bibata Cursor release. The goal is to ensure that every release is reproducible, validated, and clearly documented now that this repository owns the theme configuration and release packaging.

## Before tagging

- [ ] Confirm the intended version number follows the existing semantic-version pattern, such as `v1.5.0`.
- [ ] Review all changes since the previous release.
- [ ] Confirm `themes.json` changes are intentional, including theme keys, optional `label` values, and color values.
- [ ] Confirm new or changed themes meet the documented contrast expectations.
- [ ] Confirm no unintended cursor-shape, alias, hotspot, or packaging changes are included.

## CI and local validation

- [ ] The **Cursor asset validation** workflow is green.
- [ ] Builder unit tests pass.
- [ ] Representative Linux dark and light themes build successfully.
- [ ] Representative Windows dark and light themes build successfully.
- [ ] Generated Xcursor, Hyprcursor, scalable SVG, and Windows assets validate.
- [ ] Linux and Windows release-archive smoke tests pass.
- [ ] CSS cursor names resolve to dedicated shapes or documented aliases; no unexpected `left_ptr` fallback exists.

## Linux release artifacts

- [ ] Build all themes with `just build` or the intended subset.
- [ ] Generate scalable SVG assets.
- [ ] Run `just package <version>`.
- [ ] Confirm the dark archive contains the 28 dark themes plus Classic.
- [ ] Confirm the light archive contains the 28 `-Light` themes.
- [ ] Confirm each Linux theme includes `index.theme`, `cursors/`, `hyprcursors/`, and `cursors_scalable/` where applicable.
- [ ] Confirm `INSTALL.txt`, `LICENSE`, `README.md`, and `CREDITS.txt` are present.

## Windows release artifacts

- [ ] Build Windows assets with `just build-win` or the intended subset.
- [ ] Run `just package-win <version>`.
- [ ] Confirm dark and Windows ZIP archives contain the expected themes.
- [ ] Confirm each theme includes `.cur` files, animated `wait.ani` and `left_ptr_watch.ani`, and `Install.inf`.
- [ ] Confirm Windows-specific `INSTALL.txt`, `LICENSE`, `README.md`, and `CREDITS.txt` are present.

## Checksums and release notes

- [ ] Confirm `dist/SHA256SUMS-<version>.txt` contains checksums for every archive produced for the release.
- [ ] Write release notes that call out any new themes, removed themes, changed colors, new shapes, alias changes, hotspot changes, or packaging changes.
- [ ] Link the release notes to the interactive gallery when it is publicly deployed.
- [ ] Confirm attribution and licensing remain accurate, especially for vendored or derived Bibata artwork.

## Tag and publish

- [ ] Tag the release, for example `v1.5.0`.
- [ ] Push the tag to trigger the automated release workflow.
- [ ] Confirm the release workflow completes successfully.
- [ ] Confirm the GitHub Release contains the expected Linux archives, Windows ZIPs, and checksum file.
- [ ] Download and inspect at least one Linux archive and one Windows ZIP before announcing the release.
