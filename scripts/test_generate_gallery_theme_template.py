#!/usr/bin/env python3
"""Tests for the gallery's downloadable theme template."""
import base64
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_gallery_theme_template import BIBATA_DIR, build_template_tree, main


class GalleryThemeTemplateTests(unittest.TestCase):
    def test_template_tree_has_all_shapes_and_metadata(self):
        if not (BIBATA_DIR / "config" / "build.toml").is_file():
            self.skipTest("pinned Bibata source is not vendored")
        template = build_template_tree(BIBATA_DIR)
        files = template["files"]
        self.assertIn("Bibata-Material-Custom/index.theme", files)
        self.assertIn("Bibata-Material-Custom/README.txt", files)
        svgs = [p for p in files if p.endswith(".svg")]
        metadata = [p for p in files if p.endswith("metadata.json")]
        self.assertGreater(len(svgs), 100)
        # One metadata.json per real shape dir (animated shapes have many SVGs).
        self.assertGreaterEqual(len(metadata), 50)
        self.assertLessEqual(len(metadata), len(svgs))

    def test_all_color_slots_are_placeholders(self):
        if not (BIBATA_DIR / "config" / "build.toml").is_file():
            self.skipTest("pinned Bibata source is not vendored")
        template = build_template_tree(BIBATA_DIR)
        literals = {"#00FF00", "#0000FF", "#FF0000", "#F05024", "#FCB813", "#7EBA41",
                    "#32A0DA", "#FDBE2A", "#96C865", "#F1613A", "#4FADDF"}
        for path, content in template["files"].items():
            if not path.endswith(".svg"):
                continue
            leaked = [c for c in literals if c in content]
            self.assertEqual(leaked, [], f"{path} still has {leaked}")

    def test_aliases_exclude_real_dirs(self):
        if not (BIBATA_DIR / "config" / "build.toml").is_file():
            self.skipTest("pinned Bibata source is not vendored")
        template = build_template_tree(BIBATA_DIR)
        prefix = "Bibata-Material-Custom/cursors_scalable/"
        real_dirs = {p.split("/")[-2] for p in template["files"] if "/cursors_scalable/" in p}
        for alias, target in template["css_links"].items():
            self.assertNotEqual(alias, target)
            self.assertNotIn(alias, real_dirs, f"alias {alias} collides with a real shape dir")
            self.assertIn(target, real_dirs)

    def test_committed_template_blob_decodes(self):
        path = Path(__file__).resolve().parent.parent / "docs" / "customizer" / "theme-template.js"
        if not path.is_file():
            self.skipTest("theme template blob not generated")
        text = path.read_text(encoding="utf-8")
        self.assertIn("window.GALLERY_THEME_TEMPLATE=", text)
        b64 = text.split("='", 1)[1].rsplit("';", 1)[0]
        template = json.loads(gzip.decompress(base64.b64decode(b64)).decode("utf-8"))
        self.assertGreater(len(template["files"]), 100)
        self.assertIn("css_links", template)


if __name__ == "__main__":
    unittest.main()
