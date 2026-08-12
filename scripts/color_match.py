#!/usr/bin/env python3
"""
color_match.py — CIEDE2000-based nearest-theme matcher for cursor_matugen.sh

Replaces the weighted-HSV distance formula with a perceptually uniform
CIEDE2000 Delta-E calculation in CIELAB space. This is the metric the
color-science / print & textile industries use precisely because raw
HSV (or even Lab Euclidean "Delta-E76") distorts hue differences
unevenly across the color wheel — blues and cyans are one of the worst
offenders, which is exactly the failure mode you were fighting with
dh=5.0.

No external dependencies (avoids `colormath`, which is unmaintained and
has a documented divide-by-zero bug in its CIEDE2000 implementation).

USAGE
-----
CLI (one wallpaper accent vs. a JSON theme map):

    python3 color_match.py "#7fb0d8" themes.json

    themes.json format:
    {
      "ice_blue":   {"body": "#1a333d", "primary": "#a8cbe2"},
      "sky_blue":   {"body": "#173a4a", "primary": "#8fd0f0"},
      ...
    }

    Prints the best-matching theme name to stdout (and nothing else),
    so it's safe to capture directly in fish with `set match (python3 ...)`.

Library use (import from your metadata generator, tests, etc.):

    from color_match import find_closest_theme
    best, score = find_closest_theme("#7fb0d8", themes)
"""

import sys
import json
import math
from typing import Dict, Tuple


# --------------------------------------------------------------------------
# sRGB -> XYZ -> CIELAB
# --------------------------------------------------------------------------

def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"Invalid hex color: {hex_color!r}")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return r / 255.0, g / 255.0, b / 255.0


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb_to_xyz(r: float, g: float, b: float) -> Tuple[float, float, float]:
    r, g, b = _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b)
    # sRGB D65 matrix
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    return x * 100.0, y * 100.0, z * 100.0


# D65 reference white
_XN, _YN, _ZN = 95.0489, 100.0, 108.8840


def _f(t: float) -> float:
    delta = 6.0 / 29.0
    if t > delta ** 3:
        return t ** (1.0 / 3.0)
    return t / (3 * delta ** 2) + 4.0 / 29.0


def xyz_to_lab(x: float, y: float, z: float) -> Tuple[float, float, float]:
    fx, fy, fz = _f(x / _XN), _f(y / _YN), _f(z / _ZN)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return L, a, b


def hex_to_lab(hex_color: str) -> Tuple[float, float, float]:
    return xyz_to_lab(*rgb_to_xyz(*hex_to_rgb(hex_color)))


# --------------------------------------------------------------------------
# CIEDE2000
# --------------------------------------------------------------------------

def ciede2000(lab1: Tuple[float, float, float],
              lab2: Tuple[float, float, float],
              kL: float = 1.0, kC: float = 1.0, kH: float = 1.0) -> float:
    """
    Standard CIEDE2000 Delta-E. kL/kC/kH are the parametric weighting
    factors from the spec (leave at 1.0 for "graphic arts" defaults,
    which is what you want for UI/theme matching).
    """
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2

    C1 = math.hypot(a1, b1)
    C2 = math.hypot(a2, b2)
    C_bar = (C1 + C2) / 2.0

    G = 0.5 * (1 - math.sqrt((C_bar ** 7) / (C_bar ** 7 + 25 ** 7)))
    a1p = a1 * (1 + G)
    a2p = a2 * (1 + G)

    C1p = math.hypot(a1p, b1)
    C2p = math.hypot(a2p, b2)

    def hue_angle(ap, b):
        if ap == 0 and b == 0:
            return 0.0
        h = math.degrees(math.atan2(b, ap))
        return h + 360 if h < 0 else h

    h1p = hue_angle(a1p, b1)
    h2p = hue_angle(a2p, b2)

    dLp = L2 - L1
    dCp = C2p - C1p

    if C1p * C2p == 0:
        dhp = 0.0
    else:
        diff = h2p - h1p
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
        dhp = diff
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2.0)

    L_bar = (L1 + L2) / 2.0
    C_barp = (C1p + C2p) / 2.0

    if C1p * C2p == 0:
        h_barp = h1p + h2p
    else:
        s = h1p + h2p
        diff = abs(h1p - h2p)
        if diff <= 180:
            h_barp = s / 2.0
        elif s < 360:
            h_barp = (s + 360) / 2.0
        else:
            h_barp = (s - 360) / 2.0

    T = (1
         - 0.17 * math.cos(math.radians(h_barp - 30))
         + 0.24 * math.cos(math.radians(2 * h_barp))
         + 0.32 * math.cos(math.radians(3 * h_barp + 6))
         - 0.20 * math.cos(math.radians(4 * h_barp - 63)))

    d_theta = 30 * math.exp(-(((h_barp - 275) / 25) ** 2))
    RC = 2 * math.sqrt((C_barp ** 7) / (C_barp ** 7 + 25 ** 7))
    SL = 1 + (0.015 * (L_bar - 50) ** 2) / math.sqrt(20 + (L_bar - 50) ** 2)
    SC = 1 + 0.045 * C_barp
    SH = 1 + 0.015 * C_barp * T
    RT = -math.sin(math.radians(2 * d_theta)) * RC

    dE = math.sqrt(
        (dLp / (kL * SL)) ** 2 +
        (dCp / (kC * SC)) ** 2 +
        (dHp / (kH * SH)) ** 2 +
        RT * (dCp / (kC * SC)) * (dHp / (kH * SH))
    )
    return dE


def delta_e_hex(hex1: str, hex2: str, kL=1.0, kC=1.0, kH=1.0) -> float:
    return ciede2000(hex_to_lab(hex1), hex_to_lab(hex2), kL, kC, kH)


# --------------------------------------------------------------------------
# Theme matching
# --------------------------------------------------------------------------

def find_closest_theme(
    target_hex: str,
    themes: Dict[str, Dict[str, str]],
    primary_weight: float = 0.75,
    body_weight: float = 0.25,
) -> Tuple[str, float]:
    """
    themes: {theme_name: {"body": "#hex", "primary": "#hex"}}

    Matches primarily on the 'primary' (border) color since that's the
    dominant perceived hue of the cursor, but blends in the body/container
    color at a lower weight so two themes with near-identical borders but
    very different container darkness don't collide. Weights are
    normalized, so they don't need to sum to 1.

    Returns (best_theme_name, delta_e_score). Lower score = closer match.
    A score below ~2.3 is generally "not perceptibly different" to a
    typical viewer; below ~1.0 is "indistinguishable."
    """
    target_lab = hex_to_lab(target_hex)
    total_w = primary_weight + body_weight

    best_name = None
    best_score = math.inf

    for name, cols in themes.items():
        primary_de = ciede2000(target_lab, hex_to_lab(cols["primary"]))
        score = (primary_de * primary_weight) / total_w
        if "body" in cols and body_weight > 0:
            body_de = ciede2000(target_lab, hex_to_lab(cols["body"]))
            score += (body_de * body_weight) / total_w

        if score < best_score:
            best_score = score
            best_name = name

    return best_name, best_score


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _main():
    if len(sys.argv) != 3:
        print("usage: color_match.py <target_hex> <themes.json>", file=sys.stderr)
        sys.exit(1)

    target_hex = sys.argv[1]
    themes_path = sys.argv[2]

    with open(themes_path, "r") as f:
        themes = json.load(f)

    best_name, score = find_closest_theme(target_hex, themes)

    # Print ONLY the theme name to stdout — fish captures this directly.
    print(best_name)
    # Diagnostics go to stderr so they don't pollute the captured value.
    print(f"[color_match] matched '{best_name}' (dE2000={score:.3f})", file=sys.stderr)


if __name__ == "__main__":
    _main()
