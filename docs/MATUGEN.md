# Matugen setup

Get a theme that matches your wallpaper with
[matugen](https://github.com/InioX/matugen) and the included post-hook.

The hook supports GNOME/GTK, KDE Plasma, Hyprland, Sway, and an opt-in Niri
configuration include. It preserves `XCURSOR_SIZE` when set and otherwise
tries to read the active Hyprland or GNOME cursor size before using 24 as a
fallback.

## Setup

1. Copy `scripts/cursor_matugen.sh`, `scripts/color_match.py`, and the
   repository-root `themes.json` into
   `~/.config/matugen/post-hook-scripts/`.
2. Add the template to `~/.config/matugen/config.toml`:

```toml
[templates.cursor]
input_path = "~/.config/matugen/templates/cursors.json"
output_path = "~/.config/colors.json"
post_hook = "~/.config/matugen/post-hook-scripts/cursor_matugen.sh"
```

3. Create `~/.config/matugen/templates/cursors.json` with:

```json
{
    "colors": {
        "color13": "{{colors.primary.default.hex}}"
    }
}
```

Before running the hook, build/install the cursor themes (for example,
with `just build`) so the matched preset is available locally.

The hook does **not** build or install themes: it picks the closest preset
in `themes.json` using `color_match.py` and applies that already-installed
theme. It selects the nearest existing palette using CIEDE2000; it does not
recolor or rebuild a cursor to match Matugen's exact primary hex value, so
the result may be close rather than identical.

When run directly from a repository checkout, it finds `themes.json` in the
repository root. When installed as a Matugen post-hook, keep `themes.json`
beside the copied script.

## Niri support

The Matugen post-hook can also update the cursor theme used by
[Niri](https://github.com/niri-wm/niri).

Add this line to your Niri configuration, normally
`~/.config/niri/config.kdl`:

```kdl
include "cursor-theme.kdl"
```

If your `config.kdl` already has a `cursor` block with an `xcursor-theme`
setting, remove that setting to avoid configuring the theme in two places.
If the block contains no other settings afterward, remove the entire block.

The generated `cursor-theme.kdl` file must be in the same directory as the
main Niri configuration. It looks like:

```kdl
cursor {
  xcursor-theme "Bibata-Material-Teal"
}
```

The theme name changes automatically according to the color selected by the
Matugen hook.

### Requirements

- Install the matching `Bibata-Material-*` cursor themes before running the hook.
- Keep the `include "cursor-theme.kdl"` line in your main Niri configuration.
- Niri support has not yet been verified on a live Niri session.
