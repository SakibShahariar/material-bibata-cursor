import json
import tempfile
import unittest
from pathlib import Path

from validate_contrast import MIN_RATIO, contrast_ratio, validate


class ContrastValidationTest(unittest.TestCase):
    def test_good_theme_passes(self):
        themes = {
            "Ice-Blue": {
                "body": "#1a333d",
                "primary": "#a8cbe2",
                "watch": "#0a1f26",
            }
        }
        errors, _ = validate(themes)
        self.assertEqual(errors, [])

    def test_low_contrast_theme_fails(self):
        themes = {
            "Bad": {
                "body": "#777777",
                "primary": "#888888",
                "watch": "#0a1f26",
            }
        }
        errors, _ = validate(themes)
        self.assertTrue(any("body/primary contrast" in e for e in errors))

    def test_missing_color_fails(self):
        themes = {"Incomplete": {"body": "#1a333d", "primary": "#a8cbe2"}}
        errors, _ = validate(themes)
        self.assertTrue(any("missing required color" in e for e in errors))

    def test_classic_is_exempt(self):
        themes = {
            "Classic": {
                "body": "#777777",
                "primary": "#888888",
                "watch": "#999999",
            }
        }
        errors, _ = validate(themes)
        self.assertEqual(errors, [])

    def test_contrast_ratio_bounds(self):
        self.assertGreaterEqual(contrast_ratio("#000000", "#ffffff"), 21.0)
        self.assertEqual(contrast_ratio("#000000", "#000000"), 1.0)

    def test_real_themes_json_passes(self):
        themes_path = Path(__file__).resolve().parent.parent / "themes.json"
        themes = json.loads(themes_path.read_text(encoding="utf-8"))
        errors, _ = validate(themes)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
