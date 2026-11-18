#!/usr/bin/env python3
"""Generate a local hotspot QA page for a built theme (#38).

The page shows each critical cursor shape enlarged, with the true hotspot
marked, so a tester can compare where a real click lands at 125/150/200%
desktop scaling. It is a development aid only - not shipped in releases.

Usage:
    python3 scripts/generate_hotspot_qa_page.py --theme Peach
    # open docs/hotspot-qa.html in a browser next to a window to test against
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_hotspots import CRITICAL_SHAPES, QA_SCALES

DEFAULT_OUTPUT = REPO_ROOT / "docs" / "hotspot-qa.html"


def svg_data_uri(path: Path) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", default="Peach")
    parser.add_argument(
        "--scalable-dir", type=Path,
        default=Path.home() / ".local" / "share" / "icons",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    theme_dir = args.scalable_dir / f"Bibata-Material-{args.theme}" / "cursors_scalable"
    if not theme_dir.is_dir():
        print(f"error: missing {theme_dir}", file=sys.stderr)
        return 1

    cards = []
    for shape in CRITICAL_SHAPES:
        meta_path = theme_dir / shape / "metadata.json"
        if not meta_path.is_file():
            continue
        frames = json.loads(meta_path.read_text(encoding="utf-8"))
        if not frames:
            continue
        frame = frames[0]
        svg = theme_dir / shape / frame["filename"]
        if not svg.is_file():
            continue
        hx, hy, nominal = frame["hotspot_x"], frame["hotspot_y"], frame["nominal_size"]
        # Mark the hotspot as a percentage of the 256-unit source canvas.
        x_pct = hx / nominal * 100
        y_pct = hy / nominal * 100
        scales = " · ".join(
            f"{int(s * 100)}%: ({round(hx * s)}, {round(hy * s)})" for s in QA_SCALES
        )
        cards.append(
            '<article class="card"><h2>{shape}</h2>'
            '<div class="canvas"><img src="{uri}" alt="{shape}">'
            '<div class="hotspot" style="left:{x:.4f}%;top:{y:.4f}%"></div></div>'
            '<p class="scales">{scales}</p>'
            '<p class="hint">Click near the crosshair: it marks ({hx}, {hy}) in a '
            '{nominal}px canvas. At 100% on screen it is {screen:.0f}px from the top-left.</p>'
            '</article>'.format(
                shape=shape, uri=svg_data_uri(svg), x=x_pct, y=y_pct,
                scales=scales, hx=hx, hy=hy, nominal=nominal,
                screen=hx / nominal * 256,
            )
        )

    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hotspot QA - {theme}</title>
<style>
 body{{font:15px/1.5 system-ui,sans-serif;margin:0;padding:2rem;background:#f4f6f8;color:#17212b}}
 h1{{margin-top:0}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1rem}}
 .card{{background:#fff;border:1px solid #d9e0e6;border-radius:.8rem;padding:1rem}}
 .card h2{{margin:.2rem 0 .6rem;font-size:1.1rem}}
 .canvas{{position:relative;width:256px;height:256px;border:1px solid #ccc;background:
   repeating-conic-gradient(#eee 0% 25%, #fff 0% 50%) 50%/16px 16px}}
 .canvas img{{width:256px;height:256px;display:block}}
 .hotspot{{position:absolute;width:1px;height:1px;background:transparent}}
 .hotspot::before,.hotspot::after{{content:"";position:absolute;background:#e00}}
 .hotspot::before{{left:-12px;top:0;width:25px;height:2px}}
 .hotspot::after{{left:0;top:-12px;width:2px;height:25px}}
 .scales{{font-size:.8rem;color:#5c6873;overflow-wrap:anywhere}}
 .hint{{font-size:.8rem;color:#5c6873}}
</style></head><body>
<h1>Hotspot QA - {theme}</h1>
<p>Set desktop scaling to 125% / 150% / 200%, then hover a window edge/corner and text to
compare the real pointer with the crosshairs below. The crosshair marks the hotspot in the
source artwork; the red lines show where a click should land.</p>
<section class="grid">{cards}</section>
</body></html>""".format(theme=args.theme, cards="".join(cards))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"Wrote {args.output} ({len(cards)} shapes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
