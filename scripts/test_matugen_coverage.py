#!/usr/bin/env python3
"""Unit tests for the Matugen-generated palette coverage analyzer."""

import unittest

try:
    from .analyze_matugen_coverage import (
        extract_primary_colors,
        percentile,
        primary_hue_chroma_region,
        source_colors,
        summarize_matcher_selection,
        summarize_mode_aware_selection,
        find_closest_theme,
        SCHEME_TYPES,
    )
except ImportError:
    from analyze_matugen_coverage import (
        extract_primary_colors,
        percentile,
        primary_hue_chroma_region,
        source_colors,
        summarize_matcher_selection,
        SCHEME_TYPES,
    )


class MatugenCoverageTests(unittest.TestCase):
    def test_source_grid_is_deterministic_and_covers_hue_saturation_lightness(self):
        samples = source_colors()
        self.assertEqual(len(samples), 216)
        self.assertEqual({hue for hue, _ in samples}, set(range(0, 360, 15)))
        self.assertEqual(len({color for _, color in samples}), 216)
        self.assertEqual(len(SCHEME_TYPES), 9)
        self.assertNotIn("scheme-smart", SCHEME_TYPES)

    def test_summarizes_matcher_selection_against_primary_only_winner(self):
        samples = [
            {
                "matcher_theme": "A",
                "nearest_primary_theme": "A",
                "matcher_primary_delta_e00": 4.0,
                "primary_delta_e00": 4.0,
            },
            {
                "matcher_theme": "B",
                "nearest_primary_theme": "A",
                "matcher_primary_delta_e00": 9.0,
                "primary_delta_e00": 5.0,
            },
        ]
        result = summarize_matcher_selection(samples)
        self.assertEqual(result["selection_mismatch_count"], 1)
        self.assertEqual(result["selection_mismatch_rate"], 0.5)
        self.assertEqual(result["primary_fidelity_regret_delta_e00"]["mean"], 2.0)
        self.assertEqual(result["selected_primary_delta_e00"]["median"], 6.5)

    def test_mode_aware_matcher_filters_candidates_to_requested_mode(self):
        themes = {
            "Dark": {"body": "#000000", "primary": "#ff0000"},
            "Light": {"body": "#ffffff", "primary": "#0000ff"},
            "Classic": {"body": "#000000", "primary": "#ff0000"},
        }
        light_name, _ = find_closest_theme(
            "#ff0000", themes, primary_weight=1.0, body_weight=0.0, mode="light"
        )
        dark_name, _ = find_closest_theme(
            "#0000ff", themes, primary_weight=1.0, body_weight=0.0, mode="dark"
        )
        self.assertEqual(light_name, "Light")
        self.assertEqual(dark_name, "Dark")

    def test_mode_aware_summary_counts_cross_mode_selections(self):
        samples = [
            {
                "mode": "light",
                "mode_matcher_theme": "Light",
                "nearest_primary_theme": "Light",
                "mode_matcher_primary_delta_e00": 1.0,
                "primary_delta_e00": 1.0,
            },
            {
                "mode": "light",
                "mode_matcher_theme": "Dark",
                "nearest_primary_theme": "Light",
                "mode_matcher_primary_delta_e00": 5.0,
                "primary_delta_e00": 2.0,
            },
        ]
        result = summarize_mode_aware_selection(samples)
        self.assertEqual(result["mode_mismatch_count"], 1)
        self.assertEqual(result["selection_mismatch_count"], 1)
        self.assertEqual(result["selected_primary_delta_e00"]["median"], 3.0)

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
