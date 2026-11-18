# Semantic cursor color roles (#71)

Research deliverable for #71. Proposes mapping cursor states to semantic
palette roles while preserving Bibata artwork and the 28 palette families.
This is a proposal: shipped recoloring is unchanged.

## 1. Verified Matugen token facts

- Matugen version installed here: **4.1.0** (`matugen --version`). Coverage
  tooling pins **4.2.0** ([Cargo.toml](https://github.com/InioX/matugen/blob/main/Cargo.toml)
  on branch `main` reports `version = "4.2.0"`).
- Scheme types in upstream `src/scheme.rs`: `Content`, `Expressive`,
  `Fidelity`, `FruitSalad`, `Monochrome`, `Neutral`, `Rainbow`, `TonalSpot`,
  `Vibrant`, and `Smart` — Smart is image-only; the other nine accept hex seeds
  (consistent with `docs/MATUGEN.md`).
- The live hook consumes `{{colors.primary.default.hex}}` and `{{mode}}`
  ([docs/MATUGEN.md](MATUGEN.md)); coverage reads
  `colors.primary.light.color` / `colors.primary.dark.color`.
- A local generated `colors.json` contains `colors.color0..color15` plus
  `special.background/foreground/cursor/border`; the semantic nested roles are
  produced by Matugen's JSON dump when generated with those templates, not by
  every custom/older template. Therefore **only `primary` is guaranteed for our
  current hook**; other semantic names are version/template dependent.

Guaranteed for our supported setup: `primary` (via the documented template),
`mode`. Available in Matugen's material-color schemes but not currently emitted
by our template: `error`, `tertiary`, `surface`, etc. **`tertiary` is not a
success role** — it is the third accent color in Material You; do not map copy
to it assuming success semantics. `error` is a genuine semantic role and is the
correct candidate for forbidden/not-allowed states.

## 2. Proposed semantic role map

| Cursor state | Proposed role | Rationale / exception |
|---|---|---|
| Default pointer | `primary` | Current behavior; keeps Material You identity |
| Text (`xterm`) | `primary` for outline, body for fill | Current behavior; no signal to convey |
| Link / alias (`hand2`, `link`, `dnd-link`) | `primary` | Link affordance is the shape, not a state color |
| Progress / wait | `primary`-derived shades | Already implemented (#74 sibling): 4 shades of primary |
| Forbidden / not-allowed (`crossed_circle`, `dnd_no_drop`) | `error` (when available) | Red is a universal prohibition signal; falls back to current fixed red if `error` is absent |
| Copy / alias (`copy`, `dnd-copy`) | fixed green | Green means "copy" conventionally; not a Material You semantic token — keep as preserved artwork color |
| Busy spinner accents | primary-derived shades | Already implemented; no token change |

Deliberate exceptions: copy stays fixed green (do not recolor to `tertiary`),
and semantic fixed colors (red/green/gray) remain preserved as documented in
[CURSOR_SHAPES.md](CURSOR_SHAPES.md). Light/dark variants keep their own
palette families; no cross-mode role mixing.

## 3. SVG element audit (representative)

Audited vendored sources via `grep` for color literals:

- Most shapes use only the 3 recolor slots (`#00FF00` body, `#0000FF` primary,
  `#FF0000` watch) — safely themeable.
- `wait` / `left_ptr_watch` additionally use 4 rainbow colors — now remapped to
  primary shades in `spinner_colors.py`.
- 4 corner cursors each have a 4th hardcoded color — now remapped to primary
  shades.
- DND/status shapes (`dnd_no_drop`, `dnd-copy`, `dnd-link`, `dnd-ask`,
  `circle`, `copy`, `crossed_circle`, `context-menu`, `pointer-move`) carry
  semantic red/green/gray/purple/blue accents that **must be preserved** —
  see [CURSOR_SHAPES.md](CURSOR_SHAPES.md) for the full list.
- Filter regions (`<rect>` inside `<g filter>`) use solid colors as filter
  inputs; their opacity attributes are preserved by `validate_animations.py`.

Conclusion: a blanket "recolor every path" would erase meaningful signals.
Role metadata must identify preserved regions explicitly.

## 4. Prototype (non-shipping)

A prototype was evaluated by recoloring representative SVGs with role-derived
colors for one light and one dark palette and rendering via `render_size_qa.py`.
No shipped artwork changed. The [ARCHITECTURE.md](ARCHITECTURE.md) `color_roles`
field is the proposed place to record this mapping; `preserved` lists the
regions above. Automated checks already available for such a prototype:
`validate_theme_assets.py`, `validate_animations.py`, `render_size_qa.py`
(baselines catch unintended color-region changes).

## 5. Impact and status

- Build cost: role lookup is a JSON/constant substitution, same complexity as
  today's 11 color entries; no measurable build-time impact.
- Determinism: roles derive from `themes.json` and the matched palette; no
  randomness, so ordinary palette generation remains deterministic.
- Contrast/state recognition: should be compared with rendered previews and
  baselines before any coverage expansion; not yet done for `error` because
  our current template does not emit it.

Per #71's constraint ("no artwork-wide migration until the prototype and
compatibility implications are reviewed"), this document stops at proposal.
Checkboxes requiring owner review or shipped changes remain open.
