#!/usr/bin/env python3
"""Tests for the opt-in semantic role prototype (#71)."""
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from semantic_roles_prototype import ROLE_MAP, build_report, contrast


class SemanticRolePrototypeTests(unittest.TestCase):
    def test_report_covers_light_and_dark(self):
        report = build_report()
        self.assertEqual(set(report["palettes"]), {"Apricot", "Midnight-Light"})
        self.assertIn("contrast_primary_on_body", report["palettes"]["Apricot"])

    def test_contrast_above_threshold(self):
        report = build_report()
        for key, data in report["palettes"].items():
            self.assertGreater(data["contrast_primary_on_body"], 3.0, key)

    def test_preserved_roles_unchanged(self):
        report = build_report()
        for data in report["palettes"].values():
            self.assertEqual(data["roles"]["copy"], "#06B231")
            self.assertEqual(data["roles"]["dnd-link"], "#606060")

    def test_error_fallback_when_token_absent(self):
        report = build_report()
        for data in report["palettes"].values():
            self.assertFalse(data["error_available"])
            self.assertEqual(data["roles"]["dnd_no_drop"], "#FE0000")


if __name__ == "__main__":
    unittest.main()
