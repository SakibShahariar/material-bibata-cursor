#!/usr/bin/env bash
# Bundles already-compiled Bibata-Material-* themes for Linux and Windows.
#
# Usage:
#   bash scripts/package_release.sh <version> [--exclude Name1,Name2,...]
#   bash scripts/package_release.sh <version> --win [--exclude ...]
#   bash scripts/package_release.sh <version> --win --only-dark
#   bash scripts/package_release.sh <version> --win --only-light
#
# Output:
#   dist/bibata-material-dark-<version>.tar.gz    — the 28 dark themes + Classic
#   dist/bibata-material-light-<version>.tar.gz   — the 28 "-Light" themes
#   dist/bibata-material-dark-<version>-win.zip   — Windows .cur (dark themes + Classic)
#   dist/bibata-material-light-<version>-win.zip  — Windows .cur (light themes)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="${BIBATA_MATERIAL_INSTALL_DIR:-$HOME/.icons}"
THEMES_JSON="$REPO_ROOT/themes.json"
DIST_DIR="$REPO_ROOT/dist"
OUT_WIN="$REPO_ROOT/out_win"

MODE="linux"
ONLY_LIGHT=""
ONLY_DARK=""
VERSION="untagged"
EXCLUDE_LIST=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --win)
            MODE="windows"
            shift
            ;;
        --only-light)
            ONLY_LIGHT=1
            shift
            ;;
        --only-dark)
            ONLY_DARK=1
            shift
            ;;
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
if [[ -n "${EXCLUDE_LIST:-}" ]]; then
    IFS=',' read -ra _excl_arr <<< "$EXCLUDE_LIST"
    for name in "${_excl_arr[@]}"; do
        EXCLUDE_SET["$name"]=1
    done
fi

if [[ "$MODE" == "windows" ]]; then
    package_windows
    exit 0
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

# --- Windows packaging ---

package_windows() {
    if [[ ! -d "$OUT_WIN" ]]; then
        echo "Error: $OUT_WIN not found. Run 'python3 scripts/build_windows.py' first." >&2
        exit 1
    fi

    if ! command -v zip >/dev/null; then
        echo "Error: zip is required for Windows packaging." >&2
        exit 1
    fi

    # Read theme names from out_win directory
    win_names=()
    while IFS= read -r d; do
        win_names+=("$(basename "$d")")
    done < <(find "$OUT_WIN" -maxdepth 1 -mindepth 1 -type d | sort)

    if [[ ${#win_names[@]} -eq 0 ]]; then
        echo "Error: no themes found in $OUT_WIN" >&2
        exit 1
    fi

    dark_win=()
    light_win=()
    for name in "${win_names[@]}"; do
        if [[ "$name" == *-Light ]]; then
            light_win+=("$name")
        else
            dark_win+=("$name")
        fi
    done

    if [[ -n "${ONLY_LIGHT:-}" ]]; then
        pack_win_group "light" "Light" "${light_win[@]}"
    elif [[ -n "${ONLY_DARK:-}" ]]; then
        pack_win_group "dark" "Dark" "${dark_win[@]}"
    else
        pack_win_group "dark" "Dark" "${dark_win[@]}"
        pack_win_group "light" "Light" "${light_win[@]}"
    fi
}

pack_win_group() {
    local group_name="$1"
    local group_label="$2"
    shift 2
    local names=("$@")

    if [[ ${#names[@]} -eq 0 ]]; then
        echo "Warning: no themes for group '$group_name' — skipping" >&2
        return
    fi

    local stage_dir="$DIST_DIR/bibata-material-$group_name-$VERSION-win"
    rm -rf "$stage_dir"
    mkdir -p "$stage_dir"

    local included=0 excluded=0 missing=0
    for name in "${names[@]}"; do
        if [[ -n "${EXCLUDE_SET[$name]+x}" ]]; then
            echo "Excluding '$name' (--exclude)" >&2
            excluded=$((excluded + 1))
            continue
        fi

        local src="$OUT_WIN/$name"
        if [[ ! -d "$src" ]]; then
            echo "Skipping '$name': not found at $src" >&2
            missing=$((missing + 1))
            continue
        fi

        cp -r "$src" "$stage_dir/$name"
        included=$((included + 1))
    done

    if [[ $included -eq 0 ]]; then
        echo "Warning: nothing packaged for '$group_name' — skipping" >&2
        rm -rf "$stage_dir"
        return
    fi

    write_win_install_txt "$stage_dir" "$group_label (Windows .cur)"

    mkdir -p "$DIST_DIR"
    local zip_path="$DIST_DIR/bibata-material-$group_name-$VERSION-win.zip"
    (cd "$DIST_DIR" && zip -rq "bibata-material-$group_name-$VERSION-win.zip" \
        "bibata-material-$group_name-$VERSION-win")
    rm -rf "$stage_dir"

    echo "Wrote $zip_path ($included theme(s))"
}

write_win_install_txt() {
    local dir="$1"
    local group_label="$2"
    cat > "$dir/INSTALL.txt" << EOF
Material Bibata Cursor — $group_label — Installation (Windows)

1. Extract this archive.
2. Copy every "Bibata-Material-*" folder into your icon theme directory:
     %LOCALAPPDATA%\Icons\  (per-user) or
     C:\Windows\Cursors\   (all users, requires admin)
3. Open Windows Settings → Personalization → Colors →
  "Edit your settings" → select the cursor theme.

Full source and build instructions:
https://github.com/SakibShahariar/material-bibata-cursor
EOF
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
