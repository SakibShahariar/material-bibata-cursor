# SVG-first cursor authoring

This document describes how to add or modify cursor shapes in Material Bibata Cursor. The scalable SVG pipeline is the source of truth for new artwork; bitmap formats are generated from the same sources and configuration.

## Canvas and hotspots

- Author cursor SVGs on a **256 × 256** canvas.
- Use hotspot coordinates in the same **0–256** coordinate space.
- Set `x_hotspot` and `y_hotspot` in the cursor’s build configuration so the active pixel — usually the pointer tip, text-caret point, or resize handle — lands where users expect.
- Do not use a 24-unit canvas. The generated scalable metadata uses `nominal_size: 256`; a mismatched canvas breaks hotspot placement and scaling.

## Recolor slots

The build recolors source SVGs by replacing three fixed placeholder colors:

| Placeholder | Theme role | Example |
|---|---|---|
| `#00FF00` | Body / container fill | Dark neutral fill |
| `#0000FF` | Primary / outline | Vibrant accent |
| `#FF0000` | Watch / busy accent | Busy-indicator color |

Use these exact placeholder colors in new artwork. Do not introduce additional theme-dependent colors: they will not be recolored per theme.

## Static shapes

A static cursor needs:

1. An SVG source file in the Bibata SVG source tree.
2. A cursor entry in the build configuration.
3. An `x11_name`, which becomes the real shape directory under `cursors_scalable/`.
4. Hotspot coordinates, either per-shape or inherited from the defaults.

For example, a shape with `x11_name: "left_ptr"` is written to:

```text
cursors_scalable/left_ptr/left_ptr.svg
cursors_scalable/left_ptr/metadata.json
```

## Animated shapes

Animations are frame sequences, not animated SVG files.

- Put the frames in a source directory.
- Use a wildcard PNG/SVG reference such as `wait-*.png` in the cursor configuration.
- The generator sorts the frames, recolors each one, and writes a `metadata.json` frame list.
- Provide delays either as a single value or as a list for variable frame timing.

Animated cursors such as `wait` and `left_ptr_watch` must retain valid frame ordering, delays, transparency, and hotspots after recoloring.

## Names and aliases

Every real shape needs an `x11_name`. This is the directory name used by X11/KDE lookups and the target for aliases.

Use `x11_symlinks` for additional legacy X11 names. For example, a shape may be stored as `hand` while also being linked from another legacy name.

Freedesktop/CSS names used by GNOME/Mutter — such as `pointer`, `text`, `ew-resize`, and `zoom-in` — are resolved as follows:

1. Prefer an exact match against an `x11_name` or alias.
2. Otherwise, use the documented legacy X11 fallback.

Do not let a CSS name silently resolve to `left_ptr` when dedicated art exists or is expected. Known intentional pointer aliases and documented gaps are the only exceptions.

## Adding a theme

Add an entry to the repository-root `themes.json`:

```json
"Coral": {
  "label": "Coral",
  "body": "#4e2418",
  "primary": "#ff7f50",
  "watch": "#2e130a"
}
```

Rules:

- The theme key must be path-safe; prefer hyphenated names such as `Ice-Blue`.
- `label` is optional and is used for human-friendly display in the gallery and documentation.
- `body`, `primary`, and `watch` are required six-digit hex colors.
- The builder validates theme names and color formats before generating assets.

## Build and validation

After changing artwork or configuration:

```bash
just build-one <Theme>
just svg-one <Theme>
```

Then run the asset validator. CI builds representative themes and validates Xcursor, Hyprcursor, scalable SVG, Windows, and release-archive outputs.

A new shape should:

- Have a valid 256-unit canvas and in-bounds hotspot.
- Recolor correctly using the three placeholder slots.
- Expose every required CSS/X11 name through real art or an explicit alias.
- Not introduce a silent `left_ptr` fallback.
- Preserve animation frame order, delay, transparency, and hotspot behavior.
