#!/usr/bin/env python3
"""Keep the published gallery palette data aligned with the build source."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class ThemeDataSyncTests(unittest.TestCase):
    def test_gallery_palette_data_matches_build_palette_data(self):
        build_data = json.loads((ROOT / "themes.json").read_text(encoding="utf-8"))
        gallery_data = json.loads(
            (ROOT / "docs" / "themes.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            gallery_data,
            build_data,
            "docs/themes.json must mirror themes.json so the gallery previews "
            "the same colors that the builders compile",
        )


if __name__ == "__main__":
    unittest.main()
