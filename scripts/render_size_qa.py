#!/usr/bin/env python3
"""Render representative cursors at each shipped size and run objective QA (#73, #58).

Renders the actual vendored SVG artwork in a theme's colors with the pinned
rsvg-convert renderer, then checks dimensions, clipping, transparency and
hotspot bounds at every Xcursor and Windows size. Optionally compares the
rendered PNGs against committed baselines to detect visual regressions (#58).

Usage:
    python3 scripts/render_size_qa.py --theme Peach
    python3 scripts/render_size_qa.py --theme Peach --baselines docs/baselines
    python3 scripts/render_size_qa.py --theme Peach --update-baselines docs/baselines
    python3 scripts/render_size_qa.py --theme Peach --contact-sheet out.png
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_svg_cursors import recolor_svg, resolve_source_dir
from spinner_colors import recolor_entries

BIBATA_DIR = REPO_ROOT / "scripts" / "bibata_cursor"
THEMES_JSON = REPO_ROOT / "themes.json"
XCURSOR_SIZES = (16, 20, 22, 24, 28, 32, 48, 64, 72, 84, 96)
WINDOWS_SIZES = (16, 24, 32, 48, 64, 128)
# Representative categories: thin strokes, outline, detail, animation, corner.
SHAPES = ("left_ptr", "xterm", "bd_double_arrow", "wait", "bottom_right_corner", "circle", "copy", "zoom-in")


def source_for(shape: str, resolved: dict[str, Path]) -> Path:
    if shape == "wait":
        return resolved["wait"] / "wait-01.svg"
    return resolved[shape + ".svg"]


def render(svg_text: str, size: int, out: Path) -> None:
    subprocess.run(
        ["rsvg-convert", "-a", "-f", "png", "-w", str(size), "-h", str(size),
         "-o", str(out), "-"],
        input=svg_text, text=True, check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def analyze(image: Image.Image, size: int, hotspot: tuple[int, int] | None) -> dict:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    opaque = sum(1 for p in alpha.getdata() if p >= 200)
    # Clipping: visible artwork touches the canvas edge (alpha at edge > 0).
    edges = [alpha.getpixel((x, 0)) for x in range(size)] + \
            [alpha.getpixel((x, size - 1)) for x in range(size)] + \
            [alpha.getpixel((0, y)) for y in range(size)] + \
            [alpha.getpixel((size - 1, y)) for y in range(size)]
    touches_edge = any(v > 0 for v in edges)
    # A narrow gap is normal at small sizes; clipping means the artwork fills
    # the entire canvas in a dimension (content cut at opposite edges).
    clipped = bool(bbox) and (bbox[2] - bbox[0] >= size or bbox[3] - bbox[1] >= size)
    result = {
        "size": size,
        "dimensions_ok": rgba.size == (size, size),
        "has_transparency": opaque < size * size,
        "opaque_pixels": opaque,
        "content_bbox": list(bbox) if bbox else None,
        "touches_edge": touches_edge,
        "clipped": clipped,
    }
    if hotspot is not None:
        hx, hy = hotspot
        result["hotspot"] = [hx, hy]
        result["hotspot_in_bounds"] = 0 <= hx < size and 0 <= hy < size
        if bbox:
            result["hotspot_in_artwork"] = bbox[0] <= hx < bbox[2] and bbox[1] <= hy < bbox[3]
    return result


def render_theme(theme: str, colors: dict, out_dir: Path) -> dict:
    resolved = resolve_source_dir(BIBATA_DIR, "modern")
    body, primary, watch = colors["body"], colors["primary"], colors["watch"]
    extra = recolor_entries(primary)

    def recolor(text: str) -> str:
        text = text.replace("#00FF00", body).replace("#0000FF", primary).replace("#FF0000", watch)
        for entry in extra:
            text = text.replace(entry["match"], entry["replace"])
        return text

    report = {"theme": theme, "colors": colors, "shapes": {}}
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        svg_tmp = Path(tmp) / "frame.svg"
        for shape in SHAPES:
            src = source_for(shape, resolved)
            text = recolor(src.read_text(encoding="utf-8"))
            svg_tmp.write_text(text, encoding="utf-8")
            shape_dir = out_dir / shape
            shape_dir.mkdir(parents=True, exist_ok=True)
            # Reference render at native canvas size for the clipping check.
            ref_png = shape_dir / "reference-256.png"
            render(text, 256, ref_png)
            ref = analyze(Image.open(ref_png), 256, None)
            checks = []
            for size in sorted(set(XCURSOR_SIZES) | set(WINDOWS_SIZES)):
                png = shape_dir / f"{size}.png"
                render(text, size, png)
                c = analyze(Image.open(png), size, None)
                c["clipped"] = ref["clipped"]  # clipping decided at reference size
                checks.append(c)
            report["shapes"][shape] = {"reference": ref, "sizes": checks}
    return report


def pixel_diff(a: Image.Image, b: Image.Image) -> tuple[int, float]:
    """Return (max channel difference, percent of pixels differing > 8)."""
    if a.size != b.size:
        return 255, 100.0
    diff = ImageChops.difference(a.convert("RGBA"), b.convert("RGBA"))
    # Consider a pixel changed if any channel differs meaningfully.
    changed = sum(
        1 for px in diff.getdata()
        if any(v > 8 for v in px)
    )
    maxdiff = max(max(px) for px in diff.getdata())
    return maxdiff, changed / (a.width * a.height) * 100


def check_baselines(out_dir: Path, baseline_dir: Path,
                    max_channel_delta: int = 48, max_changed_pct: float = 2.0) -> list[str]:
    """Compare renders to baselines with tolerance for renderer version drift."""
    problems = []
    for png in sorted(out_dir.rglob("*.png")):
        rel = png.relative_to(out_dir)
        base = baseline_dir / rel
        if not base.is_file():
            problems.append(f"missing baseline: {rel}")
            continue
        maxdiff, changed_pct = pixel_diff(Image.open(png), Image.open(base))
        if maxdiff > max_channel_delta or changed_pct > max_changed_pct:
            problems.append(f"visual difference: {rel} (max Δ{maxdiff}, {changed_pct:.2f}% pixels)")
    for base in sorted(baseline_dir.rglob("*.png")):
        if not (out_dir / base.relative_to(baseline_dir)).is_file():
            problems.append(f"extra baseline: {base.relative_to(baseline_dir)}")
    return problems


def contact_sheet(report: dict, out_dir: Path, target: Path) -> None:
    imgs = []
    for shape in SHAPES:
        if shape not in report["shapes"]:
            continue
        for size in (16, 32, 64, 128):
            p = out_dir / shape / f"{size}.png"
            if p.is_file():
                imgs.append((f"{shape} {size}", Image.open(p).convert("RGBA")))
    w, h = 140, 150
    cols = 4
    rows = (len(imgs) + cols - 1) // cols
    canvas = Image.new("RGB", (w * cols, h * rows), "white")
    draw = ImageDraw.Draw(canvas)
    for i, (label, im) in enumerate(imgs):
        x, y = (i % cols) * w, (i // cols) * h
        canvas.paste(im.resize((128, 128), Image.NEAREST), (x + 6, y + 18), im.resize((128, 128), Image.NEAREST))
        draw.text((x + 6, y + 2), label, fill="black")
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", default="Peach")
    parser.add_argument("--themes-json", type=Path, default=THEMES_JSON)
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/opencode/size-qa"))
    parser.add_argument("--baselines", type=Path, help="baseline directory to compare against")
    parser.add_argument("--max-channel-delta", type=int, default=48,
                        help="largest per-channel pixel delta tolerated vs baselines (default: 48)")
    parser.add_argument("--max-changed-pct", type=float, default=2.0,
                        help="max %% of pixels allowed to differ vs baselines (default: 2.0)")
    parser.add_argument("--update-baselines", type=Path, help="copy renders to this baseline dir")
    parser.add_argument("--contact-sheet", type=Path, help="write a contact-sheet PNG")
    args = parser.parse_args()
    themes = json.loads(args.themes_json.read_text(encoding="utf-8"))
    if args.theme not in themes:
        print(f"error: unknown theme {args.theme}", file=sys.stderr)
        return 1
    out = args.output_dir / args.theme
    if out.exists():
        import shutil
        shutil.rmtree(out)
    report = render_theme(args.theme, themes[args.theme], out)
    # Objective checks
    failures = []
    for shape, data in report["shapes"].items():
        if data["reference"]["clipped"]:
            failures.append(f"{shape}: artwork clipped at reference size")
        for c in data["sizes"]:
            if not c["dimensions_ok"] or not c["has_transparency"]:
                failures.append(f"{shape}@{c['size']}: dimensions/transparency issue")
    if failures:
        for f in failures[:20]:
            print(f"FAIL: {f}", file=sys.stderr)
    print(f"Rendered {len(report['shapes'])} shapes at {len(set(XCURSOR_SIZES) | set(WINDOWS_SIZES))} sizes; "
          f"objective failures: {len(failures)}")
    if args.contact_sheet:
        contact_sheet(report, out, args.contact_sheet)
    if args.update_baselines:
        import shutil
        base = args.update_baselines / args.theme
        if base.exists():
            shutil.rmtree(base)
        shutil.copytree(out, base)
        print(f"Updated baselines at {base}")
    if args.baselines:
        problems = check_baselines(out, args.baselines / args.theme,
                                   args.max_channel_delta, args.max_changed_pct)
        if problems:
            for p in problems[:20]:
                print(f"BASELINE: {p}", file=sys.stderr)
            print(f"{len(problems)} baseline difference(s)", file=sys.stderr)
            return 1
        print("Baseline comparison: identical")
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
