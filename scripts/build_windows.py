#!/usr/bin/env python3
"""Build Windows .cur/.ani cursor themes from themes.json.

Generates a per-theme folder under out_win/ with .cur files
(PNG-compressed, multi-size) for static cursors, plus animated .ani
files for the busy (wait) and working (left_ptr_watch) cursors, so the
spinner actually spins on Windows. Reuses the same SVG sources and
color replacement logic as the Linux build. The .ani byte layout
mirrors clickgen's (RIFF "ACON", anih header, LIST "fram" of icon
chunks, rate chunk).

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

from generate_svg_cursors import resolve_source_dir

REPO_ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = REPO_ROOT / "scripts" / "bibata_cursor" / "svg"
BIBATA_DIR = SVG_DIR.parent
CONFIG_TOML = BIBATA_DIR / "config" / "build.toml"
RENDER_JSON = BIBATA_DIR / "config" / "render.json"
THEMES_JSON = REPO_ROOT / "themes.json"
RSVG_CONVERT = "rsvg-convert"

WINDOWS_SIZES = [16, 24, 32, 48, 64, 128]
ANI_SIZE = 32
THEME_PREFIX = "Bibata-Material-"

RIFF_HEADER = struct.Struct("<4sI4s")
CHUNK_HEADER = struct.Struct("<4sI")
ANIH_HEADER = struct.Struct("<IIIIIIIII")


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


def single_cur_icon(png_bytes: bytes, w: int, h: int,
                    x_hot: int, y_hot: int) -> bytes:
    """A single-image .cur file, used verbatim as one ANI 'icon' chunk."""
    header = struct.pack("<HHH", 0, 2, 1)
    entry = struct.pack("<BBBBHHII", w & 0xFF, h & 0xFF, 0, 0,
                        x_hot, y_hot, len(png_bytes), 22)
    return header + entry + png_bytes


def write_ani(frames: list[bytes], dst: Path, width: int, height: int,
              rate: int) -> None:
    """Write an .ani file.  frames = single-image .cur bytes, one per
    frame; rate = per-frame duration (clickgen multiplies the Windows
    delay by 2). Mirrors clickgen's to_ani() byte-for-byte."""
    n = len(frames)
    anih = ANIH_HEADER.pack(36, n, n, 0, 0, 32, 1, 1, 1)

    icons = []
    for icon in frames:
        icons.append(CHUNK_HEADER.pack(b"icon", len(icon)))
        icons.append(icon)
        if len(icon) & 1:
            icons.append(b"\0")

    fram = (CHUNK_HEADER.pack(b"LIST", sum(len(c) for c in icons) + 4)
            + b"fram" + b"".join(icons))

    rates = b"".join(struct.pack("<I", rate) for _ in range(n))
    rate_chunk = CHUNK_HEADER.pack(b"rate", len(rates)) + rates

    chunks = CHUNK_HEADER.pack(b"anih", len(anih)) + anih + fram + rate_chunk
    buf = RIFF_HEADER.pack(b"RIFF", len(chunks) + 4, b"ACON") + chunks
    dst.write_bytes(buf)


def render_frame_icon(svg_path: Path, colors: list[dict], tmp_dir: Path,
                      stem: str, idx: int, x_hot: int, y_hot: int) -> bytes:
    svg_tmp = tmp_dir / f"{stem}_{idx}.svg"
    png_tmp = tmp_dir / f"{stem}_{idx}.png"
    recolor_svg(svg_path, colors, svg_tmp)
    render_svg_to_png(svg_tmp, png_tmp, ANI_SIZE)
    hx = int(ANI_SIZE * x_hot / 256)
    hy = int(ANI_SIZE * y_hot / 256)
    w, h = ANI_SIZE, ANI_SIZE
    return single_cur_icon(png_tmp.read_bytes(), w, h, hx, hy)


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
        is_animated = "*" in params.get("png", "")

        if svg_path is None:
            print(f"  SVG not found for {cursor_name}", file=sys.stderr)
            fail += 1
            continue

        tmp_dir = theme_dir / "_tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        if is_animated:
            png_ref = params["png"]
            anim_dirname = png_ref.split("*")[0].rstrip("-")
            resolved = resolve_source_dir(BIBATA_DIR, "modern")
            src_dir = resolved.get(anim_dirname)
            if src_dir is None or not src_dir.is_dir():
                src_dir = svg_path.parent
            frame_files = sorted(src_dir.glob("*.svg"))
            if not frame_files:
                print(f"  No animation frames for {cursor_name}", file=sys.stderr)
                fail += 1
                continue

            (theme_dir / f"{x11_name}.cur").unlink(missing_ok=True)
            win_delay = params.get("win_delay", defaults.get("win_delay", 1))
            rate = int(round(win_delay * 2))
            frames = [
                render_frame_icon(f, colors, tmp_dir, cursor_name, i, x_hot, y_hot)
                for i, f in enumerate(frame_files)
            ]
            ani_path = theme_dir / f"{x11_name}.ani"
            write_ani(frames, ani_path, ANI_SIZE, ANI_SIZE, rate)

            for p in tmp_dir.iterdir():
                p.unlink()
            tmp_dir.rmdir()

            ok += 1
            continue

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


# Windows registry scheme value -> x11_name of the cursor file to use
# (aligned with the win_name hints in config/build.toml where they are
# unambiguous). Install.inf points at the .ani file when a theme ships
# one (Busy/Work), otherwise the .cur. Only entries whose file exists
# get written.
WIN_SCHEME = [
    ("Arrow", "left_ptr"),            # Pointer
    ("Help", "question_arrow"),       # Help
    ("AppStarting", "left_ptr_watch"),# Work (animated .ani)
    ("Wait", "wait"),                 # Busy (animated .ani)
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


def scheme_file(theme_dir: Path, x11_name: str) -> str:
    for ext in (".ani", ".cur"):
        if (theme_dir / f"{x11_name}{ext}").is_file():
            return f"{x11_name}{ext}"
    return f"{x11_name}.cur"


def write_install_inf(theme_dir: Path, theme_key: str) -> None:
    """Write an install.inf so Windows users can right-click -> Install.

    Follows the clickgen/Vimix layout that reliably shows the theme in
    the Mouse Properties -> Pointers scheme dropdown:
      * a named scheme value under Cursors\\Schemes listing all 15
        cursor slots comma-joined in the fixed required order, and
      * live values under Cursors written with REG_EXPAND_SZ
        (0x00020000) so the %10% paths expand.
    Busy/Work use the animated .ani files (falling back to .cur only if
    a theme ships none). Files land in a per-theme C:\\Windows\\Cursors\\
    subfolder so multiple Material Bibata themes can coexist."""
    scheme = [(v, scheme_file(theme_dir, n)) for v, n in WIN_SCHEME
              if (theme_dir / f"{n}.cur").is_file() or (theme_dir / f"{n}.ani").is_file()]
    subdir = f"{THEME_PREFIX}{theme_key}"
    scheme_name = f"Material Bibata ({theme_key})"

    cur_dir = f"Cursors\\{subdir}"
    frame = "%10%\\{cd}\\{f}"
    cur_paths = ",".join(frame.format(cd=cur_dir, f=cur) for _, cur in scheme)

    lines = [
        "[Version]",
        'signature="$CHICAGO$"',
        "Provider=Material Bibata Cursor",
        "",
        "[DefaultInstall]",
        "CopyFiles = Scheme.Cur",
        "AddReg = Scheme.Reg,Wreg",
        "",
        "[Scheme.Cur]",
    ]
    lines += [cur for _, cur in scheme]
    lines += [
        "",
        "[DestinationDirs]",
        f'Scheme.Cur = 10,"%CUR_DIR%"',
        "",
        "[Scheme.Reg]",
        f'HKCU,"Control Panel\\Cursors\\Schemes","%SCHEME_NAME%",,"{cur_paths}"',
        "",
        "[Wreg]",
        f'HKCU,"Control Panel\\Cursors",,0x00020000,"%SCHEME_NAME%"',
    ]
    for value, cur in scheme:
        lines.append(f'HKCU,"Control Panel\\Cursors",{value},0x00020000,"{frame.format(cd=cur_dir, f=cur)}"')
    lines += [
        "",
        "[Strings]",
        f'CUR_DIR = "{cur_dir}"',
        f'SCHEME_NAME = "{scheme_name}"',
        "",
    ]
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