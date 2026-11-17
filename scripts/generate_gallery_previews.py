#!/usr/bin/env python3
"""Generate gallery previews from the real compiled Xcursor files.

Reads the installed Xcursor themes and writes one image per cursor shape to
docs/previews/, containing the actual rendered artwork for the gallery. The
wait cursor is exported as an animated WebP (plus a static fallback for
reduced motion); other shapes are still PNGs. This keeps previews faithful to
the shipped cursors instead of using illustrative shapes drawn in the page.

Usage:
    python3 scripts/generate_gallery_previews.py
    python3 scripts/generate_gallery_previews.py --install-dir ~/.local/share/icons
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
THEMES_JSON = REPO_ROOT / "themes.json"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "previews"
SHAPES = ("left_ptr", "xterm", "bd_double_arrow")
WAIT_SHAPE = "wait"
WAIT_FRAME_STEP = 2
WAIT_QUALITY = 85
PREVIEW_BOX = 48
ARTWORK_BOX = 40

MAGIC = b"Xcur"
IMAGE_TYPE = 0xFFFD0002
FILE_HEADER = struct.Struct("<4sIII")
TOC_ENTRY = struct.Struct("<III")
CHUNK_HEADER = struct.Struct("<IIII")
IMAGE_HEADER = struct.Struct("<IIIII")


def read_xcursor_size(path: Path, size: int) -> Image.Image:
    """Return the first image of the requested size from an Xcursor file."""
    data = path.read_bytes()
    magic, header_size, _version, toc_count = FILE_HEADER.unpack_from(data)
    if magic != MAGIC:
        raise ValueError(f"{path}: invalid Xcursor magic")
    toc_end = header_size + toc_count * TOC_ENTRY.size
    if toc_end > len(data):
        raise ValueError(f"{path}: truncated table of contents")
    for index in range(toc_count):
        chunk_type, subtype, position = TOC_ENTRY.unpack_from(data, header_size + index * TOC_ENTRY.size)
        if chunk_type != IMAGE_TYPE or subtype != size:
            continue
        if position + CHUNK_HEADER.size + IMAGE_HEADER.size > len(data):
            raise ValueError(f"{path}: truncated image chunk")
        chunk_size, actual_type, actual_subtype, _version = CHUNK_HEADER.unpack_from(data, position)
        width, height, _xhot, _yhot, _delay = IMAGE_HEADER.unpack_from(data, position + CHUNK_HEADER.size)
        if actual_type != IMAGE_TYPE or actual_subtype != size:
            continue
        pixels_start = position + CHUNK_HEADER.size + IMAGE_HEADER.size
        pixels_end = pixels_start + width * height * 4
        if pixels_end > len(data) or chunk_size < CHUNK_HEADER.size + IMAGE_HEADER.size:
            raise ValueError(f"{path}: truncated pixel data")
        return Image.frombytes("RGBA", (width, height), data[pixels_start:pixels_end], "raw", "BGRA")
    raise ValueError(f"{path}: no image at size {size}")


def read_xcursor_frames(path: Path, size: int) -> tuple[list[Image.Image], int]:
    """Return every animation frame at the requested size and its delay."""
    data = path.read_bytes()
    magic, header_size, _version, toc_count = FILE_HEADER.unpack_from(data)
    if magic != MAGIC:
        raise ValueError(f"{path}: invalid Xcursor magic")
    frames: list[Image.Image] = []
    delay = 40
    for index in range(toc_count):
        chunk_type, subtype, position = TOC_ENTRY.unpack_from(data, header_size + index * TOC_ENTRY.size)
        if chunk_type != IMAGE_TYPE or subtype != size:
            continue
        _chunk_size, actual_type, actual_subtype, _version = CHUNK_HEADER.unpack_from(data, position)
        width, height, _xhot, _yhot, frame_delay = IMAGE_HEADER.unpack_from(data, position + CHUNK_HEADER.size)
        if actual_type != IMAGE_TYPE or actual_subtype != size:
            continue
        delay = frame_delay
        pixels_start = position + CHUNK_HEADER.size + IMAGE_HEADER.size
        frames.append(
            Image.frombytes("RGBA", (width, height), data[pixels_start:pixels_start + width * height * 4], "raw", "BGRA")
        )
    if not frames:
        raise ValueError(f"{path}: no animation frames at size {size}")
    return frames, delay


def normalize(frames: list[Image.Image]) -> list[Image.Image]:
    """Crop transparent padding and scale artwork into a uniform box.

    Shapes have very different alpha bounds (e.g. a slim I-beam vs a full
    circular spinner). Cropping to the shared bounds and scaling to a fixed
    footprint makes all four previews look equally sized and evenly spaced.
    """
    bbox = None
    for frame in frames:
        current = frame.getchannel("A").getbbox()
        if current is None:
            continue
        bbox = current if bbox is None else (
            min(bbox[0], current[0]), min(bbox[1], current[1]),
            max(bbox[2], current[2]), max(bbox[3], current[3]),
        )
    if bbox is None:
        return frames
    result = []
    for frame in frames:
        cropped = frame.crop(bbox)
        cropped.thumbnail((ARTWORK_BOX, ARTWORK_BOX), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (PREVIEW_BOX, PREVIEW_BOX), (0, 0, 0, 0))
        canvas.alpha_composite(
            cropped,
            ((PREVIEW_BOX - cropped.width) // 2, (PREVIEW_BOX - cropped.height) // 2),
        )
        result.append(canvas)
    return result


def generate(
    themes_json: Path,
    install_dir: Path,
    output_dir: Path,
    size: int,
) -> list[str]:
    themes = json.loads(themes_json.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for theme in themes:
        for shape in SHAPES:
            cursor = install_dir / f"Bibata-Material-{theme}" / "cursors" / shape
            if not cursor.is_file():
                raise ValueError(f"missing cursor for {theme}/{shape}: {cursor}")
            target = output_dir / f"{theme}-{shape}.png"
            normalize([read_xcursor_size(cursor, size)])[0].save(target)
            written.append(target.name)

        wait_path = install_dir / f"Bibata-Material-{theme}" / "cursors" / WAIT_SHAPE
        if not wait_path.is_file():
            raise ValueError(f"missing cursor for {theme}/{WAIT_SHAPE}: {wait_path}")
        frames, delay = read_xcursor_frames(wait_path, size)
        frames = normalize(frames[::WAIT_FRAME_STEP])
        animated = output_dir / f"{theme}-wait.webp"
        frames[0].save(
            animated, "WEBP", save_all=True, append_images=frames[1:],
            duration=delay * WAIT_FRAME_STEP, loop=0, quality=WAIT_QUALITY, method=6,
        )
        written.append(animated.name)
        # Static first frame for visitors who prefer reduced motion.
        still = output_dir / f"{theme}-wait.png"
        frames[0].save(still)
        written.append(still.name)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--themes-json", type=Path, default=THEMES_JSON)
    parser.add_argument(
        "--install-dir", type=Path,
        default=Path(os.environ.get("BIBATA_MATERIAL_INSTALL_DIR", str(Path.home() / ".local" / "share" / "icons"))),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--size", type=int, default=48, help="Xcursor image size to extract (default: 48)")
    args = parser.parse_args()
    if args.size <= 0:
        parser.error("--size must be positive")
    try:
        written = generate(args.themes_json, args.install_dir.resolve(), args.output_dir, args.size)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {len(written)} real-cursor preview assets to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
