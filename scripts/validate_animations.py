#!/usr/bin/env python3
"""Validate animated cursors against the pinned upstream contract (#39).

Checks two things the general asset validator does not:

1. Frame sequence: each built animated theme must have exactly the same
   frame count, filenames, order, and per-frame delays as the pinned upstream
   source (wait and left_ptr_watch are 54 frames at 40ms in the pinned tree).
2. Transparency: recoloring must not turn upstream transparent regions opaque.
   The SVG root stays `fill="none"`, and any transparent/filter elements keep
   their original opacity attributes after recoloring.

Usage:
    python3 scripts/validate_animations.py
    python3 scripts/validate_animations.py --themes Peach,Charcoal
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BIBATA_DIR = REPO_ROOT / "scripts" / "bibata_cursor"
DEFAULT_SCALABLE = Path.home() / ".local" / "share" / "icons"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_svg_cursors import resolve_source_dir

ANIMATED = ("wait", "left_ptr_watch")
THEME_PREFIX = "Bibata-Material-"


def upstream_contract(bibata_dir: Path) -> dict[str, dict]:
    """Return expected {shape: {frames: [...], delay: ms}} from pinned sources."""
    cfg = tomllib.loads((bibata_dir / "config" / "build.toml").read_text(encoding="utf-8"))
    defaults = cfg["cursor_defaults"]
    resolved = resolve_source_dir(bibata_dir, "modern")
    contract = {}
    for shape in ANIMATED:
        params = cfg["cursors"][shape]
        png_ref = params["png"]
        dirname = png_ref.split("*")[0].rstrip("-")
        src_dir = resolved.get(dirname)
        if src_dir is None or not src_dir.is_dir():
            raise RuntimeError(f"upstream animation source missing for {shape}: {dirname}")
        frames = sorted(p.name for p in src_dir.glob("*.svg"))
        delays = params.get("x11_delay", defaults.get("x11_delay", 40))
        delay_list = delays if isinstance(delays, list) else [delays]
        contract[shape] = {
            "frames": frames,
            "delays": [delay_list[i % len(delay_list)] for i in range(len(frames))],
        }
    return contract


def check_transparency(svg_path: Path, upstream_path: Path) -> list[str]:
    """Return a list of transparency problems introduced by recoloring."""
    problems = []
    built = ET.parse(svg_path).getroot()
    upstream = ET.parse(upstream_path).getroot()
    # The source canvas must remain transparent (no fill on root).
    if built.attrib.get("fill") not in (None, "none"):
        problems.append(f"{svg_path.name}: root fill changed to {built.attrib['fill']!r}")
    # Opacity attributes on any element must match upstream exactly.
    def opacities(root):
        out = []
        for el in root.iter():
            for key in ("fill-opacity", "stroke-opacity", "opacity", "flood-opacity"):
                if key in el.attrib:
                    out.append((el.tag.split("}")[-1], key, el.attrib[key]))
        return out
    built_o, upstream_o = opacities(built), opacities(upstream)
    if built_o != upstream_o:
        problems.append(f"{svg_path.name}: opacity attributes changed: {built_o} vs upstream {upstream_o}")
    return problems


def validate_theme(theme: str, scalable_root: Path, contract: dict) -> list[str]:
    problems = []
    theme_dir = scalable_root / f"{THEME_PREFIX}{theme}" / "cursors_scalable"
    if not theme_dir.is_dir():
        return [f"{theme}: missing scalable theme dir {theme_dir}"]
    for shape, expected in contract.items():
        meta_path = theme_dir / shape / "metadata.json"
        if not meta_path.is_file():
            problems.append(f"{theme}/{shape}: missing metadata.json")
            continue
        frames = json.loads(meta_path.read_text(encoding="utf-8"))
        filenames = [f["filename"] for f in frames]
        delays = [f.get("delay") for f in frames]
        if filenames != expected["frames"]:
            problems.append(f"{theme}/{shape}: frame sequence differs from upstream")
        if delays != expected["delays"]:
            problems.append(f"{theme}/{shape}: delays differ from upstream: {delays} vs {expected['delays']}")
        # Transparency on the first frame (all frames come from the same template).
        upstream_frame = BIBATA_DIR / "svg" / "groups"
        # Locate the exact upstream frame via the resolver to avoid guessing the group.
        cfg = tomllib.loads((BIBATA_DIR / "config" / "build.toml").read_text(encoding="utf-8"))
        dirname = cfg["cursors"][shape]["png"].split("*")[0].rstrip("-")
        src_dir = resolve_source_dir(BIBATA_DIR, "modern")[dirname]
        for frame in frames:
            built_svg = theme_dir / shape / frame["filename"]
            upstream_svg = src_dir / frame["filename"]
            if built_svg.is_file() and upstream_svg.is_file():
                problems.extend(check_transparency(built_svg, upstream_svg))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bibata-dir", type=Path, default=BIBATA_DIR)
    parser.add_argument("--scalable-dir", type=Path, default=DEFAULT_SCALABLE)
    parser.add_argument("--themes-json", type=Path, default=REPO_ROOT / "themes.json")
    parser.add_argument("--themes", help="Comma-separated theme names (default: all)")
    args = parser.parse_args()
    try:
        contract = upstream_contract(args.bibata_dir)
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print("Upstream animation contract:")
    for shape, info in contract.items():
        print(f"  {shape}: {len(info['frames'])} frames, delays={sorted(set(info['delays']))}")

    themes = json.loads(args.themes_json.read_text(encoding="utf-8"))
    names = [n.strip() for n in args.themes.split(",")] if args.themes else list(themes)
    all_problems = []
    for name in names:
        all_problems.extend(validate_theme(name, args.scalable_dir, contract))
    if all_problems:
        for problem in all_problems[:40]:
            print(f"FAIL: {problem}", file=sys.stderr)
        print(f"\n{len(all_problems)} animation problem(s) found.", file=sys.stderr)
        return 1
    print(f"\nOK: {len(names)} theme(s) match the upstream animation contract; transparency preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
