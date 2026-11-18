# Animation research (#74)

Research deliverable for #74. This document inventories the current animations,
compares them with the metadata architecture proposed in
[ARCHITECTURE.md](ARCHITECTURE.md), and records restrained concepts and
constraints. No shipped animation is changed here.

## 1. Current animation inventory

Verified from the pinned vendored source and built assets:

| Property | `wait` | `left_ptr_watch` |
|---|---|---|
| Source frames | `svg/groups/shared/wait/wait-01..54.svg` (54 SVGs) | `svg/groups/modern/left_ptr_watch/left_ptr_watch-01..54.svg` (54 SVGs) |
| Frame order | sorted filename order (`-01` … `-54`) | sorted filename order |
| Delay | 40ms per frame (from `build.toml cursor_defaults.x11_delay`) | 40ms per frame |
| Hotspot | (128,128) in 256-unit canvas, fixed across frames | (55,17), fixed across frames |
| X11 output | 54 frames × each Xcursor size (16…96) | 54 frames × each Xcursor size |
| Windows output | `wait.ani` at 32px, delay×2 = 80ms/frame | `left_ptr_watch.ani` at 32px, 80ms/frame |
| Scalable SVG | 54 frame SVGs + `metadata.json` with per-frame delay/hotspot | same |
| Recoloring | body/primary/watch + 4 spinner shades from `spinner_colors.py` | same |

Total loop duration: 54 × 40ms = **2.16s** (X11/scalable); 54 × 80ms =
**4.32s** for Windows `.ani` (clickgen convention doubles the delay).

Automated checks already in CI (#39): frame count/filenames/delays match the
upstream contract exactly, hotspots fixed, transparency/opacity preserved.
Size rendering is checked in #73; baselines in #58.

## 2. Comparison with the proposed metadata architecture

The [ARCHITECTURE.md](ARCHITECTURE.md) schema has an `animation` field. Applied
here, it would describe:

```jsonc
"animation": {
  "frames": "glob:wait-*.svg",       // resolved at build time
  "order": "filename-ascending",
  "delay_ms": 40,
  "hotspot": [128, 128],
  "loop": true,
  "windows_delay_multiplier": 2
}
```

Phinger's Cursor Theme Builder instead uses declarative SVG.js instructions
(`animate`, `rotate`, duration/ease) applied to a CSS selector
([Builder README](https://github.com/phisch/cursor-theme-builder#animations)).
That model is **not adopted**: Xcursor and Windows ANI need concrete raster
frames, and our 54-frame upstream artwork already produces valid output in all
formats. Metadata should *describe* the existing frames, not synthesize motion.

## 3. Restrained concepts (not implemented)

Evaluated options against usability, accessibility, and output cost:

- **Shorter loops / fewer frames** — would cut build time and asset size, but
  #62/#64 made builds fast enough (~13 min full serial) and the 54-frame
  artwork is the recognizable Bibata spinner. Rejected for the research phase.
- **CSS/SVG.js rotation** — incompatible with Xcursor/ANI outputs. Rejected.
- **State-aware spinner colors** — already implemented in #74's sibling work:
  the 4 spinner shades derive from the theme's primary color, so the animation
  follows the palette without new assets.
- **Reduced-motion variant** — feasible as an opt-in static first frame (the
  gallery already does this for its preview). Not applied to shipped themes
  without owner approval; would be a separate output variant via #70 metadata.

## 4. Constraints and risks

- Preserve recognizable Bibata artwork and Material You identity.
- No animation dependencies or shipped-animation changes in the research phase.
- Hotspot must stay fixed across frames (asserted in CI); any redesign must
  keep that invariant.
- Frame-count/delay changes alter `.ani` loop timing (×2) and animation QA
  baselines; require explicit review and baseline updates (#58).
- Reduced-motion expectations differ by desktop; keep as opt-in, never a
  surprise default.
- Real desktop appearance remains a separate validation concern (#38/SUPPORT).

## 5. Automated checks if implementation proceeds

Already present and reusable: `validate_animations.py` (frame/delay/hotspot/
transparency), `render_size_qa.py` (size/clipping/baselines), and
`validate_theme_assets.py` (structure). Any new animation metadata must be
validated against these rather than replacing them.

## 6. Status

Research complete; no implementation authorized by this document. Dependent
decisions belong to the owner through #70 (schema), #71 (semantic colors), and
#72 (handedness). Acceptance checkboxes that require a reviewed prototype or
owner decision remain open.
