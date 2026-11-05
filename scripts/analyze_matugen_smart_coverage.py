#!/usr/bin/env python3
"""Exercise Matugen 4.2.0 Smart mode with deterministic synthetic image fixtures.

These fixtures cover Smart's four variant thresholds and both mode decisions.
They are regression inputs, not a representative wallpaper corpus.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import zlib
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

try:
    from .analyze_matugen_coverage import delta_e_hex
except ImportError:
    from analyze_matugen_coverage import delta_e_hex

FIXTURES = (
    ("monochrome-dark", (64, 64, 64), "SchemeMonochrome", "dark"),
    ("monochrome-light", (224, 224, 224), "SchemeMonochrome", "light"),
    ("neutral-dark", (96, 64, 64), "SchemeNeutral", "dark"),
    ("neutral-light", (224, 192, 192), "SchemeNeutral", "light"),
    ("tonal-spot-dark", (128, 64, 32), "SchemeTonalSpot", "dark"),
    ("tonal-spot-light", (255, 192, 128), "SchemeTonalSpot", "light"),
    ("vibrant-dark", (255, 0, 0), "SchemeVibrant", "dark"),
    ("vibrant-light", (255, 255, 0), "SchemeVibrant", "light"),
)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_solid_png(path: Path, rgb: tuple[int, int, int]) -> None:
    """Write a dependency-free 128x128 RGB PNG with a uniform pixel value."""
    width = height = 128
    row = b"\x00" + bytes(rgb) * width
    raw = row * height
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(raw))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def run_smart_fixture(
    executable: str, image_path: Path, fallback_hex: str
) -> dict[str, Any]:
    command = [
        executable,
        "image",
        str(image_path),
        "--type",
        "scheme-smart",
        "--mode",
        "smart",
        "--fallback-color",
        fallback_hex,
        "--source-color-index",
        "0",
        "--json",
        "hex",
        "--dry-run",
        "--verbose",
    ]
    try:
        completed = subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=30
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Matugen Smart command failed for {image_path.name}: "
            f"exit={exc.returncode}; stdout={exc.stdout!r}; stderr={exc.stderr!r}"
        ) from exc
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Matugen did not return JSON for {image_path.name}: "
            f"{completed.stdout[:300]!r}; stderr={completed.stderr[:300]!r}"
        ) from exc

    plain_stderr = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", completed.stderr)
    variant_match = re.search(r"variant=(Scheme[A-Za-z]+)", plain_stderr)
    if not variant_match:
        raise RuntimeError(
            f"Matugen did not report its resolved Smart variant for "
            f"{image_path.name}: stderr={plain_stderr!r}"
        )
    payload["_matugen_detected_variant"] = variant_match.group(1)
    return payload


def analyze_smart_images(matugen: str, themes_path: Path) -> dict[str, Any]:
    themes = json.loads(themes_path.read_text(encoding="utf-8"))
    material_themes = {
        name: colors for name, colors in themes.items() if name != "Classic"
    }
    if len(material_themes) != 56:
        raise ValueError(
            f"Expected 56 Material palette variants, found {len(material_themes)}"
        )

    version = subprocess.run(
        [matugen, "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.strip()
    if "4.2.0" not in version:
        raise RuntimeError(f"Expected Matugen 4.2.0, found {version!r}")

    results = []
    with TemporaryDirectory(prefix="matugen-smart-") as temporary:
        directory = Path(temporary)
        for name, rgb, expected_variant, expected_mode in FIXTURES:
            image_path = directory / f"{name}.png"
            write_solid_png(image_path, rgb)
            fallback_hex = "#{:02x}{:02x}{:02x}".format(*rgb)
            payload = run_smart_fixture(matugen, image_path, fallback_hex)
            actual_variant = payload.pop("_matugen_detected_variant")
            actual_mode = payload.get("mode")
            if actual_variant != expected_variant or actual_mode != expected_mode:
                raise RuntimeError(
                    f"{name}: expected {expected_variant}/{expected_mode}, "
                    f"got {actual_variant!r}/{actual_mode!r}"
                )

            try:
                primary_hex = payload["colors"]["primary"][actual_mode]["color"]
            except (KeyError, TypeError) as exc:
                raise ValueError(
                    f"Matugen JSON is missing selected Smart primary for {name}"
                ) from exc
            nearest_name = min(
                material_themes,
                key=lambda theme: delta_e_hex(
                    primary_hex, material_themes[theme]["primary"]
                ),
            )
            nearest_delta = delta_e_hex(
                primary_hex, material_themes[nearest_name]["primary"]
            )
            results.append(
                {
                    "fixture": name,
                    "source_rgb": list(rgb),
                    "expected_variant": expected_variant,
                    "selected_variant": actual_variant,
                    "expected_mode": expected_mode,
                    "selected_mode": actual_mode,
                    "primary_hex": primary_hex,
                    "nearest_theme": nearest_name,
                    "primary_delta_e00": nearest_delta,
                }
            )

    values = sorted(item["primary_delta_e00"] for item in results)
    return {
        "matugen_version": version,
        "sampling": {
            "fixture_count": len(FIXTURES),
            "variants_covered": [
                "SchemeMonochrome",
                "SchemeNeutral",
                "SchemeTonalSpot",
                "SchemeVibrant",
            ],
            "modes_covered": ["dark", "light"],
            "fixture_kind": "synthetic solid-color PNGs",
            "representative_wallpaper_corpus": False,
            "note": (
                "These controlled fixtures verify Matugen Smart's variant and "
                "mode selection paths. They do not estimate real wallpaper "
                "frequency or representative wallpaper palette coverage."
            ),
        },
        "primary_fidelity_delta_e00": {
            "median": values[len(values) // 2],
            "worst": values[-1],
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matugen", default="matugen")
    parser.add_argument(
        "--themes",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "themes.json",
    )
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    try:
        report = analyze_smart_images(args.matugen, args.themes)
    except (OSError, subprocess.SubprocessError, ValueError, RuntimeError) as exc:
        print(f"Matugen Smart coverage failed: {exc}")
        return 1

    print(
        f"Matugen Smart fixtures: {report['sampling']['fixture_count']} "
        f"({', '.join(report['sampling']['variants_covered'])}; dark/light)"
    )
    print(
        "Selected-mode primary ΔE00: "
        f"median {report['primary_fidelity_delta_e00']['median']:.2f}, "
        f"worst {report['primary_fidelity_delta_e00']['worst']:.2f}"
    )
    for item in report["results"]:
        print(
            f"  {item['fixture']}: {item['selected_variant']}/"
            f"{item['selected_mode']} -> {item['primary_hex']} "
            f"({item['nearest_theme']}, ΔE00 {item['primary_delta_e00']:.2f})"
        )

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Full report: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
