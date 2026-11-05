"""Tests for staged cursor-output validation."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_staged_theme import validate_compiled_theme


REQUIRED_SHAPES = ("left_ptr", "xterm", "wait", "bottom_right_corner")
VALID_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"></svg>'


class ValidateCompiledThemeTests(unittest.TestCase):
    def make_theme(self, root: Path) -> tuple[Path, Path]:
        theme = root / "Bibata-Material-Test"
        scalable_theme = root / "scalable" / "Bibata-Material-Test"
        cursors = theme / "cursors"
        hypr = theme / "hyprcursors"
        scalable = scalable_theme / "cursors_scalable"
        cursors.mkdir(parents=True)
        hypr.mkdir()
        scalable.mkdir(parents=True)
        (theme / "index.theme").write_text("[Icon Theme]\nName=Test\n", encoding="utf-8")
        (theme / "manifest.hl").write_text("name = Test\n", encoding="utf-8")

        for shape in REQUIRED_SHAPES:
            (cursors / shape).write_bytes(b"Xcur" + b"\0" * 12)
            with zipfile.ZipFile(hypr / f"{shape}.hlc", "w") as archive:
                archive.writestr("meta.hl", "resize_algorithm = none\n")
                archive.writestr(f"{shape}.svg", VALID_SVG)

            shape_dir = scalable / shape
            shape_dir.mkdir()
            (shape_dir / f"{shape}.svg").write_text(VALID_SVG, encoding="utf-8")
            (shape_dir / "metadata.json").write_text(
                json.dumps([{
                    "filename": f"{shape}.svg",
                    "hotspot_x": 0,
                    "hotspot_y": 0,
                    "nominal_size": 256,
                }]),
                encoding="utf-8",
            )
        return theme, scalable_theme

    def test_accepts_complete_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            theme, scalable_theme = self.make_theme(Path(temporary))
            validate_compiled_theme(theme, scalable_theme)

    def test_rejects_missing_xcursor_shape(self):
        with tempfile.TemporaryDirectory() as temporary:
            theme, scalable_theme = self.make_theme(Path(temporary))
            (theme / "cursors" / "wait").unlink()
            with self.assertRaisesRegex(RuntimeError, "Xcursor shape is missing"):
                validate_compiled_theme(theme, scalable_theme)

    def test_rejects_malformed_svg_frame(self):
        with tempfile.TemporaryDirectory() as temporary:
            theme, scalable_theme = self.make_theme(Path(temporary))
            (scalable_theme / "cursors_scalable" / "xterm" / "xterm.svg").write_text(
                "<svg>", encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeError, "invalid SVG frame"):
                validate_compiled_theme(theme, scalable_theme)


if __name__ == "__main__":
    unittest.main()
