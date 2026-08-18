#!/usr/bin/env bash
# Bundles already-compiled Bibata-Material-* themes (from BIBATA_MATERIAL_INSTALL_DIR,
# default ~/.icons) into TWO distributable archives — one for the 28
# dark themes (+ Classic), one for the 28 "-Light" themes — for GitHub
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
# 28 M3 themes) from the dark archive:
#   bash scripts/package_release.sh v1.3.0 --exclude Classic
#
# Output:
#   dist/bibata-material-dark-<version>.tar.gz   — the 28 dark themes (+ Classic unless excluded)
#   dist/bibata-material-light-<version>.tar.gz  — the 28 "-Light" themes
# Both extract straight into ~/.icons.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="${BIBATA_MATERIAL_INSTALL_DIR:-$HOME/.icons}"
THEMES_JSON="$REPO_ROOT/themes.json"
DIST_DIR="$REPO_ROOT/dist"

VERSION="untagged"
EXCLUDE_LIST=""

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

declare -A EXCLUDE_SET
if [[ -n "$EXCLUDE_LIST" ]]; then
    IFS=',' read -ra _excl_arr <<< "$EXCLUDE_LIST"
    for name in "${_excl_arr[@]}"; do
        EXCLUDE_SET["$name"]=1
    done
fi

# Plain-language install instructions, shared by both archives.
write_install_txt() {
    local dir="$1"
    local group_label="$2"
    cat > "$dir/INSTALL.txt" << EOF
Material Bibata Cursor — $group_label — Installation

1. Extract this archive.
2. Copy every "Bibata-Material-*" folder into ~/.icons/
   (create that folder if it doesn't exist).
3. Open GNOME Settings (or GNOME Tweaks) → Mouse & Touchpad, or your
   DE/WM's cursor theme picker, and select one of the themes.

If your cursor theme doesn't show up after copying, log out and back in
— some environments only rescan cursor themes at session start.

Full source and build instructions:
https://github.com/SakibShahariar/material-bibata-cursor
EOF
}

# Packages one group (a bash array of theme names passed by nameref)
# into dist/bibata-material-<group>-<version>.tar.gz
package_group() {
    local group_name="$1"
    local group_label="$2"
    shift 2
    local names=("$@")

    local stage_dir="$DIST_DIR/bibata-material-$group_name-$VERSION"
    rm -rf "$stage_dir"
    mkdir -p "$stage_dir"

    local included=0 missing=0 excluded=0
    for name in "${names[@]}"; do
        if [[ -n "${EXCLUDE_SET[$name]+x}" ]]; then
            echo "Excluding '$name' (--exclude)" >&2
            excluded=$((excluded + 1))
            continue
        fi

        local folder="Bibata-Material-$name"
        local src="$INSTALL_DIR/$folder"

        if [[ ! -d "$src" ]] || [[ ! -f "$src/index.theme" ]]; then
            echo "Skipping '$folder': not found or missing index.theme at $src" >&2
            missing=$((missing + 1))
            continue
        fi

        cp -r "$src" "$stage_dir/$folder"
        included=$((included + 1))
    done

    if [[ $included -eq 0 ]]; then
        echo "Warning: nothing packaged for group '$group_name' — skipping archive" >&2
        rm -rf "$stage_dir"
        echo "0"
        return
    fi

    write_install_txt "$stage_dir" "$group_label"

    mkdir -p "$DIST_DIR"
    local tar_path="$DIST_DIR/bibata-material-$group_name-$VERSION.tar.gz"
    tar -czf "$tar_path" -C "$DIST_DIR" "bibata-material-$group_name-$VERSION"
    rm -rf "$stage_dir"

    echo "Wrote $tar_path ($included theme(s), $excluded excluded, $missing missing)" >&2
    echo "$included"
}

dark_names=()
light_names=()
while IFS= read -r name; do
    if [[ "$name" == *-Light ]]; then
        light_names+=("$name")
    else
        dark_names+=("$name")
    fi
done <<< "$theme_names"

echo "--- Dark archive ---" >&2
dark_count=$(package_group "dark" "Dark" "${dark_names[@]}")

echo "--- Light archive ---" >&2
light_count=$(package_group "light" "Light" "${light_names[@]}")

echo ""
echo "Done: dark=$dark_count theme(s), light=$light_count theme(s)."
echo "These are the files to attach to a GitHub Release or upload to GNOME-Look.org."

if [[ "$dark_count" -eq 0 && "$light_count" -eq 0 ]]; then
    echo "Error: nothing was packaged at all. Run compile_bibata_material.fish first." >&2
    exit 1
fi
