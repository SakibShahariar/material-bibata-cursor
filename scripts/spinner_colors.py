#!/usr/bin/env python3
"""Theme-derived spinner shades for the animated cursors.

The pinned Bibata `wait` and `left_ptr_watch` SVGs use four hardcoded rainbow
colors in addition to the three recolor slots (body/primary/watch). Those four
never changed between themes, so every theme rendered the same rainbow busy
cursor. This module derives four shades from each theme's primary color so the
spinner follows the theme instead.

The match colors are the exact literals in the upstream SVGs. Order matters:
the four wedges appear in this sequence in every animation frame.
"""
from __future__ import annotations

import colorsys
import re

RAINBOW_MATCHES = ("#F05024", "#FCB813", "#7EBA41", "#32A0DA")

# Lightness offsets applied to the primary color's own lightness. The primary
# itself sits in the middle two shades; the outer two add contrast so the
# spinning motion remains readable against the theme's background.
_LIGHTNESS_OFFSETS = (-0.18, -0.06, 0.06, 0.18)
_MIN_LIGHTNESS = 0.20
_MAX_LIGHTNESS = 0.88


def _hex_to_hls(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    red, green, blue = (int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    return hue, lightness, saturation


def _hls_to_hex(hue: float, lightness: float, saturation: float) -> str:
    red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
    return "#{:02X}{:02X}{:02X}".format(
        round(red * 255), round(green * 255), round(blue * 255)
    )


def spinner_shades(primary: str) -> tuple[str, str, str, str]:
    """Return four distinct hex shades of `primary` aligned with RAINBOW_MATCHES."""
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", primary) is None:
        raise ValueError(f"invalid primary color: {primary!r}")
    hue, lightness, saturation = _hex_to_hls(primary)
    spread = [lightness + offset for offset in _LIGHTNESS_OFFSETS]
    # Shift the whole spread into range so clamping never collapses two shades
    # into the same value (e.g. a very light primary would clamp two to white).
    if spread[-1] > _MAX_LIGHTNESS:
        shift = spread[-1] - _MAX_LIGHTNESS
        spread = [value - shift for value in spread]
    if spread[0] < _MIN_LIGHTNESS:
        shift = _MIN_LIGHTNESS - spread[0]
        spread = [value + shift for value in spread]
    shades = [_hls_to_hex(hue, value, saturation) for value in spread]
    return tuple(shades)  # type: ignore[return-value]


def recolor_entries(primary: str) -> list[dict[str, str]]:
    """Return render.json-style recolor entries for the four rainbow colors."""
    return [
        {"match": match, "replace": shade}
        for match, shade in zip(RAINBOW_MATCHES, spinner_shades(primary))
    ]
