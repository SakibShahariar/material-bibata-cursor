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
  animation metadata).
- Release archives (Linux tarballs and Windows ZIPs) build and their
  contents validate.
- Every freedesktop/CSS cursor name resolves to the intended shape — no
  unexpected `left_ptr` fallbacks — and `docs/COMPATIBILITY.md` stays in
  sync with the generator mappings.

## Best-effort / not CI-tested

- **Live desktop sessions**: CI does not run GNOME Shell, KDE Plasma,
  Hyprland, or X11 sessions, so visual rendering and cursor pickup on real
  desktops is best-effort.
- **Niri**: the Matugen post-hook can write a `cursor-theme.kdl` include,
  but Niri support has not been verified on a live Niri session.
- **Fractional scaling hotspots**: hotspot correctness at 125% / 150% /
  200% is tracked separately in #38, not asserted in CI.
- **Windows `person` / `pin`**: upstream Windows-only names with no Linux
  `x11_name`; Linux parity is tracked in #37.

## Known limitations

- `all-resize` is the only CSS name resolved through the legacy fallback
  (to `move` art) rather than dedicated or aliased theme art.
- Theming relies on Bibata source SVGs using only the three recolor slots
  (`body`, `primary`, `watch`); any future shape with hardcoded colors
  outside those slots would not be recolored.

## Related docs

- [Compatibility matrix](COMPATIBILITY.md) — per-name art/alias/gap detail
- [SVG cursors](SVG_CURSORS.md) — scalable format and build flow
- [Windows cursors](WINDOWS.md) — Windows build and install
