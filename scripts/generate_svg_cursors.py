#!/usr/bin/env python3
"""
generate_svg_cursors.py — adds a cursors_scalable/ directory to compiled
Bibata-Material themes.

This is the scalable SVG cursor format used by both KDE Plasma 6.2+ and
GNOME 51+. GNOME Shell renders these in the compositor with librsvg
(src/st/st-cursor.c) and — unlike the legacy Xcursor loader — only
searches $XDG_DATA_HOME/icons and the system icon directories
(g_get_user_data_dir() / g_get_system_data_dirs()). ~/.icons is NOT on
that path, which is why this writes to $XDG_DATA_HOME/icons by default.

The on-disk format matches KDE's (blog.vladzahorodnii.com, Oct 2024):
  cursors_scalable/<shape>/some.svg
  cursors_scalable/<shape>/metadata.json
where metadata.json is a JSON array of frames
    { "filename", "delay", "hotspot_x", "hotspot_y", "nominal_size" }
Alias shapes are directories that symlink to a real shape directory.

Two naming schemes are produced from the same SVG sources:
  * One real directory per cursor shape in build.toml, named by its
    x11_name (what KDE and X11 apps look up), e.g. left_ptr.
  * Symlinked directories for the freedesktop/CSS cursor names that
    GNOME/Mutter look up (clutter_cursor_type_to_name), e.g. pointer,
    text, ew-resize — mapped to the same visual shapes the Xcursor
    fallback would show, so both renderers agree on appearance.

nominal_size is 256 because Bibata's SVGs are real 256x256 canvases with
hotspots on the same 0-256 coordinate space (x_hotspot/y_hotspot in
config/build.toml). It must NOT be "24 like Adwaita" — Adwaita's SVGs are
24-sized; a mismatch here breaks hotspot placement and scaling.

Like KDE's spec requires, the Xcursor cursors are left untouched as the
fallback for apps without cursor-shape-v1.

Usage:
    python3 generate_svg_cursors.py                     # all themes
    python3 generate_svg_cursors.py --theme Ice-Blue    # just one
"""

import argparse
import json
import os
import shutil
import sys
import tomllib
from pathlib import Path

NOMINAL_SIZE = 256  # matches the real SVG canvas size (24px canvas would be wrong)

# freedesktop/CSS cursor names as returned by ClutterCursorType's
# clutter_cursor_type_to_name() in mutter (the names GNOME 51 looks up).
CSS_CURSOR_NAMES = [
    "default", "context-menu", "help", "pointer", "progress", "wait",
    "cell", "crosshair", "text", "vertical-text", "alias", "copy",
    "move", "no-drop", "not-allowed", "grab", "grabbing",
    "e-resize", "n-resize", "ne-resize", "nw-resize",
    "s-resize", "se-resize", "sw-resize", "w-resize",
    "ew-resize", "ns-resize", "nesw-resize", "nwse-resize",
    "col-resize", "row-resize", "all-scroll", "zoom-in", "zoom-out",
    "dnd-ask", "all-resize",
]

# CSS name -> legacy X11 name, from mutter's meta_cursor_get_legacy_name()
# (src/backends/meta-cursor-xcursor.c). Used only when the CSS name itself
# doesn't appear in the theme's alias list.
CSS_TO_LEGACY = {
    "default": "left_ptr",
    "context-menu": "left_ptr",
    "help": "question_arrow",
    "pointer": "hand",
    "progress": "left_ptr_watch",
    "wait": "watch",
    "cell": "crosshair",
    "crosshair": "cross",
    "text": "xterm",
    "vertical-text": "xterm",
    "alias": "dnd-link",
    "copy": "dnd-copy",
    "move": "dnd-move",
    "no-drop": "dnd-none",
    "not-allowed": "crossed_circle",
    "grab": "hand2",
    "grabbing": "hand2",
    "e-resize": "right_side",
    "n-resize": "top_side",
    "ne-resize": "top_right_corner",
    "nw-resize": "top_left_corner",
    "s-resize": "bottom_side",
    "se-resize": "bottom_right_corner",
    "sw-resize": "bottom_left_corner",
    "w-resize": "left_side",
    "ew-resize": "h_double_arrow",
    "ns-resize": "v_double_arrow",
    "nesw-resize": "fd_double_arrow",
    "nwse-resize": "bd_double_arrow",
    "col-resize": "h_double_arrow",
    "row-resize": "v_double_arrow",
    "all-scroll": "left_ptr",
    "zoom-in": "left_ptr",
    "zoom-out": "left_ptr",
    "dnd-ask": "dnd-copy",
    "all-resize": "dnd-move",
}


def resolve_source_dir(bibata_dir: Path, group_name: str) -> dict:
    """Replicates bibata_cursor's gen_res_symlinks last-wins merge,
    without writing symlinks — resolves in memory which real file wins
    for each basename. Returns {basename: real Path}."""
    with open(bibata_dir / "svg" / "symlink.toml", "rb") as f:
        groups = tomllib.load(f)

    if group_name not in groups:
        raise ValueError(f"'{group_name}' not found in svg/symlink.toml")

    resolved = {}
    for src_dir in groups[group_name]:
        full_dir = bibata_dir / "svg" / src_dir
        if not full_dir.is_dir():
            continue
        for item in full_dir.iterdir():
            resolved[item.name] = item  # later dirs override earlier ones
    return resolved


def recolor_svg(svg_text: str, body: str, primary: str, watch: str) -> str:
    """Same plain text substitution bibata_cursor's Utils.svg_recolor
    does: body replaces #00FF00, primary replaces #0000FF, watch
    replaces #FF0000."""
    svg_text = svg_text.replace("#00FF00", body)
    svg_text = svg_text.replace("#0000FF", primary)
    svg_text = svg_text.replace("#FF0000", watch)
    return svg_text


def build_name_index(build_cfg: dict) -> dict:
    """Map every name that exists in a theme (x11_name or x11_symlink)
    to the first cursor shape that provides it: {name: shape_key}."""
    index = {}
    for shape_key, params in build_cfg["cursors"].items():
        x11_name = params.get("x11_name", "")
        if x11_name:
            index.setdefault(x11_name, shape_key)
        for alias in params.get("x11_symlinks", []):
            index.setdefault(alias, shape_key)
    return index


def resolve_css_name(css_name: str, index: dict) -> str | None:
    """Which shape provides the art for a freedesktop/CSS cursor name.
    Prefers an exact match (x11_name or symlink) so the SVG looks like
    what the Xcursor fallback draws (e.g. 'cell' is the plus shape here,
    not legacy 'crosshair'), then falls back to the legacy X11 name."""
    if css_name in index:
        return index[css_name]
    legacy = CSS_TO_LEGACY.get(css_name)
    if legacy in index:
        return index[legacy]
    return None


def generate_for_theme(bibata_dir: Path, install_dir: Path, scalable_dir: Path,
                       theme_key: str, body: str, primary: str, watch: str,
                       group_name: str = "modern") -> tuple[int, int]:
    theme_name = f"Bibata-Material-{theme_key}"
    scalable_theme = scalable_dir / theme_name
    scalable_sub = scalable_theme / "cursors_scalable"

    with open(bibata_dir / "config" / "build.toml", "rb") as f:
        build_cfg = tomllib.load(f)

    defaults = build_cfg["cursor_defaults"]
    cursors_cfg = build_cfg["cursors"]
    resolved_sources = resolve_source_dir(bibata_dir, group_name)
    index = build_name_index(build_cfg)

    if scalable_sub.exists():
        shutil.rmtree(scalable_theme)
    scalable_sub.mkdir(parents=True)

    ok, failed = 0, 0
    css_links = {}  # css_name -> real dir name
    real_dirs = set()

    # First pass: one real directory per shape with an x11_name.
    for shape_key, params in cursors_cfg.items():
        x11_name = params.get("x11_name", "")
        if not x11_name:
            continue

        png_ref = params.get("png", "")
        x_hotspot = round(params.get("x_hotspot", defaults["x_hotspot"]))
        y_hotspot = round(params.get("y_hotspot", defaults["y_hotspot"]))
        delays = params.get("x11_delay", defaults.get("x11_delay", 40))
        # A single numeric delay, or an array for variable-timing animation.
        delay_list = delays if isinstance(delays, list) else [delays]

        shape_dir = scalable_sub / x11_name
        metadata = []

        if "*" in png_ref:
            # e.g. 'wait-*.png' -> frames live in a 'wait' source dir.
            anim_dirname = png_ref.split("*")[0].rstrip("-")
            src_dir = resolved_sources.get(anim_dirname)
            if src_dir is None or not src_dir.is_dir():
                print(f"  Warning: no animation source dir for '{shape_key}' ({anim_dirname}), skipping",
                      file=sys.stderr)
                failed += 1
                continue

            frame_files = sorted(src_dir.glob("*.svg"))
            if not frame_files:
                print(f"  Warning: animation dir '{anim_dirname}' has no SVG frames, skipping",
                      file=sys.stderr)
                failed += 1
                continue

            shape_dir.mkdir(parents=True)
            for i, frame_path in enumerate(frame_files):
                recolored = recolor_svg(frame_path.read_text(), body, primary, watch)
                out_name = frame_path.name
                (shape_dir / out_name).write_text(recolored)
                metadata.append({
                    "filename": out_name,
                    "delay": delay_list[i % len(delay_list)],
                    "hotspot_x": x_hotspot,
                    "hotspot_y": y_hotspot,
                    "nominal_size": NOMINAL_SIZE,
                })
        else:
            svg_basename = Path(png_ref).stem + ".svg"
            src_path = resolved_sources.get(svg_basename)
            if src_path is None or not src_path.is_file():
                print(f"  Warning: no source SVG for '{shape_key}' ({svg_basename}), skipping",
                      file=sys.stderr)
                failed += 1
                continue

            shape_dir.mkdir(parents=True)
            recolored = recolor_svg(src_path.read_text(), body, primary, watch)
            (shape_dir / f"{x11_name}.svg").write_text(recolored)
            metadata = [{
                "filename": f"{x11_name}.svg",
                "hotspot_x": x_hotspot,
                "hotspot_y": y_hotspot,
                "nominal_size": NOMINAL_SIZE,
            }]

        (shape_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
        real_dirs.add(x11_name)
        ok += 1

        # Record CSS names that share this shape's art.
        shape_css = [css for css in CSS_CURSOR_NAMES if css == x11_name or resolve_css_name(css, index) == shape_key]
        for css_name in shape_css:
            css_links[css_name] = x11_name

    # Second pass: alias directories as symlinks (KDE spec: aliases are
    # symlinks). Covers x11_symlinks (X11/KDE lookups) plus the CSS names
    # GNOME looks up by ClutterCursorType.
    aliases = {}
    for shape_key, params in cursors_cfg.items():
        x11_name = params.get("x11_name", "")
        if not x11_name:
            continue
        for alias in params.get("x11_symlinks", []):
            aliases.setdefault(alias, x11_name)
    aliases.update(css_links)

    for alias, target in aliases.items():
        if alias == target or alias in real_dirs:
            continue
        alias_path = scalable_sub / alias
        if alias_path.exists() or alias_path.is_symlink():
            continue
        try:
            alias_path.symlink_to(target)
        except OSError as e:
            print(f"  Warning: failed to symlink alias '{alias}': {e}", file=sys.stderr)

    # Make the scalable tree a complete, recognizable theme for KDE/tools:
    # symlink the Xcursor fallback and index.theme from the compiled theme.
    installed_theme = install_dir / theme_name
    for entry in ("cursors", "index.theme"):
        src = installed_theme / entry
        dst = scalable_theme / entry
        if src.exists() and not dst.exists() and (installed_theme.resolve() != scalable_theme.resolve()):
            try:
                dst.symlink_to(str(src))
            except OSError as e:
                print(f"  Warning: failed to symlink {entry}: {e}", file=sys.stderr)

    return ok, failed


def default_scalable_dir(install_dir: Path) -> Path:
    """GNOME/KDE look for cursors_scalable/ only in XDG data dirs, never
    ~/.icons. If installing system-wide we use the same tree, otherwise
    $XDG_DATA_HOME/icons (~/.local/share/icons)."""
    env = os.environ.get("BIBATA_MATERIAL_SCALABLE_DIR")
    if env:
        return Path(env).expanduser()
    try:
        install_resolved = install_dir.resolve()
    except OSError:
        install_resolved = install_dir
    xdg_icons = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "icons"
    if any(install_resolved.is_relative_to(p) for p in (Path("/usr/share/icons"), Path("/usr/local/share/icons"))):
        return install_dir
    return xdg_icons


def main():
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    bibata_dir = script_dir / "bibata_cursor"
    default_install = os.environ.get("BIBATA_MATERIAL_INSTALL_DIR", str(Path.home() / ".icons"))
    default_themes_json = repo_root / "themes.json"

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--theme", default=None, help="Only generate for this theme (default: all in themes.json)")
    parser.add_argument("--install-dir", default=default_install,
                        help="Where the compiled Xcursor themes live (used for fallback symlinks)")
    parser.add_argument("--scalable-dir", default=None,
                        help="Where to write cursors_scalable/ (default: $XDG_DATA_HOME/icons, or install-dir if system-wide)")
    parser.add_argument("--themes-json", default=str(default_themes_json))
    parser.add_argument("--bibata-dir", default=str(bibata_dir))
    args = parser.parse_args()

    bibata_dir = Path(args.bibata_dir)
    if not bibata_dir.is_dir():
        print(f"Error: {bibata_dir} not found — run compile_bibata_material.fish at least once first "
              "(it clones bibata_cursor as a build dependency).", file=sys.stderr)
        sys.exit(1)

    themes_path = Path(args.themes_json)
    if not themes_path.is_file():
        print(f"Error: themes.json not found at {themes_path}", file=sys.stderr)
        sys.exit(1)
    with open(themes_path) as f:
        all_themes = json.load(f)

    theme_keys = [args.theme] if args.theme else list(all_themes.keys())
    install_dir = Path(args.install_dir).expanduser()
    scalable_dir = Path(args.scalable_dir).expanduser() if args.scalable_dir else default_scalable_dir(install_dir)

    total_ok, total_failed, themes_done = 0, 0, 0
    for key in theme_keys:
        if key not in all_themes:
            print(f"Error: '{key}' not found in themes.json", file=sys.stderr)
            sys.exit(1)
        colors = all_themes[key]
        try:
            body, primary, watch = colors["body"], colors["primary"], colors["watch"]
        except KeyError:
            print(f"Skipping '{key}': missing body/primary/watch colors", file=sys.stderr)
            continue
        print(f"Processing {key}...")
        ok, failed = generate_for_theme(
            bibata_dir, install_dir, scalable_dir, key,
            body, primary, watch,
        )
        total_ok += ok
        total_failed += failed
        if ok > 0:
            themes_done += 1

    print(f"\nDone: {themes_done} theme(s), {total_ok} shapes written, {total_failed} skipped/failed.")
    print(f"SVG cursors installed to: {scalable_dir}")
    if themes_done == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()