#!/usr/bin/env python3
"""Report critical cursor hotspots at fractional scaling scales (#38).

Reads scalable SVG metadata for a built theme and reports the hotspot
that Windows/Xcursor will use at 125%, 150%, and 200% of each frame's
nominal size, along with rounding drift from the ideal position.

Usage:
    python3 scripts/qa_hotspots.py --theme Peach --scalable-dir ~/.local/share/icons
    python3 scripts/qa_hotspots.py --theme Peach --scalable-dir out \
        --fail-over 1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CRITICAL_SHAPES = (
    "left_ptr",
    "xterm",
    "wait",
    "left_ptr_watch",
    "bottom_right_corner",
    "bottom_left_corner",
    "top_right_corner",
    "top_left_corner",
    "bd_double_arrow",
    "fd_double_arrow",
)
QA_SCALES = (1.25, 1.5, 2.0)
THEME_PREFIX = "Bibata-Material-"


def rounded_hotspot(value: int, nominal_size: int, target_size: int) -> int:
    return round(value * target_size / nominal_size)


def ideal_hotspot(value: int, nominal_size: int, target_size: int) -> float:
    return value * target_size / nominal_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", required=True, help="Theme key, e.g. Peach")
    parser.add_argument("--scalable-dir", type=Path, required=True,
                        help="Directory containing Bibata-Material-<Theme> scalable assets")
    parser.add_argument("--fail-over", type=float, default=None,
                        help="Exit 1 when drift exceeds this many device pixels")
    parser.add_argument("--shapes", default=",".join(CRITICAL_SHAPES),
                        help="Comma-separated scalable shape names to check")
    args = parser.parse_args()

    theme_dir = args.scalable_dir / f"{THEME_PREFIX}{args.theme}"
    if not theme_dir.is_dir():
        print(f"error: missing scalable theme directory: {theme_dir}", file=sys.stderr)
        return 1

    shapes = [name.strip() for name in args.shapes.split(",") if name.strip()]
    failures = 0
    reported = 0

    for shape in shapes:
        metadata_path = theme_dir / "cursors_scalable" / shape / "metadata.json"
        if not metadata_path.is_file():
            print(f"SKIP {shape}: no metadata at {metadata_path}")
            continue
        frames = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not frames:
            print(f"SKIP {shape}: empty metadata")
            continue

        frame = frames[0]
        nominal = frame["nominal_size"]
        hx, hy = frame["hotspot_x"], frame["hotspot_y"]
        print(f"{shape}: nominal {nominal}px, hotspot ({hx}, {hy})")

        for scale in QA_SCALES:
            target = round(nominal * scale)
            got_x = rounded_hotspot(hx, nominal, target)
            got_y = rounded_hotspot(hy, nominal, target)
            drift = max(
                abs(got_x - ideal_hotspot(hx, nominal, target)),
                abs(got_y - ideal_hotspot(hy, nominal, target)),
            )
            marker = ""
            if args.fail_over is not None and drift > args.fail_over:
                marker = " FAIL"
                failures += 1
            print(
                f"  {int(scale * 100)}% -> {target}px: "
                f"hotspot ({got_x}, {got_y}), drift {drift:.2f}px{marker}"
            )
        reported += 1

    if not reported:
        print("error: no critical shapes found to check", file=sys.stderr)
        return 1
    if failures:
        print(f"\n{failures} hotspot(s) exceeded the drift threshold.", file=sys.stderr)
        return 1
    print(f"\nChecked {reported} critical shape(s) at {', '.join(str(int(s * 100)) + '%' for s in QA_SCALES)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
