<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/logo-dark.png">
  <img src="docs/logo-light.png" alt="Material Bibata Cursor" width="360">
</picture>

# Material Bibata Cursor

28 Bibata cursor themes, colored using Material Design 3's tonal
system instead of just darkening an accent color for the body.

Grab whichever variant matches your setup, or add your own color —
`themes.json` is open for anyone to edit, no review needed.

![All 28 themes](docs/comparison-all-28.png)

## Themes

Ice Blue, Sky Blue, Deep Blue, Soft Blue, Mint, Seafoam, Teal, Peach,
Apricot, Sunset, Blush, Salmon, Pink Pastel, Pink Rose, Lilac, Violet,
Sage, Lime, Moss, Sand, Beige, Brown, Cloud, Grey, Slate, Noir,
Midnight, Charcoal. Exact hex values are in `themes.json`.

Each theme's actual range of cursor shapes:

![All 28 themes, several shapes each](docs/matrix-all-28.png)

## Install

Needs `fish`, `git`, `python3`, `jq`, plus whatever `bibata_cursor`
itself needs to build (`librsvg`, `xorg-xcursorgen` — see
[rtgiskard/bibata_cursor](https://github.com/rtgiskard/bibata_cursor)).

```bash
git clone https://github.com/SakibShahariar/material-bibata-cursor
cd material-bibata-cursor
fish scripts/compile_bibata_material.fish
```

That installs all 28 to `~/.icons`. Pick one via GNOME Settings →
Mouse & Touchpad → Cursor Size (or Tweaks), or however your setup
picks a cursor theme.

Don't want to run fish directly? There's a `justfile`:

```bash
just build              # all 28
just build-one Coral    # just one, faster for testing a color
just package v1.0.0     # bundle for a release
just list
just show Ice-Blue
just check-deps
```

## Adding a color

Add an entry to `themes.json`:

```json
"Coral": {
  "body": "#4e2418",
  "primary": "#ff7f50",
  "watch": "#2e130a"
}
```

Then `fish scripts/compile_bibata_material.fish Coral` (or
`just build-one Coral`) to build just that one instead of all 28.

Some guidelines for picking colors that actually work:

- **Body**: dark, desaturated, roughly 10-25% lightness. This is the
  neutral fill, not a darker copy of your accent.
- **Primary**: the vibrant one. This carries the actual color.
- **Watch**: near-black, just needs to sit behind the outline.

Preview it with `gsettings set org.gnome.desktop.interface cursor-theme
Bibata-Material-Coral`, or `hyprctl setcursor Bibata-Material-Coral 24`
on Hyprland.

---

## Why body and primary are separate colors

Most themed-cursor setups just take an accent color and darken it for
the body. That's why a lot of them end up low-contrast or hard to see
depending on the wallpaper.

Here, body and primary are picked independently, following Material
Design 3's Container/Primary roles:

| M3 Role | Cursor part | What it does |
|---|---|---|
| Container | Body | Dark, desaturated fill. Stays legible regardless of how bright or saturated the accent is. |
| Primary | Outline | The actual accent color — vibrant, high-chroma. |

For Ice Blue:

```
Body    (Container) : #1a333d
Primary (Outline)   : #a8cbe2
Watch                : #0a1f26
```

The body isn't a darkened version of the primary — it's chosen on its
own. That's the whole point: it keeps contrast consistent across all
28 themes no matter how saturated the accent color is.

---

## Files

```
themes.json                     # all theme colors, edit this to add/change one
scripts/
├── compile_bibata_material.fish   # builds themes.json -> ~/.icons
├── metadata_generator.py       # writes index.theme so GNOME picks it up
└── package_release.sh          # bundles compiled themes for release
```

Build flow: clone `bibata_cursor`, patch its render config with each
theme's colors, compile, install to `~/.icons`, write `index.theme`
right after so a broken metadata file gets caught immediately instead
of at the end of a 28-theme run.

## Packaging a release

The repo doesn't hold compiled cursor binaries — those are
`.gitignore`d. For a GitHub Release or GNOME-Look.org upload, package
them separately after building:

```bash
bash scripts/package_release.sh v1.0.0
```

Writes `dist/bibata-material-v1.0.0.tar.gz` from whatever's in
`~/.icons`, with a plain-language `INSTALL.txt` inside for people who
never see this README. That archive is what you actually upload.

---

## License

Scripts and `themes.json` in this repo are MIT — see `LICENSE`.

The compiled cursor themes are a different story: they're derivative
of [Bibata_Cursor](https://github.com/rtgiskard/bibata_cursor), which
is GPLv3-or-later. If you redistribute compiled themes, that's under
GPLv3, not this repo's MIT license. Not legal advice — check the GPLv3
text if you need to know exactly what that means for your situation.
