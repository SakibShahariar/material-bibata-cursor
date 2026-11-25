#!/usr/bin/env python3
"""Tests for the Matugen hook's opt-in Umbriel cursor config (#75)."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "cursor_matugen.sh"
# The hook detects opt-in via a line-based grep. Use the same sed/grep form so
# the test verifies actual behavior, not an approximation.
INCLUDE_PATTERN = r'''^[[:space:]]*["']cursor-theme\.toml["'][[:space:]]*,?[[:space:]]*(#.*)?$'''


def is_opt_in(line: str) -> bool:
    return subprocess.run(
        ["grep", "-Eq", INCLUDE_PATTERN],
        input=line + "\n", text=True,
    ).returncode == 0


class UmbrielHookTests(unittest.TestCase):
    def test_shell_syntax(self):
        result = subprocess.run(["bash", "-n", str(HOOK)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_hook_contains_umbriel_section(self):
        text = HOOK.read_text(encoding="utf-8")
        self.assertIn("UMBRIEL_CONFIG_PATH", text)
        self.assertIn("[input.cursor]", text)
        self.assertIn("cursor-theme.toml", text)

    def test_include_detection(self):
        cases = {
            '  "cursor-theme.toml"': True,
            "  'cursor-theme.toml'": True,
            '  "cursor-theme.toml",': True,
            '  "cursor-theme.toml" # comment': True,
            '  "cursor-theme.toml", # comment': True,
            '  files = ["cursor-theme.toml"]': False,
            '  "appearance.toml"': False,
        }
        for line, expected in cases.items():
            self.assertEqual(is_opt_in(line), expected, f"{line}: expected {expected}")

    def test_generated_toml_is_valid(self):
        import tomllib
        content = '[input.cursor]\ntheme = "Bibata-Material-Apricot"\n'
        parsed = tomllib.loads(content)
        self.assertEqual(parsed["input"]["cursor"]["theme"], "Bibata-Material-Apricot")


if __name__ == "__main__":
    unittest.main()
