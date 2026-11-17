#!/usr/bin/env python3
"""Build a color-placeholder scalable cursor theme for the gallery download.

Produces the same cursors_scalable tree that generate_svg_cursors.py builds,
but with color literals replaced by {{TOKEN}} placeholders. The gallery
substitutes a user's chosen colors and zips the result into an installable
theme entirely in the browser.

The tree is stored as gzip+base64 in a JS file so the gallery page stays small
and needs no runtime fetches of individual SVGs.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BIBATA_DIR = REPO_ROOT / "scripts" / "bibata_cursor"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "customizer" / "theme-template.js"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_svg_cursors import NOMINAL_SIZE, resolve_source_dir, build_name_index, resolve_css_name
from generate_gallery_templates import REPLACEMENTS


def tokenize(svg_text: str) -> str:
    text = svg_text
    for match, token in REPLACEMENTS.items():
        text = text.replace(match, token)
    return text


def build_template_tree(bibata_dir: Path) -> dict:
    """Return {relative_path: content} for a placeholder scalable theme."""
    with open(bibata_dir / "config" / "build.toml", "rb") as f:
        build_cfg = tomllib.load(f)
    defaults = build_cfg["cursor_defaults"]
    cursors_cfg = build_cfg["cursors"]
    resolved = resolve_source_dir(bibata_dir, "modern")
    index = build_name_index(build_cfg)

    tree: dict[str, str] = {}
    css_links: dict[str, str] = {}
    real_dirs: set[str] = set()
    prefix = "Bibata-Material-Custom/cursors_scalable"

    for shape_key, params in cursors_cfg.items():
        x11_name = params.get("x11_name", "")
        if not x11_name:
            continue
        png_ref = params.get("png", "")
        x_hotspot = round(params.get("x_hotspot", defaults["x_hotspot"]))
        y_hotspot = round(params.get("y_hotspot", defaults["y_hotspot"]))
        delays = params.get("x11_delay", defaults.get("x11_delay", 40))
        delay_list = delays if isinstance(delays, list) else [delays]
        shape_dir = f"{prefix}/{x11_name}"
        real_dirs.add(x11_name)
        metadata = []

        if "*" in png_ref:
            anim_dirname = png_ref.split("*")[0].rstrip("-")
            src_dir = resolved.get(anim_dirname)
            if src_dir is None or not src_dir.is_dir():
                raise FileNotFoundError(f"no animation source dir for {shape_key} ({anim_dirname})")
            for i, frame_path in enumerate(sorted(src_dir.glob("*.svg"))):
                out_name = frame_path.name
                tree[f"{shape_dir}/{out_name}"] = tokenize(frame_path.read_text(encoding="utf-8"))
                metadata.append({
                    "filename": out_name,
                    "delay": delay_list[i % len(delay_list)],
                    "hotspot_x": x_hotspot,
                    "hotspot_y": y_hotspot,
                    "nominal_size": NOMINAL_SIZE,
                })
        else:
            svg_basename = Path(png_ref).stem + ".svg"
            src_path = resolved.get(svg_basename)
            if src_path is None or not src_path.is_file():
                raise FileNotFoundError(f"no source SVG for {shape_key} ({svg_basename})")
            tree[f"{shape_dir}/{x11_name}.svg"] = tokenize(src_path.read_text(encoding="utf-8"))
            metadata.append({
                "filename": f"{x11_name}.svg",
                "hotspot_x": x_hotspot,
                "hotspot_y": y_hotspot,
                "nominal_size": NOMINAL_SIZE,
            })
        tree[f"{shape_dir}/metadata.json"] = json.dumps(metadata, indent=2)

    # Alias directories (symlinks handled at unzip time in the browser).
    # Mirrors generate_svg_cursors.py: x11_symlinks plus CSS names, excluding
    # aliases that collide with a real shape directory.
    from generate_svg_cursors import CSS_CURSOR_NAMES
    for shape_key, params in cursors_cfg.items():
        x11_name = params.get("x11_name", "")
        if not x11_name:
            continue
        for alias in params.get("x11_symlinks", []):
            css_links.setdefault(alias, x11_name)
    for css_name in CSS_CURSOR_NAMES:
        shape = resolve_css_name(css_name, index)
        if shape and shape in real_dirs:
            css_links[css_name] = shape
    css_links = {alias: target for alias, target in css_links.items()
                 if target in real_dirs and alias != target and alias not in real_dirs}

    tree["Bibata-Material-Custom/index.theme"] = (
        "[Icon Theme]\nName=Bibata Material (Custom)\n"
        "Comment=Custom Material Bibata cursor theme\nInherits=hicolor\n"
    )
    tree["Bibata-Material-Custom/README.txt"] = (
        "Custom Material Bibata Cursor theme\n\n"
        "This is a scalable SVG cursor theme for GNOME 51+ and KDE Plasma 6.2+.\n"
        "Install: extract this folder into ~/.local/share/icons/ (create the\n"
        "directory if needed), then select 'Bibata Material (Custom)' in your\n"
        "desktop's cursor settings.\n\n"
        "For X11, Hyprland, and Windows cursor formats, add the palette to\n"
        "themes.json in the source repository and run 'just build' /\n"
        "'just build-win'.\n\n"
        "Derived cursor artwork is based on Bibata_Cursor (GPL-3.0-or-later).\n"
    )
    return {"files": tree, "css_links": css_links}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bibata-dir", type=Path, default=BIBATA_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        template = build_template_tree(args.bibata_dir)
    except (OSError, KeyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    blob = json.dumps(template).encode("utf-8")
    encoded = base64.b64encode(gzip.compress(blob, 9)).decode("ascii")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        f"window.GALLERY_THEME_TEMPLATE='{encoded}';\n", encoding="utf-8"
    )
    print(f"Wrote theme template ({len(template['files'])} files, {len(encoded)} base64 bytes) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
