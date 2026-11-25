# Supported desktops and test matrix

This documents which platforms Material Bibata targets, where each format
installs, and what CI actually validates versus what is best-effort.

## Formats and desktops

| Format | Desktop / stack | Install location | Status |
|---|---|---|---|
| Xcursor (`cursors/`) | X11 apps, X11 desktops | `~/.icons` (user) or `/usr/share/icons` (system) | Supported; built and validated in CI |
| Hyprcursor (`hyprcursors/`) | Hyprland | `~/.icons` (alongside Xcursor) | Supported; built and validated in CI |
| Scalable SVG (`cursors_scalable/`) | GNOME 51+, KDE Plasma 6.2+ | `$XDG_DATA_HOME/icons` (default `~/.local/share/icons`) or system icon dirs | Supported; built and validated in CI |
| Windows `.cur` / `.ani` | Windows | `C:\Windows\Cursors\<theme>\` via `Install.inf` | Supported; built and validated in CI |

GNOME's compositor only scans XDG icon directories for `cursors_scalable/`
— `~/.icons` is not on that path — which is why the scalable tree installs
to `~/.local/share/icons` while the Xcursor/Hyprcursor packs stay in
`~/.icons`.

## What CI validates

The `Cursor asset validation` workflow builds a representative theme set
(Peach dark + Peach-Light) and checks:

- Linux Xcursor, Hyprcursor, and scalable SVG assets build cleanly.
- Windows `.cur` and animated `.ani` assets build cleanly.
- Generated assets pass `validate_theme_assets.py` (structure, hotspots,
  animation metadata) and `validate_animations.py` (frame/delay contract and
  transparency).
- Rendered PNGs for representative themes are compared against committed
  baselines, and the descriptive cursor metadata is checked against sources
  and built assets.
- Release archives (Linux tarballs and Windows ZIPs) build and their
  contents validate.
- Every freedesktop/CSS cursor name resolves to the intended shape — no
  unexpected `left_ptr` fallbacks — and `docs/COMPATIBILITY.md` stays in
  sync with the generator mappings.

## Best-effort / not CI-tested

- **Live desktop sessions**: CI does not run GNOME Shell, KDE Plasma,
  Hyprland, or X11 sessions, so visual rendering and cursor pickup on real
  desktops is best-effort. Recorded live evidence so far:
  - **GNOME Wayland** — Matugen hook applied dark/light presets via gsettings
    (#49); manual hotspot click checklist at 125/150/200% passed (#38).
  - **KDE Plasma** — the reporter of #1 confirmed at 2560×1440 / 150% scaling
    that the cursor blur with the Shake Cursor / Locate Pointer effect was
    fixed in `v1.6.0-rc1` (scalable SVG path). This verifies rendering for that
    scenario only — not Matugen theme application or hotspot click accuracy on
    KDE, which remain untested there.
- **Niri**: the Matugen post-hook can write a `cursor-theme.kdl` include,
  but Niri support has not been verified on a live Niri session.
- **Umbriel**: the Matugen post-hook can write an opt-in `cursor-theme.toml`
  include (#75). The generated TOML and opt-in detection are tested, but live
  Umbriel session behavior has not been verified here.
- **Fractional scaling hotspots**: verified manually on GNOME at 125% /
  150% / 200% (#38); asset-level drift is ≤1px. Not asserted in CI.
- **Windows `person` / `pin`**: upstream Windows-only names with no Linux
  `x11_name`; Linux parity is tracked in #37.

## Known limitations

- `all-resize` is the only CSS name resolved through the legacy fallback
  (to `move` art) rather than dedicated or aliased theme art.
- Theming uses the three upstream slots (`body`, `primary`, `watch`) plus
  derived primary shades for the spinner and corner-resize accents. Drag
  state colors (red no-drop, green copy, gray link) are intentionally fixed
  semantic signals — see [Cursor shapes](CURSOR_SHAPES.md).

## Related docs

- [Compatibility matrix](COMPATIBILITY.md) — per-name art/alias/gap detail
- [SVG cursors](SVG_CURSORS.md) — scalable format and build flow
- [Windows cursors](WINDOWS.md) — Windows build and install
