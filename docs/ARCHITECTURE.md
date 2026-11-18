# Cursor architecture research and proposed metadata schema

This document is the research deliverable for #70. It records the current
asset/build data flow, studies Phinger Cursors and its Cursor Theme Builder as
architectural references, compares the two approaches, and proposes a minimal
metadata schema and migration path. It is **research only**: no artwork,
builder, or dependency changes are made here.

## 1. Current asset and build data flow

### Source of truth

- **Palettes** — `themes.json`: 57 entries, each with `label` (optional),
  `body`, `primary`, `watch` hex colors.
- **Cursor artwork** — vendored pinned Bibata tree in
  `scripts/bibata_cursor/`: `svg/groups/*` (372 SVGs, four group variants:
  `modern`, `modern-arrow`, `modern-right`, `original*`, `shared`), `config/build.toml`,
  `config/build.right.toml`, `config/render.json`, `svg/symlink.toml`, and
  the self-contained renderer `src/cursor_utils.py`. See [VENDORED.md](../scripts/bibata_cursor/VENDORED.md).
- **Provenance** — `scripts/source_provenance.py` pins the upstream commit.

### Metadata implicit in scripts and filenames

| Property | Where it lives today | Consumed by |
|---|---|---|
| Cursor identity / X11 name | `config/build.toml [cursors.<key>] x11_name` | Linux renderer, scalable generator, Windows builder |
| Aliases | `x11_symlinks` in `build.toml`; CSS names in `generate_svg_cursors.py`; symlink rules in `svg/symlink.toml` | scalable generator, Xcursor post-setup |
| Hotspot | `x_hotspot` / `y_hotspot` per cursor, with defaults | Linux renderer, scalable metadata, Windows `.cur`/`.ani` |
| Animation frames | `png = 'wait-*.svg'` glob + frame directory name | Linux renderer (Xcursor), scalable generator, Windows `.ani` |
| Frame delay | `x11_delay` (40ms) / `win_delay` (1 → ×2 in `.ani`) | scalable metadata, Windows `.ani` |
| Windows scheme mapping | `WIN_SCHEME` table in `build_windows.py` | `Install.inf` generation |
| Color slots | 3 `match`/`replace` entries in `render.json` (body/primary/watch) + 8 extra shades in `scripts/spinner_colors.py` | all three recolor paths |
| Size ladders | `EXTRA_X11_SIZES`-derived 11-size Xcursor set in `validate_theme_assets.py`; `WINDOWS_SIZES` in `build_windows.py`; 256px SVG canvas | builders + validators |
| Handedness | Figma/upstream group choice (`modern` vs `modern-right`), no explicit metadata | source file layout only |

### Build flow

1. `build_linux.py` creates a per-theme temp work dir, mounts vendored
   `src/`/`svg/` (symlink with copy fallback) and copies `config/`, patches
   colors into `render.json`, isolates the renderer's temp path and normalizes
   Hyprcursor archives, then runs `cursor_utils.py --x11 --hypr`.
2. `install_staged_theme.py` validates and promotes the compiled theme, and
   calls `metadata_generator.py` (writes `index.theme`) and
   `generate_svg_cursors.py` (writes `cursors_scalable/<shape>/*.svg` +
   `metadata.json`, plus alias symlinks).
3. `build_windows.py` reuses the same recolored SVG sources to emit `.cur`
   and animated `.ani` files plus `install.inf`.
4. Validators: `validate_theme_assets.py` (structure/hotspots/animation
   metadata/aliases), `validate_animations.py` (frame/delay contract vs
   upstream + transparency), `qa_hotspots.py` (fractional scaling drift),
   `render_size_qa.py` (objective size/clipping + baselines).

Generated outputs are deliberately kept separate from source assets; see
[SIZE_QA.md](SIZE_QA.md), [CURSOR_SHAPES.md](CURSOR_SHAPES.md), and
[SUPPORT.md](SUPPORT.md).

## 2. Phinger Cursors — architectural reference (primary sources)

Sources:
- [Phinger Cursors repository](https://github.com/phisch/phinger-cursors)
  (`README.md`, `theme/cursor-theme.json` on branch `master`).
- [Cursor Theme Builder](https://github.com/phisch/cursor-theme-builder)
  (README and published JSON schema).
- Schema URL: `https://phisch.github.io/cursor-theme-builder/schemas/CursorTheme.json`.

Key concepts, with links to the exact upstream files:

- **Parts → sprites** — cursors are assembled from reusable *parts* designed
  on a 24/32 base grid; changing a part changes every sprite using it.
  ([README, "Parts"](https://github.com/phisch/phinger-cursors#parts))
- **Structured theme JSON** — `cursor-theme.json` has `name` and `variants`;
  each variant has `cursors`, each cursor has `name`, `sprites`, and `aliases`.
  ([cursor-theme.json](https://github.com/phisch/phinger-cursors/blob/master/theme/cursor-theme.json))
- **Variants and inheritance** — root and child variants; a child declares a
  parent and overrides properties (e.g. "add animations on top").
  ([Builder README, "Variants"](https://github.com/phisch/cursor-theme-builder#variants))
- **Per-sprite files + flips** — sprites list explicit files (e.g.
  `light/copy_24.svg`, `copy_32.svg`) and optional `flips` CSS selectors for
  left-handed transforms (`"svg"` flips the whole canvas, `"#icon"` flips a
  sub-element around its bounding-box center).
  ([Builder README, "Left handed cursors"](https://github.com/phisch/cursor-theme-builder#left-handed-cursors))
- **Declarative animations** — `animations` with `selector` and instruction
  lists (`animate`, `rotate`, duration/ease) applied via SVG.js.
  ([Builder README, "Animations"](https://github.com/phisch/cursor-theme-builder#animations))
- **Aliases** — multiple names per cursor for historical app compatibility.
  ([Builder README, "Aliases"](https://github.com/phisch/cursor-theme-builder#aliases))
- **Two output formats** — `cursors/` (Xcursor, rendered at 1x–4x) and
  `cursors_scalable/` (SVG + `metadata.json`, as introduced by KDE Plasma 6.2
  and GNOME 51).
  ([Builder README, "Output formats"](https://github.com/phisch/cursor-theme-builder#output-formats))

Phinger's artwork is CC-BY-SA-4.0 and designed in Figma; its visual style is
**not** a target for this project.

## 3. Comparison: useful, unnecessary, incompatible

| Phinger concept | Assessment for Material Bibata |
|---|---|
| Structured variant/cursor/sprite metadata | **Useful** — replaces implicit `build.toml` + script constants with one reviewable source, and gives #71/#72/#74 a place to attach metadata. |
| Variant inheritance (child overrides parent) | **Useful but optional** — light/dark palettes are already independent; inheritance would help left-handed/animation variants avoid duplicating base definitions. |
| Explicit alias lists | **Useful** — we already have `x11_symlinks` + CSS names split across files; unifying them is a clear win. |
| Per-sprite file lists with grid sizes | **Unnecessary** — our upstream SVGs are a 256-unit canvas rendered to a documented size ladder; file naming already encodes frame ordering. Keep the current renderer. |
| `flips` CSS selectors for left-handed | **Useful concept, needs classification** — see #72: not every cursor is safe to mirror, and hotspot transforms must be explicit. |
| Declarative SVG.js animation | **Incompatible / unnecessary** — Xcursor and Windows `.ani` need concrete frames; our 54-frame upstream animations already work and are validated (#39). Keep frame sequences; optionally describe them with metadata. |
| Figma/parts pipeline and CC-BY-SA artwork | **Incompatible** — we preserve Bibata artwork (GPL-3.0-or-later) and the vendored SVG tree; no Figma dependency. |
| Two output formats (Xcursor + scalable) | **Already aligned** — we produce Xcursor, Hyprcursor, scalable SVG, and Windows `.cur`/`.ani`. |

## 4. Proposed minimal metadata schema

A single `cursor-metadata.json` alongside the vendored source, *additive* to
the current `build.toml` during migration. Suggested shape (conceptual, not
implemented):

```jsonc
{
  "schema_version": 1,
  "source": {
    "upstream": "rtgiskard/bibata_cursor",
    "commit": "f4ccfe8abb63fddc7b3ce51a866fd8378395cb3d"
  },
  "palettes": { "source": "themes.json" },
  "cursors": {
    "left_ptr": {
      "source_svg": "svg/groups/modern/left_ptr.svg",
      "aliases": ["arrow", "default", "top_left_arrow", "css:default"],
      "hotspot": [55, 17],
      "nominal_size": 256,
      "color_roles": {
        "body": "#00FF00", "primary": "#0000FF", "watch": "#FF0000",
        "preserved": ["filter:*", "white", "black"]
      },
      "handedness": "symmetric",          // symmetric | mirror-safe | manual-review | do-not-mirror
      "sizes": { "xcursor": [12, 16, 20, 22, 24, 28, 32, 36, 42, 48, 54, 60, 64, 66, 72, 84, 96],
                 "windows": [16, 24, 32, 48, 64, 128] },
      "animation": null
    }
  }
}
```

Design rules derived from the comparison:

- One record per cursor name; aliases live with the cursor, not in a separate
  script table. `css:` prefix distinguishes Wayland/CSS names from X11 names.
- `hotspot` in the 256-unit source coordinate space, matching current
  `metadata.json` and `qa_hotspots.py`.
- `color_roles` maps the 3 existing slots plus the extra spinner/corner
  shades and lists preserved (semantic) colors — the subject of #71.
- `handedness` is an explicit per-cursor classification, never a global flag —
  the subject of #72.
- `animation` describes frame sequence/timing/hotspot, not SVG.js instructions —
  the subject of #74.
- Size overrides remain empty by default; #73 found shared artwork sufficient.

## 5. Backward-compatible migration path

1. **Record, don't change** — generate the metadata file from the current
   `build.toml`, `render.json`, script constants, and validator size sets.
   Builders keep using their current inputs; the metadata is initially unused.
2. **Verify parity** — add a check that the metadata describes exactly the
   current outputs (cursor count, aliases, hotspots, sizes, frame sequences).
   Existing byte-for-byte builds (#62/#64) and baseline comparisons (#58)
   remain the acceptance gate.
3. **Read-only consumer first** — make validators/docs read the metadata so
   drift is caught before any builder depends on it.
4. **Optional opt-in variant** — implement left-handed (#72) and semantic
   roles (#71) as separate opt-in outputs generated from metadata, leaving
   default outputs byte-identical.
5. **Only then** consider replacing inline script constants. No step in this
   plan removes the vendored artwork or changes shipped defaults.

Output parity verification already exists: full 57-theme serial/parallel
trees are byte-identical (#62/#64), animation frames/delays match upstream
(#39), visual baselines are checked (#58).

## 6. Open design decisions and risks

- **Who owns the metadata** — generated-from-scripts vs hand-maintained.
  Recommendation: generate first, hand-maintain only classified fields
  (handedness, color roles, preserved regions).
- **Scope of `color_roles`** — semantic state colors (#71) must not erase
  meaningful signals; needs a reviewed role map before any prototype ships.
- **Handedness transform** — mirror + hotspot transform must be tested for
  odd/even dimensions and directional shapes (#72); never mirror by filename.
- **Schema coupling** — keep `schema_version` and validate it; avoid copying
  Phinger's SVG.js animation model (#74), which cannot produce Xcursor/ANI frames.
- **Risk of premature rewrite** — #70's acceptance explicitly requires review
  before builder rewrites or dependencies; this document stops at proposal.
- **Licensing** — Phinger is CC-BY-SA-4.0; only architectural ideas (not
  artwork or code) are referenced here.

## 7. Review status

This proposal is published for owner review. Per #70's constraints, no artwork
changes, builder rewrites, or new dependencies are introduced until it is
reviewed and the dependent issues (#71, #72, #74) decide which pieces to adopt.
