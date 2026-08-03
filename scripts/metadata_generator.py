#!/usr/bin/env python3
"""Writes a freedesktop-spec-compliant index.theme for each compiled
Bibata-Material cursor theme, so GNOME Tweaks/Settings recognizes them.

Usage:
    python3 metadata_generator.py                 # all themes
    python3 metadata_generator.py --theme Ice-Blue # single theme
"""

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_INHERITS = "Adwaita"
THEME_PREFIX = "Bibata-Material-"


def _default_themes_json(script_dir: Path) -> str:
    repo_root_candidate = script_dir.parent / "themes.json"
    if repo_root_candidate.is_file():
        return str(repo_root_candidate)
    return str(script_dir / "themes.json")


def display_name(theme_key: str) -> str:
    return "Material Bibata Cursor " + theme_key.replace("-", " ")


def build_index_theme_content(name: str, comment: str, inherits: str) -> str:
    lines = ["[Icon Theme]", f"Name={name}", f"Comment={comment}"]
    if inherits:
        lines.append(f"Inherits={inherits}")
    return "\n".join(lines) + "\n"


def validate_theme_dir(theme_dir: Path) -> list[str]:
    problems = []
    if not theme_dir.is_dir():
        problems.append(f"directory does not exist: {theme_dir}")
        return problems
    cursors_dir = theme_dir / "cursors"
    if not cursors_dir.is_dir():
        problems.append("missing 'cursors/' subdirectory")
    elif not any(cursors_dir.iterdir()):
        problems.append("'cursors/' subdirectory is empty")
    return problems


def write_index_theme(theme_dir, theme_key, comment, inherits, dry_run) -> bool:
    content = build_index_theme_content(display_name(theme_key), comment, inherits)
    target = theme_dir / "index.theme"
    if dry_run:
        print(f"--- would write {target} ---\n{content}", end="")
        return True
    try:
        target.write_text(content, encoding="utf-8", newline="\n")
        return True
    except OSError as e:
        print(f"Failed to write {target}: {e}", file=sys.stderr)
        return False


def main():
    script_dir = Path(__file__).resolve().parent
    default_install_dir = os.environ.get("BIBATA_MATERIAL_INSTALL_DIR", str(Path.home() / ".icons"))

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--install-dir", default=default_install_dir)
    parser.add_argument("--themes-json", default=_default_themes_json(script_dir))
    parser.add_argument("--inherits", default=DEFAULT_INHERITS)
    parser.add_argument("--theme", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    themes_path = Path(args.themes_json)
    if not themes_path.is_file():
        print(f"Error: themes.json not found at {themes_path}", file=sys.stderr)
        sys.exit(1)

    with open(themes_path, "r", encoding="utf-8") as f:
        themes = json.load(f)

    if args.theme:
        if args.theme not in themes:
            print(f"Error: '{args.theme}' not found in {themes_path}", file=sys.stderr)
            sys.exit(1)
        theme_keys = [args.theme]
    else:
        theme_keys = list(themes.keys())

    install_dir = Path(args.install_dir)
    ok_count = fail_count = skip_count = 0

    for key in theme_keys:
        folder_name = f"{THEME_PREFIX}{key}"
        theme_dir = install_dir / folder_name
        problems = validate_theme_dir(theme_dir)
        if problems:
            skip_count += 1
            print(f"Skipping '{folder_name}': {'; '.join(problems)}", file=sys.stderr)
            continue

        comment = "Material Bibata Cursor"
        if write_index_theme(theme_dir, key, comment, args.inherits, args.dry_run):
            ok_count += 1
            if not args.dry_run:
                print(f"Wrote index.theme for {folder_name}")
        else:
            fail_count += 1

    print(f"\nmetadata_generator finished: {ok_count} written, {skip_count} skipped, {fail_count} failed")

    if fail_count > 0:
        sys.exit(1)
    if ok_count == 0:
        print("Nothing was written — did you run compile_bibata_material.fish first?", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
