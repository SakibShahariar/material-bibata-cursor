#!/usr/bin/env python3
"""Tests for the left-handed mirror transform and cursor classification (#72)."""
import sys
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Mirrored X coordinate and hotspot: pixel indices map x -> (N-1)-x.
def mirror_coord(value: int, nominal_size: int) -> int:
    return (nominal_size - 1) - value


REMAP_PAIRS = (
    ("left_side", "right_side"),
    ("left_tee", "right_tee"),
    ("bottom_left_corner", "bottom_right_corner"),
    ("top_left_corner", "top_right_corner"),
    ("ll_angle", "lr_angle"),
    ("ul_angle", "ur_angle"),
    ("sb_left_arrow", "sb_right_arrow"),
    ("sb_down_arrow", "sb_up_arrow"),
    ("left_ptr", "right_ptr"),
    ("bottom_side", "top_side"),
    ("bottom_tee", "top_tee"),
)
DO_NOT_MIRROR = {"xterm", "person", "pin"}
MANUAL_REVIEW = {"hand1", "hand2", "grabbing", "pencil", "question_arrow",
                 "context-menu", "circle", "copy", "link", "pointer-move",
                 "dnd-ask", "dnd-copy", "dnd-link", "dnd_no_drop", "vertical-text"}


class LeftHandedTests(unittest.TestCase):
    def test_transform_odd_and_even_boundaries(self):
        # Odd size 33: 0<->32, center 16 stays 16.
        self.assertEqual(mirror_coord(0, 33), 32)
        self.assertEqual(mirror_coord(32, 33), 0)
        self.assertEqual(mirror_coord(16, 33), 16)
        # Even size 256: 0<->255, 128<->127 (center shifts by one, expected).
        self.assertEqual(mirror_coord(0, 256), 255)
        self.assertEqual(mirror_coord(255, 256), 0)
        self.assertEqual(mirror_coord(128, 256), 127)
        self.assertEqual(mirror_coord(127, 256), 128)
        self.assertEqual(mirror_coord(55, 256), 200)

    def test_all_build_toml_hotspots_transform_in_bounds(self):
        cfg = tomllib.loads((REPO_ROOT / "scripts/bibata_cursor/config/build.toml").read_text(encoding="utf-8"))
        defaults = cfg["cursor_defaults"]
        print_count = 0
        for name, params in cfg["cursors"].items():
            if name in DO_NOT_MIRROR or name in MANUAL_REVIEW:
                continue
            hx = params.get("x_hotspot", defaults["x_hotspot"])
            hy = params.get("y_hotspot", defaults["y_hotspot"])
            size = 256
            mx, my = mirror_coord(hx, size), hy
            self.assertTrue(0 <= mx < size and 0 <= my < size, f"{name}: hotspot out of bounds")
            print_count += 1
        self.assertGreater(print_count, 20)

    def test_mirrored_artwork_keeps_hotspot_inside(self):
        import re
        import subprocess
        import tempfile
        from PIL import Image
        from generate_svg_cursors import recolor_svg
        src_path = REPO_ROOT / "scripts/bibata_cursor/svg/groups/modern/left_ptr.svg"
        if not src_path.is_file():
            self.skipTest("vendored SVG tree missing")
        text = recolor_svg(src_path.read_text(encoding="utf-8"), "#0f1519", "#ffc9a8", "#000000")
        m = re.search(r"(<svg[^>]*>)(.*)(</svg>)", text, re.S)
        mirrored = m.group(1) + '<g transform="translate(256,0) scale(-1,1)">' + m.group(2) + "</g>" + m.group(3)
        with tempfile.TemporaryDirectory() as temporary:
            p = Path(temporary)
            for label, content, hx in (("normal", text, 55), ("mirror", mirrored, mirror_coord(55, 256))):
                svg, png = p / f"{label}.svg", p / f"{label}.png"
                svg.write_text(content, encoding="utf-8")
                subprocess.run(["rsvg-convert", "-f", "png", "-w", "48", "-h", "48",
                                "-o", str(png), str(svg)], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                im = Image.open(png).convert("RGBA")
                alpha = im.getchannel("A")
                bbox = alpha.getbbox()
                px = (round(hx * 48 / 256), round(17 * 48 / 256))
                self.assertTrue(bbox[0] <= px[0] < bbox[2] and bbox[1] <= px[1] < bbox[3],
                                f"{label}: mapped hotspot outside artwork")

    def test_remap_pairs_are_bijective(self):
        lefts = [a for a, _ in REMAP_PAIRS]
        rights = [b for _, b in REMAP_PAIRS]
        self.assertEqual(len(set(lefts)), len(lefts))
        self.assertEqual(len(set(rights)), len(rights))
        self.assertFalse(set(lefts) & set(rights), "a name cannot be both a left and right source")

    def test_all_directional_names_classified(self):
        cfg = tomllib.loads((REPO_ROOT / "scripts/bibata_cursor/config/build.toml").read_text(encoding="utf-8"))
        names = set(cfg["cursors"])
        for a, b in REMAP_PAIRS:
            self.assertIn(a, names, f"missing {a}")
            self.assertIn(b, names, f"missing {b}")
        for name in DO_NOT_MIRROR | MANUAL_REVIEW:
            self.assertIn(name, names, f"missing {name}")


if __name__ == "__main__":
    unittest.main()
