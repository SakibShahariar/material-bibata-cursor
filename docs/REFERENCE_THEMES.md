# Modern cursor theme reference audit

This is a one-time comparison of maintained cursor projects. It records
formats, shape naming, scaling, hotspots, animation, and install conventions
that are relevant to Material Bibata. No third-party artwork is copied.

## Reference projects

### KDE Breeze / Breeze Light

- **Formats:** SVG source, Plasma's scalable cursor tree, and generated
  Xcursor files. Plasma 6.2 introduced SVG cursor themes; Xcursor remains
  available for compatibility.
- **Sizes:** KDE's fractional-scaling example renders a 24-logical-pixel
  cursor at physical sizes 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, and
  72px (0.5x through 3x). This supports the exact-size strategy already
  used by Material Bibata.
- **Shapes and aliases:** Xcursor themes use files plus symlinks for aliases;
  the scalable format carries per-cursor metadata. Keep CSS/Wayland names
  distinct from the underlying X11 shape names.
- **Hotspots and animation:** The SVG cursor format uses metadata alongside
  frames. This scan did not establish a single shared canvas size or a
  complete Breeze animation inventory, so no values are inferred here.
- **Install:** Plasma looks for cursor themes in XDG icon directories such
  as `~/.local/share/icons`.

References: [KDE SVG cursor overview](https://planet.kde.org/vlad-zahorodnii-2024-10-06-svg-cursors-everything-that-you-need-to-know-about-them/),
[KDE fractional-scaling size explanation](https://blogs.kde.org/2024/10/09/cursor-size-problems-in-wayland-explained/).

### GNOME Adwaita

- **Formats:** The current Adwaita icon-theme repository separates legacy
  Xcursor sources/tooling into the `adwaita-icon-theme-legacy` module.
  Its build history also records a Windows cursor build fix.
- **Sizes:** KDE's format overview uses Adwaita as an example with Xcursor
  sizes 24, 32, 48, 64, and 96px.
- **Shapes and aliases:** Adwaita maintains an explicit CSS-to-X11 alias
  map. Examples include `pointer` → `hand2`, `context-menu` →
  `dnd-ask`, `wait` → `watch`, and resize directions to their X11
  side/corner cursors. It maps `all-resize` to `fleur`, which is a
  meaningful difference from Material Bibata's current `grabbing`
  fallback and should be reviewed under #44.
- **Hotspots and animation:** The source has per-cursor artwork/configuration;
  recent release notes mention spinner updates and cursor-name cleanup.
  Exact frame counts and hotspot conventions were not established in this
  reference pass.
- **Install:** Standard icon-theme directories are used; the KDE overview
  describes XDG icon locations such as `~/.local/share/icons`.

References: [Adwaita source repository](https://github.com/GNOME/adwaita-icon-theme),
[Adwaita cursor alias map](https://github.com/GNOME/adwaita-icon-theme/blob/master/meson.build),
[Adwaita release notes](https://github.com/GNOME/adwaita-icon-theme/blob/master/NEWS).

### Capitaine Cursors (HiDPI reference)

- **Formats:** Xcursor output from editable SVG sources, plus a Windows
  build with an INF installer.
- **Sizes:** A 24px SVG base is rendered at scale factors 1, 1.25, 1.5,
  2, 2.5, 3, 4, 5, 6, and 10 — corresponding to 24, 30, 36, 48, 60,
  72, 96, 120, 144, and 240px.
- **Shapes and aliases:** The project is inspired by KDE Breeze; it keeps
  source specifications and aliases in its own build tree. No extra CSS
  shape requirement was identified by this scan.
- **Hotspots and animation:** Hotspots are scaled with the source artwork.
  The public build documentation does not define a cross-theme animation
  contract, so Material Bibata's animation checks remain project-specific.
- **Install:** User themes go under `~/.icons`; system-wide themes go
  under `/usr/share/icons`. Windows uses the included INF installer.

References: [Capitaine Cursors repository and DPI table](https://github.com/keeferrourke/capitaine-cursors),
[Capitaine build script](https://github.com/keeferrourke/capitaine-cursors/blob/master/build.sh).

### Rosé Pine Hyprcursor (Hyprcursor reference)

- **Formats:** The example is packaged for Hyprcursor and includes an
  uncompressed SVG source tree for editing. Its README identifies it as a
  dark-only remix of BreezeX; it is not a general Xcursor/Windows package.
- **Sizes:** Hyprcursor stores multiple image sizes per cursor and declares
  a per-cursor resize algorithm rather than requiring one global bitmap
  ladder. The example does not publish a fixed size list.
- **Shapes and aliases:** Each cursor has its own directory and metadata;
  the manifest names the theme and cursor directory.
- **Hotspots and animation:** Hyprcursor metadata expresses hotspots as
  normalized 0–1 coordinates and supports per-cursor resize choices such
  as bilinear, nearest, or closest-size selection. Do not copy these values
  directly into Material Bibata's 256-unit SVG metadata without conversion.
- **Install:** Hyprland looks in `~/.local/share/icons` or `~/.icons`;
  the selected theme is configured with `HYPRCURSOR_THEME` and
  `HYPRCURSOR_SIZE`. Xcursor fallback is still needed for applications
  that do not support Hyprcursor.

References: [Hyprcursor user guide](https://wiki.hypr.land/hypr-ecosystem/user/hyprcursor/),
[Hyprcursor theme authoring](https://github.com/hyprwm/hyprcursor/blob/main/docs/MAKING_THEMES.md),
[Rosé Pine Hyprcursor example](https://github.com/ndom91/rose-pine-hyprcursor).

## Material Bibata baseline and resulting gaps

The current build uses the pinned Bibata upstream revision
[`f4ccfe8abb63fddc7b3ce51a866fd8378395cb3d`](https://github.com/rtgiskard/bibata_cursor/tree/f4ccfe8abb63fddc7b3ce51a866fd8378395cb3d).
The source tree is still fetched/materialized by the build tooling rather
than checked into this repository; full in-repository vendoring remains
tracked by #40.

- **Formats:** Xcursor, Hyprcursor, scalable SVG, and Windows `.cur` /
  `.ani`.
- **Sizes:** Xcursor 12, 16, 18, 20, 22, 24, 28, 30, 32, 36, 42, 48,
  54, 60, 64, 66, 72, 84, and 96px; Windows `.cur` 16, 24, 32, 48,
  64, and 128px; SVG source canvas 256 units.
- **Hotspots and animation:** SVG frame metadata uses absolute 256-unit
  hotspot coordinates. `wait` and `left_ptr_watch` are 54-frame
  animations at 40ms per frame.
- **Install:** Xcursor and Hyprcursor are installed under `~/.icons`;
  scalable SVG assets go under `~/.local/share/icons`; Windows assets
  are installed through each theme's `Install.inf`.

### Findings fed into the compatibility matrix

1. The reference sweep did not reveal an additional required CSS or
   Wayland cursor-shape-v1 name beyond the current matrix. Adwaita's
   aliases provide useful cross-checks for names already listed.
2. **Review `all-resize`:** Adwaita uses `fleur`, while Material Bibata
   currently resolves this name to `grabbing`. This is a semantic gap,
   not a reason to silently change the mapping; #44 tracks whether to add
   dedicated move/resize art or choose an explicit alias.
3. Keep the exact-size Xcursor ladder: KDE's documented fractional-scaling
   workaround and Capitaine's DPI strategy both reinforce shipping exact
   physical sizes where source SVGs are available.
4. Keep the Hyprcursor metadata contract separate from SVG metadata:
   normalized hotspots and resize algorithms need explicit conversion and
   validation.
5. Keep Windows `.cur` / `.ani` generation and installer mapping as a
   separate output target; do not assume an Xcursor/Hyprcursor package
   provides Windows assets.
