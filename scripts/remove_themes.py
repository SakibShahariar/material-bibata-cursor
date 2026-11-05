#!/usr/bin/env python3
"""Safely remove selected Bibata-Material theme variants from install roots.

By default this is a dry run. Pass --yes to delete the listed theme directories.
Only exact theme names defined in themes.json are accepted.
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def default_scalable_dir(install_dir: Path) -> Path:
    env = os.environ.get("BIBATA_MATERIAL_SCALABLE_DIR")
    if env:
        return Path(env).expanduser()
    try:
        resolved = install_dir.resolve()
    except OSError:
        resolved = install_dir
    xdg_icons = Path(
        os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    ).expanduser() / "icons"
    system_icon_roots = (Path("/usr/share/icons"), Path("/usr/local/share/icons"))
    if any(resolved == root or root in resolved.parents for root in system_icon_roots):
        return install_dir
    return xdg_icons


def remove_path(path: Path) -> None:
    # Never follow a theme-directory symlink; unlink the link itself.
    if path.is_symlink() or not path.is_dir():
        path.unlink()
    else:
        shutil.rmtree(path)


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--themes", required=True,
        help="Comma-separated theme names from themes.json, e.g. Apricot,Coral",
    )
    parser.add_argument(
        "--install-dir",
        default=os.environ.get("BIBATA_MATERIAL_INSTALL_DIR", str(Path.home() / ".icons")),
        help="Root containing Xcursor/Hyprcursor theme directories",
    )
    parser.add_argument(
        "--scalable-dir", default=None,
        help="Root containing scalable SVG themes (defaults like the build script)",
    )
    parser.add_argument("--themes-json", default=str(repo_root / "themes.json"))
    parser.add_argument(
        "--yes", action="store_true",
        help="Actually remove the listed directories (otherwise only show the plan)",
    )
    args = parser.parse_args()

    themes_path = Path(args.themes_json).expanduser()
    try:
        with themes_path.open(encoding="utf-8") as handle:
            theme_data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error: cannot read themes file {themes_path}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(theme_data, dict):
        print("Error: themes.json must contain a JSON object.", file=sys.stderr)
        return 1

    selected = [name.strip() for name in args.themes.split(",")]
    if not selected or any(not name for name in selected):
        print("Error: --themes must contain one or more non-empty names.", file=sys.stderr)
        return 2
    invalid = [name for name in selected if name not in theme_data]
    if invalid:
        print("Error: unknown theme name(s): " + ", ".join(repr(n) for n in invalid), file=sys.stderr)
        return 2
    # Preserve input order while preventing duplicate work.
    selected = list(dict.fromkeys(selected))

    install_dir = Path(args.install_dir).expanduser().resolve()
    scalable_dir = (
        Path(args.scalable_dir).expanduser().resolve()
        if args.scalable_dir else default_scalable_dir(install_dir).resolve()
    )
    roots = list(dict.fromkeys((install_dir, scalable_dir)))
    targets = [
        root / f"Bibata-Material-{theme}"
        for theme in selected
        for root in roots
    ]
    existing = [path for path in targets if path.exists() or path.is_symlink()]

    action = "Would remove" if not args.yes else "Removing"
    for path in targets:
        if path.exists() or path.is_symlink():
            print(f"{action}: {path}")
        else:
            print(f"Not found: {path}")

    if not args.yes:
        print("\nDry run only; pass --yes to remove these directories.")
        return 0

    failed = False
    for path in existing:
        try:
            remove_path(path)
        except OSError as exc:
            failed = True
            print(f"Error: could not remove {path}: {exc}", file=sys.stderr)
    if failed:
        return 1
    print(f"Removed selected theme variant(s): {', '.join(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
