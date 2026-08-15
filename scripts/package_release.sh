#!/usr/bin/env bash
# Bundles already-compiled Bibata-Material-* themes (from BIBATA_MATERIAL_INSTALL_DIR,
# default ~/.icons) into a single distributable archive for GitHub
# Releases or GNOME-Look.org.
#
# This does NOT compile anything — run compile_bibata_material.fish first.
# Compiled binaries are deliberately kept out of the git repo itself
# (see .gitignore); this script is the packaging step for distribution
# channels that need actual files, not a build script.
#
# Usage:
#   bash scripts/package_release.sh <version> [--exclude Name1,Name2,...]
#
# Example: exclude Classic (the vanilla Bibata colors, not one of the
# 28 M3 themes) from an official release:
#   bash scripts/package_release.sh v1.1.0 --exclude Classic
#
# Output: dist/bibata-material-<version>.tar.gz — extract straight into ~/.icons

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="${BIBATA_MATERIAL_INSTALL_DIR:-$HOME/.icons}"
THEMES_JSON="$REPO_ROOT/themes.json"
DIST_DIR="$REPO_ROOT/dist"

VERSION="untagged"
EXCLUDE_LIST=""

# Simple manual arg parsing: first non-flag arg is the version,
# --exclude takes a comma-separated list.
while [[ $# -gt 0 ]]; do
    case "$1" in
        --exclude)
            EXCLUDE_LIST="$2"
            shift 2
            ;;
        *)
            VERSION="$1"
            shift
            ;;
    esac
done

STAGE_DIR="$DIST_DIR/bibata-material-$VERSION"

if [[ ! -f "$THEMES_JSON" ]]; then
    echo "Error: themes.json not found at $THEMES_JSON" >&2
    exit 1
fi

if ! command -v jq >/dev/null; then
    echo "Error: jq is required." >&2
    exit 1
fi

theme_names=$(jq -r 'keys[]' "$THEMES_JSON")
if [[ -z "$theme_names" ]]; then
    echo "Error: themes.json contains no themes" >&2
    exit 1
fi

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

missing=0
included=0
excluded=0

# Build a lookup set from the comma-separated exclude list
declare -A EXCLUDE_SET
if [[ -n "$EXCLUDE_LIST" ]]; then
    IFS=',' read -ra _excl_arr <<< "$EXCLUDE_LIST"
    for name in "${_excl_arr[@]}"; do
        EXCLUDE_SET["$name"]=1
    done
fi

while IFS= read -r name; do
    if [[ -n "${EXCLUDE_SET[$name]+x}" ]]; then
        echo "Excluding '$name' (--exclude)" >&2
        excluded=$((excluded + 1))
        continue
    fi

    folder="Bibata-Material-$name"
    src="$INSTALL_DIR/$folder"

    if [[ ! -d "$src" ]] || [[ ! -f "$src/index.theme" ]]; then
        echo "Skipping '$folder': not found or missing index.theme at $src" >&2
        missing=$((missing + 1))
        continue
    fi

    cp -r "$src" "$STAGE_DIR/$folder"
    included=$((included + 1))
done <<< "$theme_names"

if [[ $included -eq 0 ]]; then
    echo "Error: nothing to package — no compiled themes found in $INSTALL_DIR" >&2
    echo "Run compile_bibata_material.fish first." >&2
    rm -rf "$STAGE_DIR"
    exit 1
fi

# Plain-language install instructions for end users downloading from
# GitHub Releases / GNOME-Look.org, who never see the dev README.
cat > "$STAGE_DIR/INSTALL.txt" << 'EOF'
Material Bibata Cursor — Installation

1. Extract this archive.
2. Copy every "Bibata-Material-*" folder into ~/.icons/
   (create that folder if it doesn't exist).
3. Open GNOME Settings (or GNOME Tweaks) → Mouse & Touchpad, or your
   DE/WM's cursor theme picker, and select one of the "Material Bibata Cursor ..."
   themes.

If your cursor theme doesn't show up after copying, log out and back in
— some environments only rescan cursor themes at session start.

Full source and build instructions:
https://github.com/SakibShahariar/material-bibata-cursor
EOF

echo ""
echo "Packaged $included theme(s), excluded $excluded, skipped $missing missing."

mkdir -p "$DIST_DIR"
tar_path="$DIST_DIR/bibata-material-$VERSION.tar.gz"
tar -czf "$tar_path" -C "$DIST_DIR" "bibata-material-$VERSION"
rm -rf "$STAGE_DIR"

echo "Wrote $tar_path"
echo "This is the file to attach to a GitHub Release or upload to GNOME-Look.org."

if [[ $missing -gt 0 ]]; then
    exit 1
fi
