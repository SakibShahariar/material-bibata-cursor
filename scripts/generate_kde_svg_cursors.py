#!/usr/bin/env python3
"""
generate_kde_svg_cursors.py — adds a cursors_scalable/ directory (KDE
Plasma 6.2+'s native SVG cursor format) to already-compiled themes.

Per KDE's own spec (blog.vladzahorodnii.com, Oct 2024): a theme with SVG
cursors still needs Xcursor cursors too, as fallback for apps that don't
support the cursor-shape-v1 protocol — this only ADDS cursors_scalable/
alongside the existing cursors/, it never replaces it.

This does NOT re-render or approximate anything. It replicates exactly
what bibata_cursor's own build tool does internally (config/build.toml
for hotspot/alias data, svg/symlink.toml for which source file wins per
shape, plain text color substitution for recoloring) — same inputs,
same logic, just targeting KDE's on-disk format instead of Xcursor/
hyprcursor's.

Usage:
    python3 generate_kde_svg_cursors.py                    # all themes
    python3 generate_kde_svg_cursors.py --theme Ice-Blue    # just one
"""

import argparse
import json
import os
import shutil
import sys
import tomllib
from pathlib import Path

NOMINAL_SIZE = 256  # matches the actual SVG canvas size (verified: viewBox="0 0 256 256")
                     # — must match reality, NOT an arbitrary X11-style size like 24.
                     # KDE's own docs warn nominal_size can't be assumed equal to a
                     # "logical" cursor size; a mismatch here causes incorrect
                     # scaling (blurry cursors) since hotspot placement and the
                     # renderer's scale reference both derive from this value.


def resolve_source_dir(bibata_dir: Path, group_name: str) -> dict:
    """Replicates gen_res_symlinks' last-wins merge, without writing
    actual symlinks — just resolves, in memory, which real file wins
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
    does — colors[0]=body replaces #00FF00, colors[1]=primary replaces
    #0000FF, colors[2]=watch replaces #FF0000 (Bibata-Modern-Classic
    convention, same as compile_bibata_material.fish uses)."""
    svg_text = svg_text.replace("#00FF00", body)
    svg_text = svg_text.replace("#0000FF", primary)
    svg_text = svg_text.replace("#FF0000", watch)
    return svg_text


def generate_for_theme(bibata_dir: Path, install_dir: Path, theme_key: str,
                        body: str, primary: str, watch: str,
                        group_name: str = "modern") -> tuple[int, int]:
    theme_dir = install_dir / f"Bibata-Material-{theme_key}"
    if not theme_dir.is_dir():
        print(f"Skipping {theme_key}: not compiled at {theme_dir}", file=sys.stderr)
        return 0, 1

    with open(bibata_dir / "config" / "build.toml", "rb") as f:
        build_cfg = tomllib.load(f)

    defaults = build_cfg["cursor_defaults"]
    cursors_cfg = build_cfg["cursors"]
    resolved_sources = resolve_source_dir(bibata_dir, group_name)

    scalable_dir = theme_dir / "cursors_scalable"
    if scalable_dir.exists():
        shutil.rmtree(scalable_dir)
    scalable_dir.mkdir(parents=True)

    ok, failed = 0, 0
    # collect alias info for a second pass (symlinks need the real dir to exist first)
    aliases = []

    for shape_key, params in cursors_cfg.items():
        x11_name = params.get("x11_name", "")
        if not x11_name:
            continue

        png_ref = params.get("png", "")
        x_hotspot = params.get("x_hotspot", defaults["x_hotspot"])
        y_hotspot = params.get("y_hotspot", defaults["y_hotspot"])
        # x_hotspot/y_hotspot are already on a 0-256 scale (Bibata's own
        # convention), which now matches NOMINAL_SIZE exactly — no rescale.
        hotspot_x = round(x_hotspot)
        hotspot_y = round(y_hotspot)
        shape_dir = scalable_dir / x11_name

        is_animated = "*" in png_ref
        metadata = []
        frames_written = 0

        if is_animated:
            # e.g. 'wait-*.png' -> real frames live in a same-named
            # subdirectory as wait-01.svg, wait-02.svg, ... sorted.
            anim_dirname = png_ref.split("*")[0].rstrip("-")
            src_dir_path = resolved_sources.get(anim_dirname)
            if src_dir_path is None or not src_dir_path.is_dir():
                print(f"  Warning: no animation source dir for '{shape_key}' ({anim_dirname}), skipping", file=sys.stderr)
                failed += 1
                continue

            frame_files = sorted(src_dir_path.glob("*.svg"))
            if not frame_files:
                print(f"  Warning: animation dir '{anim_dirname}' has no SVG frames, skipping", file=sys.stderr)
                failed += 1
                continue

            shape_dir.mkdir(exist_ok=True)
            delay = params.get("x11_delay", defaults.get("x11_delay", 40))
            for frame_path in frame_files:
                try:
                    svg_text = frame_path.read_text()
                except OSError as e:
                    print(f"  Warning: failed to read {frame_path}: {e}", file=sys.stderr)
                    continue
                recolored = recolor_svg(svg_text, body, primary, watch)
                out_name = frame_path.name
                (shape_dir / out_name).write_text(recolored)
                metadata.append({
                    "filename": out_name,
                    "delay": delay,
                    "hotspot_x": hotspot_x,
                    "hotspot_y": hotspot_y,
                    "nominal_size": NOMINAL_SIZE,
                })
                frames_written += 1

            if frames_written == 0:
                failed += 1
                continue

        else:
            svg_basename = Path(png_ref).stem + ".svg" if png_ref else f"{shape_key}.svg"
            src_path = resolved_sources.get(svg_basename)
            if src_path is None or not src_path.is_file():
                print(f"  Warning: no source SVG for '{shape_key}' ({svg_basename}), skipping", file=sys.stderr)
                failed += 1
                continue

            shape_dir.mkdir(exist_ok=True)
            try:
                svg_text = src_path.read_text()
            except OSError as e:
                print(f"  Warning: failed to read {src_path}: {e}", file=sys.stderr)
                failed += 1
                continue

            recolored = recolor_svg(svg_text, body, primary, watch)
            (shape_dir / f"{x11_name}.svg").write_text(recolored)
            metadata = [{
                "filename": f"{x11_name}.svg",
                "hotspot_x": hotspot_x,
                "hotspot_y": hotspot_y,
                "nominal_size": NOMINAL_SIZE,
            }]

        (shape_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
        ok += 1

        for alias in params.get("x11_symlinks", []):
            aliases.append((alias, x11_name))

    # second pass: aliases as directory symlinks, per KDE spec
    for alias_name, target_name in aliases:
        alias_path = scalable_dir / alias_name
        target_path = scalable_dir / target_name
        if not target_path.is_dir():
            continue
        if alias_path.exists() or alias_path.is_symlink():
            continue
        try:
            alias_path.symlink_to(target_name)
        except OSError as e:
            print(f"  Warning: failed to symlink alias '{alias_name}': {e}", file=sys.stderr)

    return ok, failed


def main():
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    bibata_dir = script_dir / "bibata_cursor"
    default_install = os.environ.get("BIBATA_MATERIAL_INSTALL_DIR", str(Path.home() / ".icons"))
    default_themes_json = repo_root / "themes.json"

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--theme", default=None, help="Only generate for this theme (default: all in themes.json)")
    parser.add_argument("--install-dir", default=default_install)
    parser.add_argument("--themes-json", default=str(default_themes_json))
    args = parser.parse_args()

    if not bibata_dir.is_dir():
        print(f"Error: {bibata_dir} not found — run compile_bibata_material.fish at least once first "
              f"(it clones bibata_cursor as a build dependency).", file=sys.stderr)
        sys.exit(1)

    themes_path = Path(args.themes_json)
    if not themes_path.is_file():
        print(f"Error: themes.json not found at {themes_path}", file=sys.stderr)
        sys.exit(1)
    with open(themes_path) as f:
        all_themes = json.load(f)

    theme_keys = [args.theme] if args.theme else list(all_themes.keys())
    install_dir = Path(args.install_dir)

    total_ok, total_failed, themes_done = 0, 0, 0
    for key in theme_keys:
        if key not in all_themes:
            print(f"Error: '{key}' not found in themes.json", file=sys.stderr)
            sys.exit(1)
        colors = all_themes[key]
        print(f"Processing {key}...")
        ok, failed = generate_for_theme(
            bibata_dir, install_dir, key,
            colors["body"], colors["primary"], colors["watch"],
        )
        total_ok += ok
        total_failed += failed
        if ok > 0:
            themes_done += 1

    print(f"\nDone: {themes_done} theme(s), {total_ok} shapes written, {total_failed} skipped/failed.")
    if themes_done == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
