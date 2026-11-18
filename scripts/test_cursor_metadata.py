#!/usr/bin/env python3
"""Tests for the descriptive cursor metadata and its validators (#70)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_cursor_metadata import REMAP_PAIRS, build_metadata, main as generate_main
from validate_cursor_metadata import main as validate_main


class CursorMetadataTests(unittest.TestCase):
    def test_generated_metadata_is_committed_and_current(self):
        path = REPO_ROOT / "scripts" / "cursor-metadata.json"
        self.assertTrue(path.is_file())
        with mock.patch.object(sys, "argv", ["generate_cursor_metadata.py", "--check"]):
            self.assertEqual(generate_main(), 0)

    def test_metadata_describes_current_sources(self):
        meta = build_metadata()
        self.assertEqual(meta["schema_version"], 1)
        self.assertGreater(len(meta["cursors"]), 50)
        left = meta["cursors"]["left_ptr"]
        self.assertEqual(left["hotspot"], [55, 17])
        self.assertEqual(left["handedness"], "remap:right_ptr")
        self.assertIn("default", left["aliases"] + left["css_aliases"])
        self.assertIsNotNone(meta["cursors"]["wait"]["animation"])
        self.assertIsNone(meta["cursors"]["xterm"]["animation"])

    def test_remap_pairs_symmetric(self):
        for a, b in REMAP_PAIRS.items():
            self.assertEqual(REMAP_PAIRS[b], a)

    def test_validator_checks_installed_theme(self):
        icons = Path.home() / ".local" / "share" / "icons"
        if not (icons / "Bibata-Material-Peach" / "cursors_scalable").is_dir():
            self.skipTest("no installed Peach theme")
        with mock.patch.object(sys, "argv", ["validate_cursor_metadata.py", "--themes", "Peach"]):
            self.assertEqual(validate_main(), 0)


if __name__ == "__main__":
    unittest.main()
