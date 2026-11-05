#!/usr/bin/env python3
"""Tests for the palette comparison matrix generator."""

import json
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from scripts.generate_palette_matrices import build_matrix_svg

ROOT = Path(__file__).resolve().parent.parent


class PaletteMatrixTests(unittest.TestCase):
    def setUp(self):
        self.themes = {}
        for index in range(28):
            name = f"Theme-{index}"
            self.themes[name] = {
                "label": name,
                "body": "#123456",
                "primary": "#abcdef",
                "watch": "#010203",
            }
        for index in range(28):
            name = f"Theme-{index}-Light"
            self.themes[name] = {
                "label": name,
                "body": "#eeeeee",
                "primary": "#234567",
                "watch": "#ffffff",
            }

    def test_generates_28_real_pointer_cards_per_mode(self):
        path = "M0 0L10 10Z"
        for mode in ("dark", "light"):
            with self.subTest(mode=mode):
                svg = build_matrix_svg(self.themes, path, mode)
                self.assertIn(f"Material Bibata · {mode.title()} palettes", svg)
                self.assertEqual(svg.count('data-theme="'), 28)
                self.assertIn('d="M0 0L10 10Z"', svg)

    def test_committed_comparison_sheets_match_current_palette_data(self):
        themes = json.loads((ROOT / "themes.json").read_text(encoding="utf-8"))
        for mode, filename in (
            ("dark", "comparison-all-28.svg"),
            ("light", "comparison-all-28-light.svg"),
        ):
            with self.subTest(mode=mode):
                path = ROOT / "docs" / filename
                content = path.read_text(encoding="utf-8")
                root = ET.fromstring(content)
                path_element = next(
                    node for node in root.iter()
                    if node.tag.rsplit("}", 1)[-1] == "path"
                )
                expected = build_matrix_svg(themes, path_element.get("d"), mode)
                self.assertEqual(content, expected)

    def test_rejects_invalid_mode_and_incomplete_palette_set(self):
        with self.assertRaises(ValueError):
            build_matrix_svg(self.themes, "M0 0L10 10Z", "system")
        with self.assertRaises(ValueError):
            build_matrix_svg({"Theme": self.themes["Theme-0"]}, "M0 0L10 10Z", "dark")


if __name__ == "__main__":
    unittest.main()
