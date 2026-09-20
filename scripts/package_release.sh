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
# Where the scalable SVG cursor trees live (KDE Plasma 6.2+ / GNOME 51+).
# GNOME only scans XDG data dirs for cursors_scalable, never ~/.icons.
if [[ -n "${BIBATA_MATERIAL_SCALABLE_DIR:-}" ]]; then
    SCALABLE_DIR="$BIBATA_MATERIAL_SCALABLE_DIR"
elif [[ "$INSTALL_DIR" == /usr/share/icons || "$INSTALL_DIR" == /usr/local/share/icons ]]; then
    SCALABLE_DIR="$INSTALL_DIR"
else
    SCALABLE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
fi
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

# Plain-language install instructions, shared by both archives.
write_install_txt() {
    local dir="$1"
    local group_label="$2"
    cat > "$dir/INSTALL.txt" << EOF
Material Bibata Cursor — $group_label — Installation

Each "Bibata-Material-*" folder ships two cursor formats:
  - cursors/  (Xcursor bitmaps) — every desktop, and the fallback for
    X11/XWayland apps.
  - cursors_scalable/ (SVG cursors) — rendered by KDE Plasma 6.2+ and
    GNOME 51+ instead of the bitmaps.

On Linux:
1. Copy every "Bibata-Material-*" folder into ~/.icons/
   (create that folder if it doesn't exist).
2. For KDE 6.2+ / GNOME 51+, also copy the SVG cursors into your icon
   data directory (GNOME does NOT scan ~/.icons for those):
     install -d ~/.local/share/icons
     for d in Bibata-Material-*; do
       install -d ~/.local/share/icons/"\$d"
       cp -r "\$d"/cursors_scalable ~/.local/share/icons/"\$d"/
     done
3. Select the theme in GNOME Settings (Mouse & Touchpad), GNOME Tweaks,
   or your DE/WM's cursor theme picker.

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

        # Merge in the scalable SVG cursors when they live in a separate
        # dir (the ~/.local/share/icons case). System-wide installs
        # already have them inside "$src".
        if [[ "$SCALABLE_DIR" != "$INSTALL_DIR" ]]; then
            local scalable_src="$SCALABLE_DIR/$folder/cursors_scalable"
            if [[ -d "$scalable_src" ]]; then
                cp -r "$scalable_src" "$stage_dir/$folder/"
            else
                echo "Warning: no cursors_scalable at $scalable_src" >&2
            fi
        fi
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

if [[ "$MODE" == "windows" ]]; then
    package_windows
    exit 0
fi

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
