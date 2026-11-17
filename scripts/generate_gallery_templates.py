#!/usr/bin/env python3
"""Generate recolorable SVG templates for the gallery's theme customizer.

The gallery's regular previews are rendered PNG/WebP images in each shipped
theme's colors, which a browser cannot recolor. This script takes the pinned
upstream cursor SVGs and replaces their color literals with placeholder tokens
so the gallery can substitute a user's chosen colors live.

Usage:
    python3 scripts/generate_gallery_templates.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SVG_ROOT = REPO_ROOT / "scripts" / "bibata_cursor" / "svg"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "customizer"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from spinner_colors import CORNER_MATCHES, RAINBOW_MATCHES

# Upstream match color -> placeholder token used in the templates.
REPLACEMENTS: dict[str, str] = {
    "#00FF00": "{{BODY}}",
    "#0000FF": "{{PRIMARY}}",
    "#FF0000": "{{WATCH}}",
}
for _index, _color in enumerate(RAINBOW_MATCHES):
    REPLACEMENTS[_color] = f"{{{{SPINNER{_index}}}}}"
for _index, _color in enumerate(CORNER_MATCHES):
    REPLACEMENTS[_color] = f"{{{{CORNER{_index}}}}}"

# Template name -> upstream source file (relative to SVG_ROOT).
SOURCES: dict[str, str] = {
    "left_ptr": "groups/modern/left_ptr.svg",
    "xterm": "groups/shared/xterm.svg",
    "bd_double_arrow": "groups/modern-arrow/bd_double_arrow.svg",
    "wait": "groups/shared/wait/wait-01.svg",
    "bottom_right_corner": "groups/shared/bottom_right_corner.svg",
}


def build_template(source: Path) -> str:
    text = source.read_text(encoding="utf-8")
    for match, token in REPLACEMENTS.items():
        text = text.replace(match, token)
    return text


def js_string(text: str) -> str:
    """Encode text as a JS string literal (single-quoted, escaped)."""
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"


def generate(svg_root: Path, output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    templates: dict[str, str] = {}
    for name, relative in SOURCES.items():
        source = svg_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"upstream SVG not found: {source}")
        text = build_template(source)
        (output_dir / f"{name}.svg").write_text(text, encoding="utf-8")
        templates[name] = text
        written.append(f"{name}.svg")
    # Also emit a JS module with templates embedded so the gallery needs no
    # runtime fetches (works from file:// as well as HTTP).
    js = "window.GALLERY_TEMPLATES = {\n"
    js += "".join(f"  {js_string(name)}: {js_string(text)},\n" for name, text in templates.items())
    js += "};\n"
    (output_dir / "templates.js").write_text(js, encoding="utf-8")
    written.append("templates.js")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg-root", type=Path, default=SVG_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        written = generate(args.svg_root, args.output_dir)
    except OSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {len(written)} gallery templates to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
