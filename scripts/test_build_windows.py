#!/usr/bin/env python3
"""Unit tests for Windows SVG source indexing and cursor-name resolution."""
import sys
import tempfile
import unittest
from unittest.mock import patch
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

class StaticRenderTests(unittest.TestCase):
    def test_recolors_static_source_once_for_all_sizes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "pointer.svg"
            source.write_text("<svg fill='#000000'/>", encoding="utf-8")
            tmp_dir = root / "tmp"
            colors = [{"match": "#000000", "replace": "#FFFFFF"}]

            def fake_render(svg_path, png_path, size):
                png_path.write_bytes(f"png-{size}".encode())

            with patch.object(build_windows, "recolor_svg", wraps=build_windows.recolor_svg) as recolor, \\
                 patch.object(build_windows, "render_svg_to_png", side_effect=fake_render) as render:
                images = build_windows.render_static_cursor(
                    source, colors, tmp_dir, "pointer", 128, 128
                )

            self.assertEqual(recolor.call_count, 1)
            self.assertEqual(render.call_count, len(build_windows.WINDOWS_SIZES))
            self.assertEqual(len(images), len(build_windows.WINDOWS_SIZES))
            self.assertEqual({call.args[0] for call in render.call_args_list}, {tmp_dir / "pointer_recolored.svg"})
            self.assertEqual(
                (tmp_dir / "pointer_recolored.svg").read_text(encoding="utf-8"),
                "<svg fill='#FFFFFF'/>",
            )


class ThemeSelectionTests(unittest.TestCase):
    def setUp(self):
        self.themes = {"Dark": {}, "Light-Light": {}, "Other": {}}

    def args(self, **overrides):
        from types import SimpleNamespace
        values = {"theme": None, "themes": None, "only_light": False, "only_dark": False, "exclude": None}
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_selects_requested_theme_subset_in_order(self):
        self.assertEqual(build_windows.filter_themes(self.themes, self.args(themes="Other,Dark")), ["Other", "Dark"])

    def test_rejects_duplicate_requested_themes(self):
        with self.assertRaises(ValueError):
            build_windows.filter_themes(self.themes, self.args(themes="Dark,Dark"))

    def test_rejects_unknown_requested_theme(self):
        with self.assertRaises(ValueError):
            build_windows.filter_themes(self.themes, self.args(themes="Missing"))

if __name__ == "__main__":
    unittest.main()
