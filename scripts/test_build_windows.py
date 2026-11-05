#!/usr/bin/env python3
"""Unit tests for Windows SVG source indexing and cursor-name resolution."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_windows


class SvgIndexTests(unittest.TestCase):
    def test_exact_name_precedes_wildcard_and_underscore_alias(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exact = root / "z" / "left_ptr.svg"
            wildcard = root / "a" / "left_ptr-alt.svg"
            alias = root / "left-ptr.svg"
            for path in (exact, wildcard, alias):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("<svg/>", encoding="utf-8")

            index = build_windows.build_svg_index(root)

            self.assertEqual(build_windows.find_svg("left_ptr", index), exact)
            self.assertEqual(build_windows.find_svg("left_ptr-alt", index), wildcard)

    def test_wildcard_uses_lexicographically_first_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            later = root / "z" / "resize-nwse-extra.svg"
            first = root / "a" / "resize-nwse-alt.svg"
            for path in (later, first):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("<svg/>", encoding="utf-8")

            index = build_windows.build_svg_index(root)

            self.assertEqual(build_windows.find_svg("resize-nwse", index), first)

    def test_exact_duplicate_basename_uses_lexicographically_first_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            later = root / "z" / "pointer.svg"
            first = root / "a" / "pointer.svg"
            for path in (later, first):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("<svg/>", encoding="utf-8")

            index = build_windows.build_svg_index(root)

            self.assertEqual(build_windows.find_svg("pointer", index), first)

    def test_missing_cursor_returns_none(self):
        with tempfile.TemporaryDirectory() as temporary:
            index = build_windows.build_svg_index(Path(temporary))
            self.assertIsNone(build_windows.find_svg("not-a-cursor", index))


if __name__ == "__main__":
    unittest.main()
