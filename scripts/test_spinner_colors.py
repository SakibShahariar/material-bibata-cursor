#!/usr/bin/env python3
"""Tests for theme-derived spinner shades."""
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spinner_colors import CORNER_MATCHES, RAINBOW_MATCHES, recolor_entries, spinner_shades


class SpinnerColorTests(unittest.TestCase):
    def test_all_themes_get_four_distinct_valid_shades(self):
        themes = json.loads((Path(__file__).resolve().parent.parent / "themes.json").read_text())
        for name, colors in themes.items():
            shades = spinner_shades(colors["primary"])
            self.assertEqual(len(shades), 4, name)
            self.assertEqual(len(set(shades)), 4, f"{name}: duplicate shades {shades}")
            for shade in shades:
                self.assertRegex(shade, r"^#[0-9A-F]{6}$", name)

    def test_rejects_invalid_primary(self):
        with self.assertRaises(ValueError):
            spinner_shades("not-a-color")

    def test_recolor_entries_match_upstream_hardcoded_literals(self):
        entries = recolor_entries("#226d1e")
        self.assertEqual(
            [entry["match"] for entry in entries],
            list(RAINBOW_MATCHES) + list(CORNER_MATCHES),
        )
        self.assertEqual(
            [entry["replace"] for entry in entries],
            list(spinner_shades("#226d1e")) * 2,
        )

    def test_semantic_status_colors_are_not_remapped(self):
        # These keep fixed meanings (red=no-drop, green=copy, etc.) and must
        # never enter the theme-derived recolor map.
        semantic = {"#FE0000", "#06B231", "#606060", "#F27400", "#5F3BE4", "#179DD8", "#2C2C2C", "#0A6857"}
        mapped = {entry["match"].upper() for entry in recolor_entries("#226d1e")}
        self.assertFalse(semantic & mapped, f"semantic colors were remapped: {semantic & mapped}")

    def test_shades_are_hue_consistent_with_primary(self):
        # All shades should share the primary's hue family (no rainbow drift).
        import colorsys
        primary = "#1557bd"
        hue, _, _ = colorsys.rgb_to_hls(*(int(primary[i:i + 2], 16) / 255 for i in (1, 3, 5)))
        for shade in spinner_shades(primary):
            shade_hue, _, _ = colorsys.rgb_to_hls(*(int(shade[i:i + 2], 16) / 255 for i in (1, 3, 5)))
            self.assertLess(min(abs(shade_hue - hue), 1 - abs(shade_hue - hue)), 0.02)


if __name__ == "__main__":
    unittest.main()
