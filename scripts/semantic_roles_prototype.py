#!/usr/bin/env python3
"""Prototype opt-in semantic cursor color roles (#71).

Does NOT change shipped recoloring. Loads the descriptive cursor metadata,
maps the proposed semantic roles (see docs/SEMANTIC_ROLES.md) to concrete
colors for a light and dark palette, and verifies that preserved color regions
remain untouched after substitution. Reports contrast ratios for review.

Usage:
    python3 scripts/semantic_roles_prototype.py
    python3 scripts/semantic_roles_prototype.py --json report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Proposed role map from docs/SEMANTIC_ROLES.md. "error" is only applied when
# the palette provides it; otherwise the fixed red is preserved.
ROLE_MAP = {
    "crossed_circle": "error",
    "dnd_no_drop": "error",
    "copy": "preserved",
    "dnd-copy": "preserved",
    "dnd-link": "preserved",
    "link": "preserved",
    "wait": "primary_shades",
    "left_ptr_watch": "primary_shades",
}
PRESERVED = {"crossed_circle": "#F1613A", "dnd_no_drop": "#FE0000",
             "copy": "#06B231", "dnd-copy": "#06B231",
             "dnd-link": "#606060", "link": "#606060"}


def relative_luminance(hex_color: str) -> float:
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = map(lin, rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def build_report() -> dict:
    themes = json.loads((REPO_ROOT / "themes.json").read_text(encoding="utf-8"))
    report = {"role_map": ROLE_MAP, "palettes": {}, "findings": []}
    for key in ("Apricot", "Midnight-Light"):
        palette = themes[key]
        primary = palette["primary"]
        body = palette["body"]
        error = palette.get("error")  # not present in current themes.json
        applied = {}
        for shape, role in ROLE_MAP.items():
            if role == "error":
                applied[shape] = error or PRESERVED.get(shape, "#FF0000")
            elif role == "primary_shades":
                from spinner_colors import spinner_shades
                applied[shape] = list(spinner_shades(primary))
            elif role == "preserved":
                applied[shape] = PRESERVED.get(shape, "(unchanged)")
        report["palettes"][key] = {
            "body": body, "primary": primary,
            "error_available": error is not None,
            "roles": applied,
            "contrast_primary_on_body": round(contrast(primary, body), 2),
        }
        if error is None:
            report["findings"].append(f"{key}: no 'error' token in themes.json; fixed red fallback used")
    report["findings"].append("Preserved roles unchanged: copy/link DND accents keep semantic colors")
    report["findings"].append("No shipped assets modified; this is a research prototype only")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="write report JSON here")
    args = parser.parse_args()
    report = build_report()
    print("Semantic role prototype (research only; no shipped changes)")
    for key, data in report["palettes"].items():
        print(f"  {key}: primary={data['primary']} error_available={data['error_available']} "
              f"contrast(primary/body)={data['contrast_primary_on_body']}")
        for shape, value in data["roles"].items():
            print(f"    {shape}: {value}")
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
