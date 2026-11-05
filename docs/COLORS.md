# Adding a color

Add an entry to the repository-root `themes.json`:

```json
"Coral": {
  "label": "Coral",
  "body": "#4e2418",
  "primary": "#ff7f50",
  "watch": "#2e130a"
}
```

Then build just that theme:

```bash
python3 scripts/build_linux.py Coral
# or
just build-one Coral
```

## Color roles

| Role | Cursor part | Purpose |
|---|---|---|
| `body` | Container | Dark, desaturated fill |
| `primary` | Outline | Vibrant accent color |
| `watch` | Busy indicator | Background behind the spinner |

## Choosing colors

- **Body**: dark and desaturated, roughly 10–25% lightness. This is the
  neutral fill, not a darker copy of your accent.
- **Primary**: the vibrant color. This carries the actual hue.
- **Watch**: derived for dark themes by setting its CIELAB lightness to
  50% of the body lightness while preserving the body hue and chroma.
  `Classic` is exempt and keeps its original upstream colors.

## Why body and primary are separate

Most themed-cursor setups darken a single accent color and call it a day —
fine against some wallpapers, invisible against others. Picking body and
primary independently keeps the cursor legible no matter how bright or
saturated the accent is.

For Ice Blue: `Body #1a333d` · `Primary #a8cbe2` · `Watch #001e27`.

The same treatment is applied to every palette, so contrast stays consistent
across all 28 themes.

## Preview

```bash
gsettings set org.gnome.desktop.interface cursor-theme Bibata-Material-Coral
```

On Hyprland:

```bash
hyprctl setcursor Bibata-Material-Coral 24
```
