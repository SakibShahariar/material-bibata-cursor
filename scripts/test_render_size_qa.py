#!/usr/bin/env python3
"""Tests for the size/rendering QA and visual regression helper."""
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_size_qa import SHAPES, THEMES_JSON, check_baselines, main, pixel_diff
from PIL import Image, ImageDraw


class RenderSizeQATests(unittest.TestCase):
    def test_baselines_exist_for_built_representative_themes(self):
        base = REPO_ROOT / "docs" / "baselines"
        for theme in ("Peach", "Peach-Light"):
            for shape in SHAPES:
                self.assertTrue((base / theme / shape / "24.png").is_file(),
                                f"missing baseline {theme}/{shape}/24.png")

    def test_baseline_comparison_identical(self):
        base = REPO_ROOT / "docs" / "baselines" / "Peach"
        if not base.is_dir():
            self.skipTest("baselines not generated")
        self.assertEqual(check_baselines(base, base), [])

    def test_pixel_diff_detects_change_and_tolerates_none(self):
        a = Image.new("RGBA", (16, 16), (255, 0, 0, 255))
        self.assertEqual(pixel_diff(a, a.copy()), (0, 0.0))
        b = a.copy(); ImageDraw.Draw(b).rectangle((0, 0, 4, 4), fill=(0, 255, 0, 255))
        maxdiff, pct = pixel_diff(a, b)
        self.assertGreater(maxdiff, 48)
        self.assertGreater(pct, 2.0)


if __name__ == "__main__":
    unittest.main()
