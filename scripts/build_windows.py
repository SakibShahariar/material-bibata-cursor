#!/usr/bin/env python3
"""Build Windows .cur cursor themes from themes.json.

Generates .cur files (PNG-compressed, multi-size) for each Bibata-
Material theme. Reuses the same SVG sources and color replacement
logic as the Linux build.

Usage:
    python3 scripts/build_windows.py
    python3 scripts/build_windows.py Ice-Blue
    python3 scripts/build_windows.py --only-dark
    python3 scripts/build_windows.py --only-light
    python3 scripts/build_windows.py --exclude Noir,Charcoal
"""

import argparse
import json
import struct
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = REPO_ROOT / "scripts" / "bibata_cursor" / "svg"
CONFIG_TOML = REPO_ROOT / "scripts" / "bibata_cursor" / "config" / "build.toml"
RENDER_JSON = REPO_ROOT / "scripts" / "bibata_cursor" / "config" / "render.json"
THEMES_JSON = REPO_ROOT / "themes.json"
RSVG_CONVERT = "rsvg-convert"

WINDOWS_SIZES = [16, 24, 32, 48, 64, 128]
THEME_PREFIX = "Bibata-Material-"


def load_themes() -> dict:
    with open(THEMES_JSON) as f:
        return json.load(f)


def load_render_theme(theme_key: str) -> dict:
    with open(RENDER_JSON) as f:
        return json.load(f)[theme_key]


def load_cursor_config() -> tuple[dict, dict]:
    with open(CONFIG_TOML, "rb") as f:
        cfg = tomllib.load(f)
    return cfg["cursors"], cfg["cursor_defaults"]


def get_hotspot(params: dict, defaults: dict, key: str) -> int:
    return params.get(key, defaults.get(key, 128))


def recolor_svg(svg_path: Path, colors: list[dict], dst: Path) -> None:
    data = svg_path.read_text(encoding="utf-8")
    for cmap in colors:
        data = data.replace(cmap["match"], cmap["replace"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(data, encoding="utf-8")


def render_svg_to_png(svg_path: Path, png_path: Path, size: int) -> None:
    subprocess.run(
        [RSVG_CONVERT, "-f", "png", "-w", str(size), "-h", str(size),
         "-o", str(png_path), str(svg_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def find_svg(cursor_name: str) -> Path:
    candidates = [cursor_name, cursor_name.replace("_", "-")]
    for name in candidates:
        for pat in (f"{name}.svg", f"{name}-*.svg"):
            matches = sorted(SVG_DIR.rglob(pat))
            if matches:
                return matches[0]
    return None


def create_cur(images: list[tuple[Path, int, int]], dst: Path) -> None:
    """Create a .cur file.  images = [(png_path, x_hot, y_hot), ...]."""
    from PIL import Image

    entries = []
    for png_path, x_hot, y_hot in images:
        img = Image.open(png_path)
        entries.append((img.width, img.height, x_hot, y_hot,
                        png_path.read_bytes()))

    buf = bytearray()
    buf += struct.pack("<HHH", 0, 2, len(entries))

    offset = 6 + len(entries) * 16
    dir_data = []
    for w, h, x_hot, y_hot, png_bytes in entries:
        bw = 0 if w == 256 else w
        bh = 0 if h == 256 else h
        dir_data.append((bw, bh, x_hot, y_hot, png_bytes, offset))
        offset += len(png_bytes)

    for bw, bh, x_hot, y_hot, png_bytes, img_off in dir_data:
        buf += struct.pack("<BBBBHHII", bw, bh, 0, 0, x_hot, y_hot,
                           len(png_bytes), img_off)

    for _, _, _, _, png_bytes, _ in dir_data:
        buf += png_bytes

    dst.write_bytes(bytes(buf))


def build_theme(theme_key: str, themes: dict,
                out_base: Path) -> int:
    theme = themes[theme_key]
    body, primary, watch = theme["body"], theme["primary"], theme["watch"]

    render_theme = load_render_theme("Bibata-Modern-Classic")
    colors = render_theme["colors"]
    colors[0]["replace"] = body
    colors[1]["replace"] = primary
    colors[2]["replace"] = watch

    cursor_configs, defaults = load_cursor_config()
    theme_dir = out_base / f"{THEME_PREFIX}{theme_key}"
    theme_dir.mkdir(parents=True, exist_ok=True)

    ok, fail = 0, 0

    for cursor_name, params in cursor_configs.items():
        x11_name = params.get("x11_name", "")
        if not x11_name:
            continue

        x_hot = get_hotspot(params, defaults, "x_hotspot")
        y_hot = get_hotspot(params, defaults, "y_hotspot")
        svg_path = find_svg(cursor_name)

        if svg_path is None:
            print(f"  SVG not found for {cursor_name}", file=sys.stderr)
            fail += 1
            continue

        tmp_dir = theme_dir / "_tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        images = []

        for size in WINDOWS_SIZES:
            svg_tmp = tmp_dir / f"{cursor_name}_{size}.svg"
            png_tmp = tmp_dir / f"{cursor_name}_{size}.png"
            recolor_svg(svg_path, colors, svg_tmp)
            render_svg_to_png(svg_tmp, png_tmp, size)

            hx = int(size * x_hot / 256)
            hy = int(size * y_hot / 256)
            images.append((png_tmp, hx, hy))

        cur_path = theme_dir / f"{x11_name}.cur"
        create_cur(images, cur_path)

        for p in tmp_dir.iterdir():
            p.unlink()
        tmp_dir.rmdir()

        ok += 1

    write_index_theme(theme_dir, theme_key)
    write_install_inf(theme_dir, theme_key)
    print(f"  {theme_key}: {ok} cursors")
    return fail


def write_index_theme(theme_dir: Path, theme_key: str) -> None:
    (theme_dir / "index.theme").write_text(
        "[Icon Theme]\n"
        f"Name={THEME_PREFIX}{theme_key.replace('-', ' ')}\n"
        f"Comment=Material Bibata Cursor "
        f"{theme_key.replace('-', ' ')}\n"
        "Inherits=hicolor\n",
        encoding="utf-8",
    )


# Windows registry scheme value -> x11_name of the .cur file to use
# (aligned with the win_name hints in config/build.toml where they are
# unambiguous). Only entries whose .cur file exists get written.
WIN_SCHEME = [
    ("Arrow", "left_ptr"),            # Pointer
    ("Help", "question_arrow"),       # Help
    ("AppStarting", "left_ptr_watch"),# Work
    ("Wait", "wait"),                 # Busy
    ("Crosshair", "crosshair"),       # Cross
    ("IBeam", "xterm"),               # Text
    ("NWPen", "pencil"),              # Handwriting
    ("No", "crossed_circle"),         # Unavailable-style circle-slash
    ("SizeNS", "sb_v_double_arrow"),  # Vert
    ("SizeWE", "sb_h_double_arrow"),  # Horz
    ("SizeNWSE", "fd_double_arrow"),  # Dgn2
    ("SizeNESW", "bd_double_arrow"),  # Dgn1
    ("SizeAll", "move"),              # Move
    ("UpArrow", "sb_up_arrow"),
    ("Hand", "hand2"),                # Link
]


def write_install_inf(theme_dir: Path, theme_key: str) -> None:
    """Write an install.inf so Windows users can right-click -> Install.

    Copies the mapped .cur files into a per-theme subfolder of
    C:\\Windows\\Cursors\\ and registers the scheme under
    HKCU\\Control Panel\\Cursors, so multiple Material Bibata themes can
    be installed side-by-side without overwriting each other."""
    scheme = [(v, f"{n}.cur") for v, n in WIN_SCHEME if (theme_dir / f"{n}.cur").is_file()]
    subdir = f"{THEME_PREFIX}{theme_key}"

    lines = [
        "[Version]",
        'Signature="$CHICAGO$"',
        "Provider=Material Bibata Cursor",
        "",
        "[DefaultInstall]",
        "CopyFiles=Cur.Copy",
        "AddReg=Cursor.Reg",
        "",
        "[Cur.Copy]",
    ]
    lines += [cur for _, cur in scheme]
    lines += [
        "",
        "[DestinationDirs]",
        f'Cur.Copy=10,"Cursors\\{subdir}"',
        "",
        "[Cursor.Reg]",
    ]
    lines += ['HKCU,"Control Panel\\Cursors","{value}",,"%10%\\Cursors\\{subdir}\\{cur}"'.format(
        value=v, subdir=subdir, cur=c) for v, c in scheme]
    lines += ['HKCU,"Control Panel\\Cursors",,,"Material Bibata ({theme})"'.format(theme=theme_key)]
    lines.append("")
    (theme_dir / "install.inf").write_text("\r\n".join(lines), encoding="utf-8")


def filter_themes(themes: dict, args) -> list[str]:
    names = list(themes.keys())
    if args.only_light:
        names = [n for n in names if n.endswith("-Light")]
    elif args.only_dark:
        names = [n for n in names if not n.endswith("-Light")]
    if args.exclude:
        exclude = set(args.exclude.split(","))
        names = [n for n in names if n not in exclude]
    if args.theme:
        if args.theme not in themes:
            print(f"Error: '{args.theme}' not found", file=sys.stderr)
            sys.exit(1)
        names = [args.theme]
    return names


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Windows .cur cursor themes")
    parser.add_argument("theme", nargs="?", default=None)
    parser.add_argument("--only-light", action="store_true")
    parser.add_argument("--only-dark", action="store_true")
    parser.add_argument("--exclude", default=None)
    args = parser.parse_args()

    themes = load_themes()
    names = filter_themes(themes, args)
    if not names:
        print("Error: no themes to build", file=sys.stderr)
        sys.exit(1)

    out_base = REPO_ROOT / "out_win"
    out_base.mkdir(parents=True, exist_ok=True)

    total_ok, total_fail = 0, 0
    for name in names:
        print(f"Building {name}...")
        fail = build_theme(name, themes, out_base)
        total_ok += 1
        total_fail += fail

    print(f"\nDone: {total_ok - total_fail} succeeded, "
          f"{total_fail} failed")
    print(f"Output: {out_base}")
    if total_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()