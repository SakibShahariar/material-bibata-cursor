#!/usr/bin/env python3
"""Unit tests for the Python Linux theme builder's validation and config patching."""
import argparse
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_linux


class LoadThemesTests(unittest.TestCase):
    def write_json(self, directory: Path, value) -> Path:
        path = directory / "themes.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_loads_valid_theme_map(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_json(
                Path(temporary),
                {"Coral": {"body": "#112233", "primary": "#AABBCC", "watch": "#000000"}},
            )
            self.assertIn("Coral", build_linux.load_themes(path))

    def test_rejects_path_like_theme_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_json(
                Path(temporary),
                {"../outside": {"body": "#112233", "primary": "#AABBCC", "watch": "#000000"}},
            )
            with self.assertRaises(build_linux.BuildError):
                build_linux.load_themes(path)

    def test_rejects_invalid_color_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_json(
                Path(temporary),
                {"Coral": {"body": "red", "primary": "#AABBCC", "watch": "#000000"}},
            )
            with self.assertRaises(build_linux.BuildError):
                build_linux.load_themes(path)

    def test_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "themes.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(build_linux.BuildError):
                build_linux.load_themes(path)


class ThemeSelectionTests(unittest.TestCase):
    def setUp(self):
        self.parser = argparse.ArgumentParser()
        self.themes = {
            "Classic": {"body": "#000000", "primary": "#FFFFFF", "watch": "#000000"},
            "Coral": {"body": "#112233", "primary": "#AABBCC", "watch": "#000000"},
            "Coral-Light": {"body": "#EEEEEE", "primary": "#112233", "watch": "#FFFFFF"},
        }

    def args(self, **overrides):
        values = {
            "theme": None,
            "themes": None,
            "exclude": None,
            "only_light": False,
            "only_dark": False,
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_defaults_to_all_themes(self):
        self.assertEqual(
            build_linux.select_themes(self.parser, self.args(), self.themes),
            list(self.themes),
        )

    def test_selects_comma_separated_themes_in_requested_order(self):
        args = self.args(themes="Coral-Light,Classic")
        self.assertEqual(
            build_linux.select_themes(self.parser, args, self.themes),
            ["Coral-Light", "Classic"],
        )

    def test_light_filter(self):
        args = self.args(only_light=True)
        self.assertEqual(
            build_linux.select_themes(self.parser, args, self.themes),
            ["Coral-Light"],
        )

    def test_dark_filter_includes_classic(self):
        args = self.args(only_dark=True)
        self.assertEqual(
            build_linux.select_themes(self.parser, args, self.themes),
            ["Classic", "Coral"],
        )

    def test_exclusion(self):
        args = self.args(themes="Classic,Coral", exclude="Classic")
        self.assertEqual(
            build_linux.select_themes(self.parser, args, self.themes), ["Coral"]
        )

    def test_rejects_duplicate_names(self):
        with self.assertRaises(SystemExit):
            build_linux.select_themes(
                self.parser, self.args(themes="Coral,Coral"), self.themes
            )

    def test_rejects_unknown_names(self):
        with self.assertRaises(SystemExit):
            build_linux.select_themes(
                self.parser, self.args(theme="Unknown"), self.themes
            )

    def test_rejects_conflicting_filters(self):
        with self.assertRaises(SystemExit):
            build_linux.select_themes(
                self.parser,
                self.args(only_light=True, only_dark=True),
                self.themes,
            )

    def test_rejects_empty_selection_after_filtering(self):
        with self.assertRaises(SystemExit):
            build_linux.select_themes(
                self.parser, self.args(theme="Classic", only_light=True), self.themes
            )


class ConfigPatchTests(unittest.TestCase):
    def test_patches_colors_and_adds_sizes_without_losing_existing_sizes(self):
        with tempfile.TemporaryDirectory() as temporary:
            work_dir = Path(temporary)
            config_dir = work_dir / "config"
            config_dir.mkdir()
            (config_dir / "render.json").write_text(
                json.dumps({
                    "Bibata-Modern-Classic": {
                        "colors": [
                            {"replace": "#00FF00"},
                            {"replace": "#0000FF"},
                            {"replace": "#FF0000"},
                        ]
                    }
                }),
                encoding="utf-8",
            )
            (config_dir / "build.toml").write_text(
                "[cursor_defaults]\nx11_sizes = [24, 32, 48]\n",
                encoding="utf-8",
            )

            build_linux.patch_theme_config(
                work_dir,
                "Coral",
                {"body": "#112233", "primary": "#AABBCC", "watch": "#000000"},
            )

            render = json.loads((config_dir / "render.json").read_text(encoding="utf-8"))
            self.assertEqual(
                [entry["replace"] for entry in render["Bibata-Modern-Classic"]["colors"]],
                ["#112233", "#AABBCC", "#000000"],
            )
            config = tomllib.loads((config_dir / "build.toml").read_text(encoding="utf-8"))
            sizes = config["cursor_defaults"]["x11_sizes"]
            self.assertTrue({12, 18, 24, 30, 32, 36, 42, 48, 54, 60, 66}.issubset(sizes))
            self.assertEqual(sizes, sorted(set(sizes)))


if __name__ == "__main__":
    unittest.main()
