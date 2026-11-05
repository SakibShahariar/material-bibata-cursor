#!/usr/bin/env python3
"""Generate the dark/light palette comparison sheets from Bibata's real SVG pointer."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "scripts" / "bibata_cursor" / "svg" / "groups" / "modern" / "left_ptr.svg"
DEFAULT_THEMES = ROOT / "themes.json"
DEFAULT_OUTPUT = ROOT / "docs"
UPSTREAM_BODY = "#00FF00"
UPSTREAM_PRIMARY = "#0000FF"
COLUMNS = 4
CARD_WIDTH = 286
CARD_HEIGHT = 146
GAP = 16
MARGIN = 40
HEADER_HEIGHT = 108
FOOTER_HEIGHT = 58


def load_pointer_path(source_svg: Path) -> str:
    """Read the pinned Bibata Modern left_ptr shape and verify its color slots."""
    try:
        root = ET.parse(source_svg).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ValueError(
            f"cannot read {source_svg}; run 'just vendor' first: {exc}"
        ) from exc
    path = next(
        (node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "path"),
        None,
    )
    if path is None:
        raise ValueError(f"no path element found in {source_svg}")
    if path.get("fill", "").upper() != UPSTREAM_BODY:
        raise ValueError("upstream pointer fill slot changed; review matrix generator")
    if path.get("stroke", "").upper() != UPSTREAM_PRIMARY:
        raise ValueError("upstream pointer stroke slot changed; review matrix generator")
    path_data = path.get("d")
    if not path_data:
        raise ValueError("upstream pointer path has no geometry")
    return path_data


def build_matrix_svg(
    themes: dict[str, dict[str, str]], path_data: str, mode: str
) -> str:
    """Build a 28-card SVG contact sheet using real Bibata pointer geometry."""
    if mode not in {"dark", "light"}:
        raise ValueError(f"unsupported mode: {mode}")
    entries = [
        (name, palette)
        for name, palette in themes.items()
        if name != "Classic"
        and (name.endswith("-Light") if mode == "light" else not name.endswith("-Light"))
    ]
    if len(entries) != 28:
        raise ValueError(f"expected 28 {mode} palettes, found {len(entries)}")

    page_bg = "#141b20" if mode == "light" else "#edf1f4"
    card_bg = "#202a31" if mode == "light" else "#ffffff"
    ink = "#edf3f6" if mode == "light" else "#18232c"
    muted = "#aab8c1" if mode == "light" else "#64727d"
    width = MARGIN * 2 + COLUMNS * CARD_WIDTH + (COLUMNS - 1) * GAP
    rows = (len(entries) + COLUMNS - 1) // COLUMNS
    height = HEADER_HEIGHT + rows * CARD_HEIGHT + (rows - 1) * GAP + FOOTER_HEIGHT

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Material Bibata {mode} palette comparison">',
        f'<rect width="{width}" height="{height}" fill="{page_bg}"/>',
        f'<text x="{MARGIN}" y="48" fill="{ink}" font-family="Inter, Noto Sans, sans-serif" font-size="30" font-weight="700">Material Bibata · {mode.title()} palettes</text>',
        f'<text x="{MARGIN}" y="77" fill="{muted}" font-family="Inter, Noto Sans, sans-serif" font-size="14">28 palettes · real Bibata pointer geometry · body fill and primary outline</text>',
    ]
    for index, (name, palette) in enumerate(entries):
        x = MARGIN + (index % COLUMNS) * (CARD_WIDTH + GAP)
        y = HEADER_HEIGHT + (index // COLUMNS) * (CARD_HEIGHT + GAP)
        label = html.escape(palette.get("label", name.replace("-", " ")))
        body = palette["body"].upper()
        primary = palette["primary"].upper()
        watch = palette["watch"].upper()
        parts.extend([
            f'<g data-theme="{html.escape(name)}">',
            f'<rect x="{x}" y="{y}" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="14" fill="{card_bg}" stroke="{muted}" stroke-opacity=".35"/>',
            f'<text x="{x + 18}" y="{y + 29}" fill="{ink}" font-family="Inter, Noto Sans, sans-serif" font-size="16" font-weight="650">{label}</text>',
            f'<g transform="translate({x + 18} {y + 48}) scale(.25)">',
            f'<path d="{path_data}" fill="{body}" stroke="{primary}" stroke-width="17" stroke-linejoin="round"/>',
            '</g>',
        ])
        swatches = [("Body", body), ("Primary", primary), ("Watch", watch)]
        for swatch_index, (swatch_label, color) in enumerate(swatches):
            sx = x + 100 + swatch_index * 60
            parts.extend([
                f'<rect x="{sx}" y="{y + 76}" width="12" height="12" rx="3" fill="{color}" stroke="{muted}" stroke-opacity=".6"/>',
                f'<text x="{sx - 2}" y="{y + 105}" fill="{muted}" font-family="monospace" font-size="9">{swatch_label}</text>',
                f'<text x="{sx - 2}" y="{y + 120}" fill="{ink}" font-family="monospace" font-size="9">{color}</text>',
            ])
        parts.append('</g>')
    footer_y = height - 20
    parts.append(
        f'<text x="{MARGIN}" y="{footer_y}" fill="{muted}" font-family="Inter, Noto Sans, sans-serif" font-size="11">Pointer artwork: pinned Bibata Modern left_ptr · Colors: themes.json · Preview contact sheet, not a substitute for desktop testing</text>'
    )
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-svg", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--themes-json", type=Path, default=DEFAULT_THEMES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    themes = json.loads(args.themes_json.read_text(encoding="utf-8"))
    path_data = load_pointer_path(args.source_svg)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for mode, filename in (
        ("dark", "comparison-all-28.svg"),
        ("light", "comparison-all-28-light.svg"),
    ):
        output = args.output_dir / filename
        output.write_text(
            build_matrix_svg(themes, path_data, mode),
            encoding="utf-8",
            newline="\n",
        )
        print(f"Generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
