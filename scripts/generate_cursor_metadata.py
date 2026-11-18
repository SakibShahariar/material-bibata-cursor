#!/usr/bin/env python3
"""Generate cursor-metadata.json from current sources (#70, migration step 1).

The generated file is initially *descriptive* — builders keep using their
current inputs. This makes the implicit metadata explicit and reviewable, and
provides a parity check (step 2) against the shipped outputs.

Usage:
    python3 scripts/generate_cursor_metadata.py
    python3 scripts/generate_cursor_metadata.py --check   # verify file is current
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BIBATA_DIR = REPO_ROOT / "scripts" / "bibata_cursor"
DEFAULT_OUTPUT = REPO_ROOT / "scripts" / "cursor-metadata.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_svg_cursors import CSS_CURSOR_NAMES, build_name_index, resolve_css_name
from source_provenance import UPSTREAM_COMMIT, UPSTREAM_REPOSITORY
from spinner_colors import CORNER_MATCHES, RAINBOW_MATCHES
from validate_theme_assets import EXPECTED_XCURSOR_SIZES

# Mirrored/remap classification from the reviewed left-handed research (#72).
REMAP_PAIRS = {
    "left_side": "right_side", "right_side": "left_side",
    "left_tee": "right_tee", "right_tee": "left_tee",
    "bottom_left_corner": "bottom_right_corner", "bottom_right_corner": "bottom_left_corner",
    "top_left_corner": "top_right_corner", "top_right_corner": "top_left_corner",
    "ll_angle": "lr_angle", "lr_angle": "ll_angle",
    "ul_angle": "ur_angle", "ur_angle": "ul_angle",
    "sb_left_arrow": "sb_right_arrow", "sb_right_arrow": "sb_left_arrow",
    "sb_down_arrow": "sb_up_arrow", "sb_up_arrow": "sb_down_arrow",
    "left_ptr": "right_ptr", "right_ptr": "left_ptr",
    "bottom_side": "top_side", "top_side": "bottom_side",
    "bottom_tee": "top_tee", "top_tee": "bottom_tee",
}
DO_NOT_MIRROR = {"xterm", "person", "pin", "wait", "left_ptr_watch"}
MANUAL_REVIEW = {"hand1", "hand2", "grabbing", "pencil", "question_arrow", "context-menu",
                 "circle", "copy", "link", "pointer-move", "dnd-ask", "dnd-copy",
                 "dnd-link", "dnd_no_drop", "vertical-text"}
WINDOWS_SIZES = (16, 24, 32, 48, 64, 128)


def build_metadata() -> dict:
    cfg = tomllib.loads((BIBATA_DIR / "config" / "build.toml").read_text(encoding="utf-8"))
    defaults = cfg["cursor_defaults"]
    render = json.loads((BIBATA_DIR / "config" / "render.json").read_text(encoding="utf-8"))["Bibata-Modern-Classic"]
    index = build_name_index(cfg)

    cursors = {}
    for shape_key, params in cfg["cursors"].items():
        x11 = params.get("x11_name", "")
        aliases = sorted(set(params.get("x11_symlinks", [])))
        css = sorted(css for css in CSS_CURSOR_NAMES
                     if css == x11 or resolve_css_name(css, index) == shape_key)
        if x11 in DO_NOT_MIRROR:
            handedness = "do-not-mirror"
        elif x11 in MANUAL_REVIEW:
            handedness = "manual-review"
        elif x11 in REMAP_PAIRS:
            handedness = "remap:" + REMAP_PAIRS[x11]
        else:
            handedness = "mirror-safe"
        cursors[x11 or shape_key] = {
            "source_svg": params.get("png", "").split("*")[0].rstrip("-"),
            "aliases": aliases,
            "css_aliases": [c for c in css if c != x11],
            "hotspot": [params.get("x_hotspot", defaults["x_hotspot"]),
                        params.get("y_hotspot", defaults["y_hotspot"])],
            "nominal_size": 256,
            "color_roles": {
                "body": render["colors"][0]["match"],
                "primary": render["colors"][1]["match"],
                "watch": render["colors"][2]["match"],
                "spinner_shades": list(RAINBOW_MATCHES),
                "corner_shades": list(CORNER_MATCHES),
            },
            "handedness": handedness,
            "sizes": {"xcursor": sorted(EXPECTED_XCURSOR_SIZES), "windows": list(WINDOWS_SIZES)},
            "animation": {
                "frame_glob": params["png"], "frame_dir": params.get("png", "").split("*")[0].rstrip("-"),
                "delay_ms": params.get("x11_delay", defaults["x11_delay"]),
                "windows_delay_multiplier": 2,
                "loop": True,
            } if "*" in params.get("png", "") else None,
        }
    return {
        "schema_version": 1,
        "source": {"upstream": UPSTREAM_REPOSITORY, "commit": UPSTREAM_COMMIT},
        "cursors": cursors,
        "notes": "Descriptive metadata generated from current sources; builders still use build.toml/scripts.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="exit 1 if the committed file is stale")
    args = parser.parse_args()
    generated = build_metadata()
    if args.check:
        if not args.output.is_file():
            print(f"error: missing {args.output}", file=sys.stderr)
            return 1
        committed = json.loads(args.output.read_text(encoding="utf-8"))
        if committed != generated:
            print(f"error: {args.output} is stale; run 'just cursor-metadata'", file=sys.stderr)
            return 1
        print(f"OK: {args.output} matches current sources ({len(generated['cursors'])} cursors)")
        return 0
    args.output.write_text(json.dumps(generated, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} ({len(generated['cursors'])} cursors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
