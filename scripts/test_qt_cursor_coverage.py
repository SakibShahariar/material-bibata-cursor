#!/usr/bin/env python3
"""Tests that Qt's X11 cursor names all resolve in the theme (#44)."""
import sys
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_svg_cursors as gen

# X11 names Qt XCB requests via cursorIdForShape() (qxcbcursor.cpp) plus DND.
QT_X11_NAMES = (
    "left_ptr", "center_ptr", "crosshair", "watch", "xterm",
    "sb_v_double_arrow", "sb_h_double_arrow", "top_right_corner",
    "bottom_right_corner", "fleur", "hand2", "hand1", "grabbing",
    "question_arrow", "circle", "dnd-copy", "dnd-move", "dnd-link",
)


class QtCursorCoverageTests(unittest.TestCase):
    def index(self):
        cfg = tomllib.loads((REPO_ROOT / "scripts/bibata_cursor/config/build.toml").read_text(encoding="utf-8"))
        return gen.build_name_index(cfg)

    def test_all_qt_x11_names_resolve(self):
        index = self.index()
        missing = [name for name in QT_X11_NAMES if name not in index]
        self.assertEqual(missing, [], f"Qt X11 names with no theme art/alias: {missing}")

    def test_formerly_documented_gap_names_are_not_x11_names(self):
        # These are Qt enum names, not X11 cursor theme names; the theme should
        # not need them, and the docs no longer claim they are gaps.
        index = self.index()
        for enum_name in ("up_arrow", "split_v", "split_h", "whatsthis"):
            docs = (REPO_ROOT / "docs/COMPATIBILITY.md").read_text(encoding="utf-8")
            self.assertNotIn(f"`{enum_name}` | `Qt::", docs)

    def test_docs_matrix_in_sync(self):
        import subprocess
        result = subprocess.run([sys.executable, str(REPO_ROOT / "scripts/validate_cursor_names.py")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
