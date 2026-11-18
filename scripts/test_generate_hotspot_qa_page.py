#!/usr/bin/env python3
"""Tests for the local hotspot QA page generator."""
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_hotspot_qa_page import main
from qa_hotspots import CRITICAL_SHAPES


class HotspotQAPageTests(unittest.TestCase):
    def test_generates_page_with_critical_shapes(self):
        home_icons = Path.home() / ".local" / "share" / "icons"
        if not (home_icons / "Bibata-Material-Peach" / "cursors_scalable").is_dir():
            self.skipTest("no built Peach theme installed")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "qa.html"
            with mock.patch.object(sys, "argv", [
                "generate_hotspot_qa_page.py",
                "--theme", "Peach",
                "--scalable-dir", str(home_icons),
                "--output", str(output),
            ]):
                rc = main()
            self.assertEqual(rc, 0)
            html = output.read_text(encoding="utf-8")
            self.assertIn("Hotspot QA - Peach", html)
            self.assertGreaterEqual(html.count("<article"), len(CRITICAL_SHAPES))
            self.assertGreaterEqual(html.count("data:image/svg+xml"), len(CRITICAL_SHAPES))
            self.assertIn('class="hotspot"', html)
            self.assertIn("125%", html)
            self.assertIn("150%", html)
            self.assertIn("200%", html)


if __name__ == "__main__":
    unittest.main()
