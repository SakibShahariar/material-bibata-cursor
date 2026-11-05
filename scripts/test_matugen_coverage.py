#!/usr/bin/env python3
"""Unit tests for the Matugen-generated palette coverage analyzer."""

import unittest

try:
    from .analyze_matugen_coverage import (
        extract_primary_colors,
        percentile,
        primary_hue_chroma_region,
        source_colors,
    )
except ImportError:
    from analyze_matugen_coverage import (
        extract_primary_colors,
        percentile,
        primary_hue_chroma_region,
        source_colors,
    )


class MatugenCoverageTests(unittest.TestCase):
    def test_source_grid_is_deterministic_and_covers_hue_saturation_lightness(self):
        samples = source_colors()
        self.assertEqual(len(samples), 216)
        self.assertEqual({hue for hue, _ in samples}, set(range(0, 360, 15)))
        self.assertEqual(len({color for _, color in samples}), 216)

    def test_extracts_both_generated_semantic_primary_roles(self):
        payload = {
            "colors": {
                "primary": {
                    "dark": {"color": "#123456"},
                    "light": {"color": "#abcdef"},
                    "default": {"color": "#123456"},
                }
            }
        }
        self.assertEqual(
            extract_primary_colors(payload),
            {"dark": "#123456", "light": "#abcdef"},
        )

    def test_rejects_missing_or_invalid_primary_role(self):
        with self.assertRaises(ValueError):
            extract_primary_colors({"colors": {}})
        with self.assertRaises(ValueError):
            extract_primary_colors(
                {
                    "colors": {
                        "primary": {
                            "dark": {"color": "#123456"},
                            "light": {"color": "blue"},
                        }
                    }
                }
            )

    def test_generated_primary_region_includes_hue_and_chroma(self):
        self.assertEqual(primary_hue_chroma_region("#808080"), "neutral / C* 0-10")
        self.assertIn("C* ", primary_hue_chroma_region("#ff0000"))

    def test_percentile_uses_linear_interpolation(self):
        self.assertEqual(percentile([0.0, 10.0], 0.5), 5.0)
        self.assertEqual(percentile([1.0, 2.0, 3.0], 1.0), 3.0)


if __name__ == "__main__":
    unittest.main()
