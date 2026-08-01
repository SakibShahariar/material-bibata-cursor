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
#   bash scripts/package_release.sh [version]
#
# Output: dist/bibata-material-<version>.tar.gz — extract straight into ~/.icons

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="${BIBATA_MATERIAL_INSTALL_DIR:-$HOME/.icons}"
THEMES_JSON="$REPO_ROOT/themes.json"
VERSION="${1:-untagged}"
DIST_DIR="$REPO_ROOT/dist"
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

while IFS= read -r name; do
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

Full source, build instructions, and the wallpaper-aware auto-switcher:
https://github.com/SakibShahariar/bibata-material
EOF

echo ""
echo "Packaged $included theme(s), skipped $missing missing."

mkdir -p "$DIST_DIR"
tar_path="$DIST_DIR/bibata-material-$VERSION.tar.gz"
tar -czf "$tar_path" -C "$DIST_DIR" "bibata-material-$VERSION"
rm -rf "$STAGE_DIR"

echo "Wrote $tar_path"
echo "This is the file to attach to a GitHub Release or upload to GNOME-Look.org."

if [[ $missing -gt 0 ]]; then
    exit 1
fi
