#!/usr/bin/env python3
"""Tests for the upstream animation-contract validator (#39)."""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_animations import main, upstream_contract, BIBATA_DIR


class AnimationContractTests(unittest.TestCase):
    def test_upstream_contract(self):
        if not (BIBATA_DIR / "config" / "build.toml").is_file():
            self.skipTest("pinned Bibata source is not vendored")
        contract = upstream_contract(BIBATA_DIR)
        for shape in ("wait", "left_ptr_watch"):
            self.assertEqual(len(contract[shape]["frames"]), 54)
            self.assertEqual(set(contract[shape]["delays"]), {40})

    def test_validates_all_installed_themes(self):
        if not (Path.home() / ".local" / "share" / "icons" / "Bibata-Material-Peach").is_dir():
            self.skipTest("no installed themes")
        with mock.patch.object(sys, "argv", ["validate_animations.py", "--themes", "Peach,Apricot"]):
            self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
