# Cursor size and rendering QA

This records renderer-based source QA for cursor artwork across the shipped
size ladders (#73). It is distinct from real-desktop fractional-scaling QA
(#38) — see [hotspot QA](HOTSPOT_QA.md) for that.

## Tested sets and tools

- **Render tool:** `rsvg-convert` 2.63.2 (librsvg 2.63.2, cairo 1.18.6,
  pango 1.58.2, harfbuzz 15.0.0, freetype via fontconfig). Pillow 12.3.0 is
  used for pixel analysis. Versions come from `rsvg-convert --version` and
  `PIL.__version__` on the test machine; CI pins Ubuntu 24.04 packages.
- **Xcursor ladder:** 16, 20, 22, 24, 28, 32, 48, 64, 72, 84, 96px.
- **Windows `.cur` ladder:** 16, 24, 32, 48, 64, 128px.
- **Reference size:** 256px (the SVG source canvas) for clipping checks.
- **Representative shapes:** `left_ptr` (arrow + outline), `xterm` (thin I-beam),
  `bd_double_arrow` (diagonal handle), `wait` (animated, 54 frames),
  `bottom_right_corner`, `circle`, `copy`, `zoom-in`.

## Reproduce

```sh
python3 scripts/render_size_qa.py --theme Peach \
  --contact-sheet /tmp/size-qa.png
```

The script recolors the pinned upstream SVGs with the theme's colors, renders
every representative shape at the union of both ladders, and writes PNGs plus
a `report.json` with per-size checks.

## Objective checks

For every shape/size the script asserts:

- **dimensions** — rendered PNG is exactly `size × size`.
- **transparency** — the canvas is not fully opaque (transparent background).
- **clipping** — the artwork's alpha bounding box at the 256px reference does
  not span the full canvas in either dimension (no content cut at opposite
  edges). Edge-touching at 16px is recorded as an observation, not a failure,
  because downsampling naturally spreads antialiased alpha.
- **hotspot bounds** — from `metadata.json`, hotspot is within the nominal
  canvas and within the artwork's alpha bounding box (see `validate_theme_assets.py`).

Before any override was considered, a full run for `Peach` rendered 8 shapes ×
12 sizes with **0 objective failures**; no reference render was clipped.

## Visual findings

A contact sheet of `left_ptr`, `xterm`, `bd_double_arrow`, `wait`,
`bottom_right_corner`, `circle`, `copy`, `zoom-in` at 16/32/64/128px showed:

- Arrows, I-beam, diagonal handles and zoom glyph scale cleanly. At 16px thin
  strokes soften and small details merge — expected bitmap downsampling, not
  a missing-art or renderer defect. The outlines remain readable at real
  desktop sizes (24px and up).
- The spinner (`wait`) and its 4 theme-derived shades stay distinct at every
  size; the ring is recognizable at 16px.
- `bottom_right_corner`, `circle` and `copy` keep their semantic fixed colors
  (red = no-drop, green = copy) and their outlines at all sizes. At 16px the
  outline is soft but the silhouette is intact.
- No shape showed clipped art, a lost hotspot, or a detail that a hand-tuned
  size-specific variant would restore.

## Decision

**Shared artwork is sufficient.** No size-specific overrides are justified by
these measurements or rendered comparisons, so no override metadata mechanism
is added (which would also overlap #70). If a future palette or shape shows a
real regression, add evidence here first, then design the minimal override
mechanism.

Existing generated output is unchanged: this issue made no artwork or builder
changes, so all release assets remain byte-identical (verified by the full
57-theme serial/parallel comparisons in #62/#64).

Real desktop and fractional-scaling behavior is tracked separately in #38 and
the [support matrix](SUPPORT.md); this document does not claim desktop
compatibility from renderer output alone.

## Visual regression baselines (#58)

`scripts/render_size_qa.py --baselines docs/baselines` compares rendered PNGs
against committed baselines to catch unintended art/recolor/transparency
changes. To update baselines for an intentional art change:

```sh
python3 scripts/render_size_qa.py --theme Peach \
  --update-baselines docs/baselines
# review `git diff -- docs/baselines`, then commit the intended changes
```

Only representative shapes and themes are baselined to keep repository size
reasonable; the check is a guard against visual drift, not a substitute for
the objective size checks above.
