#!/usr/bin/env python3
"""apply_theme.py — set an installed Bibata-Material theme as the active
cursor theme on the current desktop, without rebuilding.

Usage:
    python3 scripts/apply_theme.py Apricot

Supports GNOME/GTK (gsettings), KDE Plasma (plasma-apply-cursortheme),
Hyprland (hyprctl), Sway (swaymsg), an opt-in Niri configuration include,
and the ~/.icons/default XCursor fallback. Reuses the detection and
size-preserving logic from scripts/cursor_matugen.sh.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
THEMES_JSON = REPO_ROOT / "themes.json"


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def resolve_theme(name):
    try:
        themes = json.loads(THEMES_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"could not read themes.json: {exc}")
    if name not in themes:
        fail(
            f"unknown theme '{name}'. Run `just list` for valid names."
        )
    return f"Bibata-Material-{name}"


def find_install(theme_name):
    candidates = [
        Path(os.environ.get("BIBATA_MATERIAL_INSTALL_DIR", ""))
        if os.environ.get("BIBATA_MATERIAL_INSTALL_DIR")
        else Path.home() / ".icons",
        Path(os.environ.get("XDG_DATA_HOME", "")) / "icons"
        if os.environ.get("XDG_DATA_HOME")
        else Path.home() / ".local" / "share" / "icons",
        Path("/usr/share/icons"),
    ]
    for base in candidates:
        if (base / theme_name).is_dir():
            return base
    fail(
        f"theme '{theme_name}' is not installed. Run `just build-one {theme_name.removeprefix('Bibata-Material-')}` first."
    )


def run(cmd, quiet=True):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def cursor_size():
    size = os.environ.get("XCURSOR_SIZE", "")
    if size.isdigit() and int(size) > 0:
        return size
    if shutil.which("hyprctl") and shutil.which("jq") and run(["pgrep", "-x", "Hyprland"]):
        out = subprocess.run(
            ["hyprctl", "getoption", "cursor:size", "-j"],
            capture_output=True, text=True,
        ).stdout
        try:
            value = json.loads(out).get("int")
            if isinstance(value, int) and value > 0:
                return str(value)
        except (json.JSONDecodeError, AttributeError):
            pass
    if shutil.which("gsettings"):
        out = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "cursor-size"],
            capture_output=True, text=True,
        ).stdout.strip().strip("'")
        if out.isdigit() and int(out) > 0:
            return out
    return "24"


def apply_gnome(theme):
    if shutil.which("gsettings") and run(
        ["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", theme]
    ):
        print(f"✓ Set GNOME cursor theme: {theme}")


def apply_plasma(theme):
    if os.environ.get("KDE_SESSION_VERSION") and shutil.which(
        "plasma-apply-cursortheme"
    ):
        if run(["plasma-apply-cursortheme", theme]):
            print(f"✓ Set KDE Plasma cursor theme: {theme}")
        else:
            print("Warning: plasma-apply-cursortheme failed", file=sys.stderr)


def apply_hyprland(theme, size):
    if shutil.which("hyprctl") and run(["pgrep", "-x", "Hyprland"]):
        if run(["hyprctl", "setcursor", theme, size]):
            print(f"✓ Set Hyprland cursor theme: {theme}")
        else:
            print("Warning: hyprctl setcursor failed", file=sys.stderr)


def apply_sway(theme, size):
    if shutil.which("swaymsg") and run(["pgrep", "-x", "sway"]):
        if run(["swaymsg", "seat", "*", "xcursor_theme", theme, size]):
            print(f"✓ Set Sway cursor theme: {theme} (size {size})")
        else:
            print("Warning: swaymsg failed to set the cursor theme", file=sys.stderr)


def apply_niri(theme):
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", "")) / "niri" if os.environ.get("XDG_CONFIG_HOME") else Path.home() / ".config" / "niri"
    config_path = Path(os.environ.get("NIRI_CONFIG", "")) if os.environ.get("NIRI_CONFIG") else config_dir / "config.kdl"
    if not config_path.is_file():
        return
    pattern = re.compile(
        r'^\s*include\s+"(\./)?cursor-theme\.kdl"\s*(//.*)?$'
    )
    if not any(pattern.match(line) for line in config_path.read_text(encoding="utf-8").splitlines()):
        return
    target = config_path.parent / "cursor-theme.kdl"
    tmp = target.with_suffix(".kdl.tmp")
    tmp.write_text(f'cursor {{\n    xcursor-theme "{theme}"\n}}\n', encoding="utf-8")
    tmp.replace(target)
    print(f"✓ Updated Niri cursor configuration: {theme}")


def apply_xcursor_fallback(theme):
    default_dir = Path.home() / ".icons" / "default"
    default_dir.mkdir(parents=True, exist_ok=True)
    index = default_dir / "index.theme"
    if index.is_file() and "Comment=Default Cursor Theme" not in index.read_text(encoding="utf-8").splitlines():
        print(
            f"Warning: preserving existing {index}; it is not managed by this script",
            file=sys.stderr,
        )
        return
    index.write_text(
        "[Icon Theme]\nName=Default\nComment=Default Cursor Theme\n"
        f"Inherits={theme}\n",
        encoding="utf-8",
    )
    print("✓ Updated ~/.icons/default/index.theme")


def main():
    if len(sys.argv) != 2:
        fail("usage: apply_theme.py <theme-name>  (e.g. Apricot)")
    theme = resolve_theme(sys.argv[1])
    base = find_install(theme)
    size = cursor_size()
    print(f"Applying {theme} from {base / theme}")
    apply_gnome(theme)
    apply_plasma(theme)
    apply_hyprland(theme, size)
    apply_sway(theme, size)
    apply_niri(theme)
    apply_xcursor_fallback(theme)


if __name__ == "__main__":
    main()
