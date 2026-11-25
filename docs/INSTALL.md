# Install and select a cursor theme

Material Bibata Cursor ships **57 themes**: 28 dark palettes, their 28
matching `-Light` variants, and `Classic` (the original Bibata colors).

- [Interactive gallery](https://sakibshahariar.github.io/material-bibata-cursor/) — preview every palette and build a custom theme.
- [Latest release](https://github.com/SakibShahariar/material-bibata-cursor/releases/latest) — prebuilt archives (Linux `tar.gz` and Windows `zip`).

The theme name used by every desktop below is `Bibata-Material-<Palette>`,
for example `Bibata-Material-Apricot` or `Bibata-Material-Seafoam-Light`.

> [!TIP]
> For Nix, you can use the [package from *nix-dryBoil*][dryboil-pkg], a 3rd-party flake.

[dryboil-pkg]: https://github.com/Drazape/nix-dryBoil/tree/main/packages/material-bibata-cursor "GitHub tree path (with README) for the package in nix-dryBoil flake"

## 1. Get the themes

**Prebuilt (recommended):** download the dark or light archive from the
latest release and extract it. Each archive contains a folder per theme.

**From source:** see the [build from source](../README.md#build-from-source)
section; `just build` installs all 57 themes locally.

## 2. Install per desktop

### GNOME (Wayland or X11)

GNOME 51+ reads scalable SVG cursors from the XDG icon directory; older
versions use the Xcursor fallback. Both are installed by the archives.

1. Copy the `Bibata-Material-*` folders into `~/.local/share/icons/`
   (create it if needed). A system-wide install uses `/usr/share/icons/`.
2. Select the theme:

   ```sh
   gsettings set org.gnome.desktop.interface cursor-theme 'Bibata-Material-Apricot'
   ```

   Or use **Settings → Appearance → Cursor**.

3. Change size if needed:

   ```sh
   gsettings set org.gnome.desktop.interface cursor-size 32
   ```

   GNOME on Wayland may require **Settings → Displays → Scale** for
   fractional scaling (125/150/200%).

### KDE Plasma 6.2+

1. Copy the `Bibata-Material-*` folders into `~/.local/share/icons/`.
2. Go to **System Settings → Appearance → Cursor** and pick the theme, or:

   ```sh
   plasma-apply-cursortheme Bibata-Material-Apricot
   ```

3. Size is under the same Cursor settings page (24, 32, 48, 64px options).

### Hyprland

1. Copy the `Bibata-Material-*` folders into `~/.icons/` (Hyprcursor lives
   alongside Xcursor there).
2. Add to `~/.config/hypr/hyprland.conf`:

   ```conf
   cursor {
       theme = Bibata-Material-Apricot
       size = 24
   }
   ```

   Or apply live with `hyprctl setcursor Bibata-Material-Apricot 24`.

### Niri

Copy the `Bibata-Material-*` folders into `~/.local/share/icons/` and add a
cursor block to `~/.config/niri/config.kdl`:

```kdl
cursor {
    xcursor-theme "Bibata-Material-Apricot"
    xcursor-size 24
}
```

If you use the Matugen hook, see [Niri support](MATUGEN.md#niri-support) for
the opt-in include that updates the theme automatically.

### Umbriel

Copy the `Bibata-Material-*` folders into `~/.local/share/icons/` and set the
cursor in `~/.config/umbriel/config.toml` (or via
`umbriel config set input.cursor.theme "Bibata-Material-Apricot"`):

```toml
[input.cursor]
theme = "Bibata-Material-Apricot"
size = 24
```

If you use the Matugen hook, see [Umbriel support](MATUGEN.md#umbriel-support)
for the opt-in include that updates the theme automatically.

### Windows

Download a `-win.zip` from the latest release. For each theme folder,
right-click `Install.inf` → **Install** (administrator prompt required), then
pick the scheme in **Settings → Devices → Mouse → Additional mouse settings
→ Pointers**. Alternatively copy the folder to `%LOCALAPPDATA%\Icons\` and
select it there. See [Windows cursors](WINDOWS.md) for details and the
manual smoke checklist.

## 3. Identify and select the installed theme

`just list` in a source checkout prints all 57 names. On any desktop, theme
names are case-sensitive: `Bibata-Material-` + the palette name as shown in
the gallery, with `-Light` for light variants. Applying a theme does not
rename files — the folder name is the theme name.

## 4. Troubleshooting

- **Theme not applying / pointer still default:** log out and back in (the
  Xcursor cache is loaded at session start). On Wayland, restart the shell
  if needed. Verify the exact folder name in `~/.local/share/icons/` or
  `~/.icons/`.
- **Stale icon cache:** run `gtk-update-icon-cache -f ~/.local/share/icons`
  (or the system icon dir) and restart the session.
- **Scalable cursors not picked up (GNOME 51+/KDE 6.2+):** ensure the
  `cursors_scalable/` tree is under `~/.local/share/icons/`, not `~/.icons/`
  — GNOME's compositor does not scan `~/.icons` for scalable cursors.
- **Fractional scaling looks soft:** see the
  [cursor size and scaling notes](SVG_CURSORS.md) — the shipped Xcursor ladder
  covers the common sizes; apps that need an exact intermediate size will
  scale the nearest bitmap.
- **Wrong theme size:** adjust the desktop cursor-size setting (GNOME/KDE)
  or the `size` value in Hyprland rather than replacing files.

## 5. Live validation status

Runtime visual checks are tracked in [the support matrix](SUPPORT.md).
Hotspots at 125/150/200% were verified on GNOME (see #38) and the animation
contract is asserted in CI. See [compatibility](COMPATIBILITY.md) for the
CSS/Wayland shape-name mapping and known gaps.
