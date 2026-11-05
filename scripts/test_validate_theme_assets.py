import struct
import unittest
from pathlib import Path

from validate_theme_assets import (
    EXPECTED_XCURSOR_SIZES,
    ValidationError,
    parse_xcursor_sizes,
    validate_xcursor_sizes,
)

IMAGE_TYPE = 0xFFFD0002


def make_xcursor(sizes, *, bad_hotspot=False, truncate=False):
    header_size = 16
    toc_size = 12
    position = header_size + len(sizes) * toc_size
    toc_entries = []
    chunks = []
    for index, size in enumerate(sizes):
        toc_entries.append(struct.pack("<III", IMAGE_TYPE, size, position))
        x_hot = size if bad_hotspot and index == 0 else size // 2
        chunk = (
            struct.pack("<IIII", 36, IMAGE_TYPE, size, 1)
            + struct.pack("<IIIII", size, size, x_hot, size // 2, 40)
            + bytes(size * size * 4)
        )
        chunks.append(chunk)
        position += len(chunk)
    data = (
        struct.pack("<4sIII", b"Xcur", header_size, 1, len(sizes))
        + b"".join(toc_entries)
        + b"".join(chunks)
    )
    return data[:-1] if truncate else data


class XcursorSizeValidationTests(unittest.TestCase):
    def test_accepts_complete_size_ladder(self):
        data = make_xcursor(sorted(EXPECTED_XCURSOR_SIZES))
        sizes = parse_xcursor_sizes(data, Path("cursor"))
        self.assertEqual(sizes, EXPECTED_XCURSOR_SIZES)
        validate_xcursor_sizes(sizes, Path("cursor"))

    def test_rejects_missing_size(self):
        sizes = parse_xcursor_sizes(
            make_xcursor(sorted(EXPECTED_XCURSOR_SIZES - {66})),
            Path("cursor"),
        )
        with self.assertRaisesRegex(ValidationError, "expected Xcursor sizes"):
            validate_xcursor_sizes(sizes, Path("cursor"))

    def test_rejects_hotspot_outside_image(self):
        data = make_xcursor([16], bad_hotspot=True)
        with self.assertRaisesRegex(ValidationError, "hotspot is outside"):
            parse_xcursor_sizes(data, Path("cursor"))

    def test_rejects_truncated_pixel_data(self):
        data = make_xcursor([16], truncate=True)
        with self.assertRaisesRegex(ValidationError, "truncated Xcursor pixels"):
            parse_xcursor_sizes(data, Path("cursor"))


if __name__ == "__main__":
    unittest.main()
