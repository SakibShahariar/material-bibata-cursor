#!/usr/bin/env python3
"""Cross-check cursor-metadata.json against built assets and current sources (#70).

Validates that the descriptive metadata matches:
- the pinned build.toml aliases/hotspots/animation globs,
- the built scalable theme's shape directories, metadata hotspots and sizes,
- the size ladders used by the validators.

Usage:
    python3 scripts/validate_cursor_metadata.py --scalable-dir ~/.local/share/icons --themes Peach
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BIBATA_DIR = REPO_ROOT / "scripts" / "bibata_cursor"
METADATA = REPO_ROOT / "scripts" / "cursor-metadata.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_theme_assets import EXPECTED_XCURSOR_SIZES


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, default=METADATA)
    parser.add_argument("--scalable-dir", type=Path, default=Path.home() / ".local" / "share" / "icons")
    parser.add_argument("--themes", default="Peach")
    args = parser.parse_args()
    if not args.metadata.is_file():
        print(f"error: missing {args.metadata}; run 'just cursor-metadata'", file=sys.stderr)
        return 1
    meta = json.loads(args.metadata.read_text(encoding="utf-8"))
    problems = []

    if meta.get("schema_version") != 1:
        problems.append("unsupported schema_version")
    # Source pin matches the provenance module.
    from source_provenance import UPSTREAM_COMMIT, UPSTREAM_REPOSITORY
    if meta["source"]["commit"] != UPSTREAM_COMMIT or meta["source"]["upstream"] != UPSTREAM_REPOSITORY:
        problems.append("source pin does not match source_provenance.py")
    # Size ladder matches validator.
    if set(meta["cursors"]["left_ptr"]["sizes"]["xcursor"]) != EXPECTED_XCURSOR_SIZES:
        problems.append("xcursor size ladder does not match validator")

    # Hotspots/animation in metadata match build.toml.
    cfg = tomllib.loads((BIBATA_DIR / "config" / "build.toml").read_text(encoding="utf-8"))
    defaults = cfg["cursor_defaults"]
    for shape_key, params in cfg["cursors"].items():
        x11 = params.get("x11_name", "")
        if not x11 or x11 not in meta["cursors"]:
            continue
        entry = meta["cursors"][x11]
        expected_hot = [params.get("x_hotspot", defaults["x_hotspot"]),
                        params.get("y_hotspot", defaults["y_hotspot"])]
        if entry["hotspot"] != expected_hot:
            problems.append(f"{x11}: hotspot mismatch metadata vs build.toml")
        expected_glob = params.get("png", "")
        if (entry["animation"] or {}).get("frame_glob") != (expected_glob if "*" in expected_glob else None):
            problems.append(f"{x11}: animation frame_glob mismatch")

    # Built scalable assets match metadata (shape dirs, hotspots, frame counts).
    for theme in [t.strip() for t in args.themes.split(",") if t.strip()]:
        root = args.scalable_dir / f"Bibata-Material-{theme}" / "cursors_scalable"
        if not root.is_dir():
            problems.append(f"{theme}: missing scalable theme dir")
            continue
        for name, entry in meta["cursors"].items():
            if name in ("person", "pin"):
                continue  # Windows-only shapes have no x11_name/scalable output
            shape_dir = root / name
            if not shape_dir.is_dir():
                problems.append(f"{theme}/{name}: missing scalable shape dir")
                continue
            frames = json.loads((shape_dir / "metadata.json").read_text(encoding="utf-8"))
            for frame in frames:
                if [frame["hotspot_x"], frame["hotspot_y"]] != entry["hotspot"]:
                    problems.append(f"{theme}/{name}: built hotspot differs from metadata")
            if entry["animation"]:
                # Animated frames live in one group dir (e.g. shared/wait or
                # modern/left_ptr_watch). Use the max across groups, not the
                # sum of duplicate modern/original/right variants.
                candidates = [len(list(p.glob("*.svg")))
                              for p in BIBATA_DIR.glob(f"svg/groups/*/{entry['animation']['frame_dir']}")
                              if p.is_dir()]
                expected = max(candidates) if candidates else 0
                if len(frames) != expected:
                    problems.append(f"{theme}/{name}: frame count {len(frames)} != upstream {expected}")

    if problems:
        for p in problems[:30]:
            print(f"FAIL: {p}", file=sys.stderr)
        print(f"\n{len(problems)} metadata problem(s)", file=sys.stderr)
        return 1
    print(f"OK: metadata matches sources and {len(args.themes.split(','))} built theme(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
