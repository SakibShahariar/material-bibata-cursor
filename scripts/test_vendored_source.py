#!/usr/bin/env python3
"""Tests that the pinned upstream source is vendored for network-free builds (#40)."""
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_linux


class VendoredSourceTests(unittest.TestCase):
    def vendored_dir(self) -> Path:
        return REPO_ROOT / "scripts" / "bibata_cursor"

    def test_vendored_files_present(self):
        d = self.vendored_dir()
        for rel in ("VENDORED.md", "src/cursor_utils.py", "config/build.toml",
                    "config/render.json", "svg/groups/shared/wait/wait-01.svg"):
            self.assertTrue((d / rel).is_file(), f"missing vendored file: {rel}")

    def test_ensure_upstream_does_not_use_git_for_vendored_source(self):
        d = self.vendored_dir()
        if not (d / "VENDORED.md").is_file():
            self.skipTest("vendored source not present")
        # Any git subprocess during ensure_upstream would mean a network/clone attempt.
        with mock.patch.object(build_linux.subprocess, "run", side_effect=AssertionError("git used")):
            build_linux.ensure_upstream(d)

    def test_incomplete_vendored_source_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            incomplete = Path(temporary) / "bibata_cursor"
            incomplete.mkdir()
            (incomplete / "VENDORED.md").write_text("test\n")
            with self.assertRaises(build_linux.BuildError):
                build_linux.ensure_upstream(incomplete)


if __name__ == "__main__":
    unittest.main()
