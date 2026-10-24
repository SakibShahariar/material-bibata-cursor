# Supported desktops and test matrix

This document describes the platforms Material Bibata Cursor targets, the cursor formats each platform uses, and what is automatically tested by CI.

## Support levels

| Platform | Cursor format | Support | CI coverage |
|---|---|---|---|
| GNOME Shell 51+ | `cursors_scalable/` SVG cursors from XDG icon paths | Supported | Asset and archive validation |
| KDE Plasma 6.2+ | `cursors_scalable/` SVG cursors | Supported | Asset and archive validation |
| Hyprland | `hyprcursors/` Hyprcursor archives | Supported | Asset and archive validation |
| X11 | `cursors/` Xcursor themes | Supported | Asset and archive validation |
| Windows | `.cur`, animated `.ani`, and `Install.inf` | Supported | Windows build and archive validation |
| Niri | Xcursor theme via Matugen-generated configuration | Best effort | Not CI-tested |
| Sway | Xcursor theme via Matugen hook | Best effort | Not CI-tested |

## GNOME Shell 51+

GNOME uses the scalable SVG cursor tree under an XDG icon path. The build writes `cursors_scalable/` and generates freedesktop/CSS alias directories so GNOME requests resolve to the intended Bibata shapes.

CI builds representative dark and light themes, validates the scalable metadata and SVG frames, and smoke-tests the Linux release archives.

## KDE Plasma 6.2+

KDE Plasma uses the same `cursors_scalable/` SVG format. Real shape directories are accompanied by symlinked alias directories, with `metadata.json` describing frames, delays, hotspots, and the 256-unit nominal canvas.

CI validates the generated scalable tree and ensures release archives contain the expected SVG assets.

## Hyprland

Hyprland uses the `hyprcursors/` Hyprcursor archives produced during the Linux build.

CI validates that each theme has a Hyprcursor manifest and `.hlc` archives, including the required core shapes.

## X11

X11 applications use the compiled Xcursor theme in `cursors/`. This remains the fallback format for environments and applications that do not use scalable cursors or Hyprcursor.

CI validates Xcursor magic bytes, required core shapes, and the presence of valid cursor files.

## Windows

Windows uses separately generated `.cur` and animated `.ani` files, registered through each theme’s `Install.inf`.

CI builds representative Windows themes, validates cursor-file structure and ANI animation chunks, and smoke-tests the Windows release ZIP archives.

## Niri and Sway

Niri and Sway are supported on a best-effort basis through the Matugen post-hook, which can update the active Xcursor theme.

These environments are not exercised by CI. Before relying on them, install the themes and verify that the generated cursor configuration selects the expected `Bibata-Material-*` theme.

## What CI does not test

CI does not perform interactive desktop testing. In particular, it does not verify:

- Live cursor rendering in GNOME, KDE, Hyprland, Niri, Sway, or Windows.
- Visual appearance after recoloring.
- Hotspot accuracy under fractional display scaling.
- Desktop-specific theme-selection UI behavior.

For those checks, install a built theme in the target environment and test the pointer, text, resize, grab, busy, and animated cursors.

## Related documentation

- [SVG-first cursor authoring](AUTHORING.md)
- [Release checklist](RELEASE.md)
