# Material Bibata Cursor — Material Design 3 Cursor Themes for Bibata

28 pre-compiled Bibata cursor theme variants built on strict Material
Design 3 (M3) color role hierarchy, instead of naive "darken the accent
color" theming.

Grab whichever variant matches your setup — see the full list below — or
[add your own](#adding-your-own-color) if you don't see what you want; no
review process, `themes.json` is open for anyone to edit and compile.

## Available themes

28 variants across the color wheel: Ice Blue, Sky Blue, Deep Blue, Soft
Blue, Mint, Seafoam, Teal, Peach, Apricot, Sunset, Blush, Salmon,
Pink Pastel, Pink Rose, Lilac, Violet, Sage, Lime, Moss, Sand, Beige,
Brown, Cloud, Grey, Slate, Noir, Midnight, Charcoal. See `themes.json`
for exact hex values.

## Installing a single theme

Requires `fish`, `git`, `python3`, `jq`, and `bibata_cursor`'s own build
dependencies (`librsvg`, `xorg-xcursorgen` — see
[rtgiskard/bibata_cursor](https://github.com/rtgiskard/bibata_cursor)).
[`just`](https://github.com/casey/just) is optional but recommended if
you're not comfortable with fish — see below.

```bash
git clone https://github.com/SakibShahariar/material-bibata-cursor
cd material-bibata-cursor
fish scripts/compile_bibata_material.fish
```

This builds and installs all 28 variants to `~/.icons`. Then set your
cursor theme to `Bibata-Material-<Name>` (e.g. `Bibata-Material-Ice-Blue`) via
GNOME Settings → Mouse & Touchpad → Cursor Size (or GNOME Tweaks), or
however your DE/WM selects a cursor theme.

### Using `just` instead

If you don't want to think about which script does what (or aren't
comfortable running `fish` directly), a `justfile` wraps everything:

```bash
just build              # compile + install all 28 themes
just build-one Coral    # compile + install just one (fast, for testing a new color)
just package v1.0.0     # bundle compiled themes for a GitHub Release / GNOME-Look.org
just list                # list all theme names in themes.json
just show Ice-Blue      # print one theme's hex values
just check-deps         # verify fish/jq/git/python3 are installed
```

Run `just` alone to see this list any time.

## Adding your own color

`themes.json` is the single source of truth for every theme — anyone can
add one, no gatekeeping. Add an entry:

```json
"Coral": {
  "body": "#4e2418",
  "primary": "#ff7f50",
  "watch": "#2e130a"
}
```

then run `fish scripts/compile_bibata_material.fish Coral` (or `just build-one
Coral`) — pass the theme name as an argument to compile just that one
instead of recompiling all 28 (much faster while you're iterating on a
color).

A couple of rules of thumb so your addition stays legible (this is the
actual point of the M3 approach — see Theory of Operation below):

- **Body** should be dark and desaturated regardless of hue — think
  ~10–25% lightness, low saturation. It's a neutral container, not a
  darkened copy of your accent color.
- **Primary** should be vibrant/high-chroma — this is what actually
  carries the color identity.
- **Watch** is near-black, just needs to read as "behind" the outline.

To preview it: `gsettings set org.gnome.desktop.interface cursor-theme
Bibata-Material-Coral` (swap in your theme name), or `hyprctl setcursor
Bibata-Material-Coral 24` on Hyprland. Move your mouse over some text/links/etc
to see the different cursor shapes, not just the pointer.

---

## Theory of Operation

Most "themed cursor" projects take an accent color and apply it almost
directly to the cursor — often just darkened by some fixed percentage
for the body, with the same hue as the border. This tends to produce low
contrast, poor accessibility, and cursors that don't hold up against
varied backgrounds.

This project instead treats the cursor as a two-role M3 surface, the same
way Material Design 3 treats a button or a card:

| M3 Role | Cursor Element | Purpose |
|---|---|---|
| **Container** | Body (fill) | A dark, desaturated, low-light tone. Provides a stable, neutral surface regardless of brightness — this is *not* just "the accent color, darker." |
| **Primary** | Outline/border | A vibrant, high-chroma tone pulled from the M3 palette. Carries the actual thematic color identity and is what gives the cursor its accent. |

Concretely, for a theme like `Ice-Blue`:

```
Body    (Container) : #1a333d   — dark, desaturated, low luminance
Primary (Outline)   : #a8cbe2   — vibrant, high-chroma accent
Watch-bg             : #0a1f26   — near-black, supports the outline color
```

The body is *not* derived by darkening the primary — it's an independently
chosen, low-light container tone. This guarantees a consistent minimum
contrast ratio between body and outline across all 28 themes, regardless
of how saturated or how pastel the source color is. That consistency is
what M3's role system is for: Container and Primary are defined by their
*relationship* to each other, not by one being a mathematical transform of
the other.

---

## Architecture

```
themes.json                     # canonical 28-theme color table (Container/Primary/Watch per theme)
                                 # — the ONLY place theme colors are edited
scripts/
├── compile_bibata_material.fish   # builds themes from themes.json → installs to ~/.icons
├── metadata_generator.py       # writes GNOME-compliant index.theme per compiled theme
└── package_release.sh          # bundles compiled themes into a distributable archive
```

**Build flow** (`compile_bibata_material.fish`):
1. Clone/reuse `bibata_cursor` source
2. For each theme in `themes.json`: inject Body/Primary/Watch hex codes into
   `config/render.json`, compile via `cursor_utils.py`, install to `~/.icons`
3. Generate `index.theme` immediately after each theme compiles (via
   `metadata_generator.py`), so a broken metadata file is caught per-theme
   instead of discovered later

## Packaging for distribution (maintainers)

For GitHub Releases or GNOME-Look.org, compiled cursor binaries need to
be shipped as an archive — the git repo itself only holds source/scripts
(compiled themes are `.gitignore`d, not committed). After compiling:

```bash
bash scripts/package_release.sh v1.0.0
```

This bundles every compiled `Bibata-Material-*` folder from `~/.icons` (or
`$BIBATA_MATERIAL_INSTALL_DIR`) into `dist/bibata-material-v1.0.0.tar.gz`, with a
plain-language `INSTALL.txt` inside for people who download the archive
directly and never see this README. That `.tar.gz` is the file to
attach to a GitHub Release or upload to GNOME-Look.org — not the repo
itself.

---

## License

The tooling in this repository (everything under `scripts/`, `themes.json`)
is MIT-licensed — see `LICENSE`.

**This does not cover the compiled cursor themes these scripts produce.**
Those are derivative works of
[Bibata_Cursor](https://github.com/rtgiskard/bibata_cursor), which is
licensed under GPLv3-or-later. If you redistribute compiled themes (GitHub
releases, GNOME-Look.org, etc.), that redistribution is governed by GPLv3,
not by this repo's MIT license — include appropriate attribution and license
text alongside any compiled packages you publish.

This isn't legal advice; if you're unsure how this applies to your specific
distribution plans, consult the GPLv3 text or a legal professional.
