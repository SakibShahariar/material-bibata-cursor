#!/usr/bin/env python3
"""Tests for real-cursor gallery preview extraction."""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_gallery_previews import (
    REPO_ROOT, SHAPES, THEMES_JSON, WAIT_SHAPE,
    generate, read_xcursor_frames, read_xcursor_size,
)
from test_validate_theme_assets import IMAGE_TYPE, make_xcursor


def make_animated_xcursor(size: int, count: int) -> bytes:
    """Build an Xcursor with distinct frames so WebP does not deduplicate them."""
    position = 16 + count * 12
    toc, chunks = [], []
    for index in range(count):
        toc.append(struct.pack("<III", IMAGE_TYPE, size, position))
        pixel = struct.pack("<4B", 0, 0, 0, 255 - index) * (size * size)
        chunk = (
            struct.pack("<IIII", 36, IMAGE_TYPE, size, 1)
            + struct.pack("<IIIII", size, size, size // 2, size // 2, 40)
            + pixel
        )
        chunks.append(chunk)
        position += len(chunk)
    return struct.pack("<4sIII", b"Xcur", 16, 1, count) + b"".join(toc + chunks)


class GalleryPreviewTests(unittest.TestCase):
    def test_reads_real_xcursor_pixels_and_reports_missing_sizes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "left_ptr"
            path.write_bytes(make_xcursor([16, 48]))
            image = read_xcursor_size(path, 48)
            self.assertEqual(image.size, (48, 48))
            self.assertEqual(image.getpixel((0, 0)), (0, 0, 0, 0))
            with self.assertRaises(ValueError):
                read_xcursor_size(path, 32)

    def test_committed_previews_exist_for_every_theme(self):
        themes = json.loads(THEMES_JSON.read_text(encoding="utf-8"))
        previews = REPO_ROOT / "docs" / "previews"
        missing = [
            name for name in themes
            if not (previews / f"{name}.png").is_file()
            or not (previews / f"{name}-wait.webp").is_file()
            or not (previews / f"{name}-wait.png").is_file()
        ]
        self.assertEqual(missing, [], f"missing real-cursor previews: {missing}")

    def test_gallery_uses_real_previews_not_illustrations(self):
        html = (REPO_ROOT / "docs" / "gallery.html").read_text(encoding="utf-8")
        self.assertIn("previews/'", html)
        self.assertIn("-wait.webp", html)
        self.assertNotIn("svgShape", html)
        self.assertNotIn("illustrative", html.lower())

    def test_reads_all_real_animation_frames(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "wait"
            path.write_bytes(make_animated_xcursor(48, 6))
            frames, delay = read_xcursor_frames(path, 48)
            self.assertEqual(len(frames), 6)
            self.assertEqual(delay, 40)

    def test_generates_strip_and_animated_wait_per_theme(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install = root / "icons"
            for theme in ("Apricot", "Peach"):
                cursors = install / f"Bibata-Material-{theme}" / "cursors"
                cursors.mkdir(parents=True)
                for shape in SHAPES:
                    (cursors / shape).write_bytes(make_xcursor([48]))
                (cursors / WAIT_SHAPE).write_bytes(make_animated_xcursor(48, 6))
            themes_json = root / "themes.json"
            themes_json.write_text(json.dumps({"Apricot": {}, "Peach": {}}))
            output = root / "previews"

            written = generate(themes_json, install, output, 48)

            self.assertEqual(sorted(written), [
                "Apricot-wait.png", "Apricot-wait.webp", "Apricot.png",
                "Peach-wait.png", "Peach-wait.webp", "Peach.png",
            ])
            for theme in ("Apricot", "Peach"):
                image = Image.open(output / f"{theme}.png")
                self.assertEqual(image.size, (48 * len(SHAPES), 48))
                animated = Image.open(output / f"{theme}-wait.webp")
                self.assertGreater(animated.n_frames, 1)


if __name__ == "__main__":
    unittest.main()
