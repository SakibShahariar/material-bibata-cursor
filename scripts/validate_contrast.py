#!/usr/bin/env python3
"""validate_contrast.py — WCAG contrast checks for themes.json (#26).

Fails when any theme's body/primary contrast drops below the documented
4.5:1 bar. Watch/primary contrast below the same bar produces a warning
(the watch color sits behind the busy spinner, so it is less critical).

Classic is exempt: it intentionally preserves the original upstream
Bibata-Modern-Classic palette rather than an M3-tuned one.

Usage:
    python3 scripts/validate_contrast.py [--themes-json themes.json]
"""

import argparse
import json
import sys
from pathlib import Path

MIN_RATIO = 4.5
EXEMPT_THEMES = {"Classic"}


def _channel(value):
    value /= 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"invalid hex color: {hex_color!r}")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (
        0.2126 * _channel(r)
        + 0.7152 * _channel(g)
        + 0.0722 * _channel(b)
    )


def contrast_ratio(hex1, hex2):
    l1 = relative_luminance(hex1)
    l2 = relative_luminance(hex2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def validate(themes, min_ratio=MIN_RATIO):
    errors = []
    warnings = []
    for name, colors in themes.items():
        if name in EXEMPT_THEMES:
            continue
        try:
            body = colors["body"]
            primary = colors["primary"]
            watch = colors["watch"]
        except KeyError as exc:
            errors.append(f"{name}: missing required color {exc}")
            continue
        try:
            body_ratio = contrast_ratio(body, primary)
            watch_ratio = contrast_ratio(watch, primary)
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue
        if body_ratio < min_ratio:
            errors.append(
                f"{name}: body/primary contrast {body_ratio:.2f}:1 "
                f"is below the {min_ratio}:1 bar"
            )
        if watch_ratio < min_ratio:
            warnings.append(
                f"{name}: watch/primary contrast {watch_ratio:.2f}:1 "
                f"is below the {min_ratio}:1 bar"
            )
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--themes-json",
        default=str(Path(__file__).resolve().parent.parent / "themes.json"),
    )
    args = parser.parse_args()

    themes = json.loads(Path(args.themes_json).read_text(encoding="utf-8"))
    errors, warnings = validate(themes)

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    checked = len(themes) - len(EXEMPT_THEMES & set(themes))
    print(f"OK: {checked} theme(s) meet the {MIN_RATIO}:1 body/primary contrast bar.")


if __name__ == "__main__":
    main()
