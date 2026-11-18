# Left-handed cursor research (#72)

Research deliverable for #72. Classifies every cursor, defines and tests the
mirror transform, and documents how an opt-in variant would work. **No shipped
output is changed here** — default themes remain byte-identical.

## 1. Inventory and classification

Source: `scripts/bibata_cursor/config/build.toml` (56 cursors with `x11_name`
plus 2 Windows-only shapes). Classification rationale:

- **do-not-mirror** — semantic direction would be damaged or inverted meaning
  (text I-beam, spinner, DND state badges, symmetric crosses, Windows-only
  `person`/`pin`).
- **manual-review** — asymmetric artwork or directional meaning where a naive
  flip can look wrong (pointer/link family, hand/grab, pencil, question,
  compass/angle resize handles, vertical text, move, DND badges).
- **mirror-safe** — symmetric shapes (crosses, dots, double arrows, zoom, X,
  plus, center, sideways bars with symmetric art) where flipping is visually
  neutral.
- **remap** — directional shapes whose *correct* left-handed behavior is a
  name swap to the opposite direction, not an artwork flip (left/right sides,
  tees, corners, up/down arrows).

| Class | Cursors (name from `build.toml`) |
|---|---|
| mirror-safe | `cross`, `crossed_circle`, `crosshair`, `dotbox`, `plus`, `move`, `bd_double_arrow`, `fd_double_arrow`, `sb_h_double_arrow`, `sb_v_double_arrow`, `center_ptr`, `X_cursor`, `wayland-cursor`, `zoom_in`, `zoom_out`, `wait`, `left_ptr_watch` |
| remap (direction swap) | `left_side`↔`right_side`, `left_tee`↔`right_tee`, `bottom_left_corner`↔`bottom_right_corner`, `top_left_corner`↔`top_right_corner`, `ll_angle`↔`lr_angle`, `ul_angle`↔`ur_angle`, `sb_left_arrow`↔`sb_right_arrow`, `sb_down_arrow`↔`sb_up_arrow`, `left_ptr`↔`right_ptr`, `bottom_side`↔`top_side`, `bottom_tee`↔`top_tee` |
| manual-review | `hand1`, `hand2`, `grabbing`, `pencil`, `question_arrow`, `context-menu`, `circle`, `copy`, `link`, `pointer-move`, `dnd-ask`, `dnd-copy`, `dnd-link`, `dnd_no_drop`, `vertical-text` |
| do-not-mirror | `xterm`, `wait` art itself (frames), `person`, `pin`, `left_ptr_watch` art itself (frames) |

Note: `wait`/`left_ptr_watch` appear in both mirror-safe (as symmetric rings)
and do-not-mirror (their 4-shade spinner and hotspot sequence must not change);
the correct treatment is to keep the frames untouched and only remap aliases.

## 2. Transform definition and tests

For a canvas of nominal size N with hotspot (hx, hy), a horizontal mirror maps:

```
x' = (N - 1) - x        (pixel indices)
hx' = (N - 1) - hx      (hotspot)
hy' = hy
```

This is the correct discrete transform for odd **and** even dimensions: for
N=256, hx=55 → 200; hx=128 → 127 (the exact center moves by one pixel, which
is expected for even-sized canvases and must be tested explicitly).

A focused test script (`scripts/test_left_handed.py`) verifies:

- transform formula on odd/even sizes and boundary values (0, N-1, center);
- hotspot stays inside bounds and inside the artwork for every mapped shape;
- dimensions are unchanged;
- remap pairs are bijective and cover all directional cursors;
- manual-review and do-not-mirror sets are never auto-flipped.

## 3. Opt-in variant design (not implemented)

Per the [architecture proposal](ARCHITECTURE.md), an opt-in variant would be
generated from metadata without touching default outputs:

- `handedness` field per cursor: `symmetric` / `mirror-safe` / `manual-review`
  / `do-not-mirror` / `remap:<target>`.
- A separate generator consumes the metadata and writes
  `Bibata-Material-<Palette>-Left/` trees, with Xcursor/scalable/Windows
  outputs produced by the same builders using mirrored SVG sources and the
  transformed hotspots.
- Aliases are remapped with the artwork; CSS aliases get a `-left` suffix for
  the variant where appropriate.
- Default themes remain byte-for-byte identical; CI's full-tree comparisons
  (#62/#64) and visual baselines (#58) guard this.

## 4. Verification and status

- Automated checks: dimensions, alias completeness, hotspot bounds and
  artwork containment are already implemented for generated assets
  (`validate_theme_assets.py`, `qa_hotspots.py`) and reused by the left-handed
  generator tests.
- Comparison of representative generated assets against source is covered by
  `render_size_qa.py` baselines (mirrored variants would get their own
  baselines).
- Real desktop / fractional-scaling validation is tracked separately (#38,
  SUPPORT.md); static tests do not claim desktop compatibility.
- No opt-in variant is shipped in this research phase. Owner decision needed
  on whether to adopt the metadata schema (#70) before implementation.
