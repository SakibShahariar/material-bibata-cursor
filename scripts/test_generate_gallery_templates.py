#!/usr/bin/env python3
"""Tests for the gallery customizer's SVG templates."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_gallery_templates import SOURCES, generate
from spinner_colors import CORNER_MATCHES, RAINBOW_MATCHES


class GalleryTemplateTests(unittest.TestCase):
    def test_committed_templates_are_present(self):
        root = Path(__file__).resolve().parent.parent
        customizer = root / "docs" / "customizer"
        missing = [f"{n}.svg" for n in SOURCES if not (customizer / f"{n}.svg").is_file()]
        if not (customizer / "templates.js").is_file():
            missing.append("templates.js")
        self.assertEqual(missing, [], f"missing gallery templates: {missing}")

    def test_templates_replace_all_hardcoded_colors_with_tokens(self):
        # Use the real pinned upstream tree so the test reflects actual sources.
        root = Path(__file__).resolve().parent.parent
        svg_root = root / "scripts" / "bibata_cursor" / "svg"
        if not (svg_root / SOURCES["left_ptr"]).is_file():
            self.skipTest("pinned Bibata SVG tree is not vendored")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            written = generate(svg_root, output)
            self.assertEqual(sorted(written), sorted([f"{n}.svg" for n in SOURCES] + ["templates.js"]))
            # No upstream color literal should survive in any template.
            all_literals = {"#00FF00", "#0000FF", "#FF0000", *RAINBOW_MATCHES, *CORNER_MATCHES}
            for template in output.glob("*.svg"):
                text = template.read_text(encoding="utf-8")
                leaked = [c for c in all_literals if c in text]
                self.assertEqual(leaked, [], f"{template.name} still has {leaked}")
            # The wait template must carry spinner/watch placeholders.
            wait = (output / "wait.svg").read_text(encoding="utf-8")
            self.assertIn("{{SPINNER0}}", wait)
            self.assertIn("{{WATCH}}", wait)
            # The corner template must carry corner placeholders.
            corner = (output / "bottom_right_corner.svg").read_text(encoding="utf-8")
            self.assertIn("{{CORNER0}}", corner)


if __name__ == "__main__":
    unittest.main()
