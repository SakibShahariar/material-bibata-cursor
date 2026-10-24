# SVG cursors

KDE Plasma 6.2+ and GNOME 51+ render cursor *SVGs* instead of bitmaps:
they expect a `cursors_scalable/<shape>/metadata.json` tree, where each
shape folder holds SVG frames plus a tiny JSON file listing them with
their hotspot. GNOME's compositor only scans XDG icon dirs
(`~/.local/share/icons`, `/usr/local/share/icons`, `/usr/share/icons`) —
`~/.icons` is never scanned, which is why the SVGs land in the XDG tree
instead of next to the Xcursor pack.

`generate_svg_cursors.py` builds that tree straight from Bibata's SVG
sources:

- one real directory per cursor shape, named by its X11 name, and
- symlinked directories for the CSS cursor names GNOME/Mutter looks up,
  mapped onto the same shapes the Xcursor bitmap theme uses.

The animated `wait`/`left_ptr_watch` cursors keep their 54 frames with a
40ms delay. `nominal_size` is 256 to match Bibata's SVG canvas, so
hotspots and scaling are identical to the bitmap theme's.

If you installed themes before SVG export existed, there's nothing to
undo: `just svg` regenerates the scalable tree without recompiling
anything.

Cursors are compiled at more sizes than upstream's default — every exact
size a 24px cursor hits across common fractional display scaling steps.
Without an exact match, some apps scale the nearest available bitmap
instead, which can look blurry on fractional scaling.

## Build flow

The Python Linux builder clones or updates the pinned `bibata_cursor`
source, patches its render config with each theme's colors, then compiles
and installs to `~/.icons` (Xcursor `cursors/` + Hyprland `hyprcursors/`).
`index.theme` is written immediately after each theme installs. The same
SVG sources are recolored into a `cursors_scalable/` tree under
`$XDG_DATA_HOME/icons`.

## Authoring

See [Cursor authoring](AUTHORING.md) for the 256-unit canvas, recolor
slots, hotspot conventions, animation frames, and alias rules.
