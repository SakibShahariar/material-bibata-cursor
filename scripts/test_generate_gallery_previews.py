#!/usr/bin/env python3
"""Tests for real-cursor gallery preview extraction."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_gallery_previews import REPO_ROOT, SHAPES, THEMES_JSON, generate, read_xcursor_size
from test_validate_theme_assets import make_xcursor


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
        missing = [name for name in themes if not (previews / f"{name}.png").is_file()]
        self.assertEqual(missing, [], f"missing real-cursor previews: {missing}")

    def test_gallery_uses_real_previews_not_illustrations(self):
        html = (REPO_ROOT / "docs" / "gallery.html").read_text(encoding="utf-8")
        self.assertIn("previews/'", html)
        self.assertNotIn("svgShape", html)
        self.assertNotIn("illustrative", html.lower())

    def test_generates_one_strip_per_theme_from_installed_cursors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install = root / "icons"
            for theme in ("Apricot", "Peach"):
                cursors = install / f"Bibata-Material-{theme}" / "cursors"
                cursors.mkdir(parents=True)
                for shape in SHAPES:
                    (cursors / shape).write_bytes(make_xcursor([48]))
            themes_json = root / "themes.json"
            themes_json.write_text(json.dumps({"Apricot": {}, "Peach": {}}))
            output = root / "previews"

            written = generate(themes_json, install, output, 48)

            self.assertEqual(sorted(written), ["Apricot.png", "Peach.png"])
            for theme in ("Apricot", "Peach"):
                image = Image.open(output / f"{theme}.png")
                self.assertEqual(image.size, (48 * len(SHAPES), 48))


if __name__ == "__main__":
    unittest.main()
