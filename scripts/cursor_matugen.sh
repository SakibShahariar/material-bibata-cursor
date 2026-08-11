#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEMES_JSON="$SCRIPT_DIR/themes.json"
COLOR_MATCH_PY="$SCRIPT_DIR/color_match.py"

INSTALL_DIR="${BIBATA_MATUGEN_INSTALL_DIR:-$HOME/.icons}"

COLORS_FILE="$HOME/.config/colors.json"

MATUGEN_KEY="${MATUGEN_KEY:-.colors.color13}"

# --- Preflight checks --------------------------------------------------
if [[ ! -f "$COLORS_FILE" ]]; then
    echo "Error: matugen color profile missing at $COLORS_FILE" >&2
    exit 1
fi

if [[ ! -f "$THEMES_JSON" ]]; then
    echo "Error: themes.json not found at $THEMES_JSON" >&2
    exit 1
fi

if [[ ! -f "$COLOR_MATCH_PY" ]]; then
    echo "Error: color_match.py not found at $COLOR_MATCH_PY" >&2
    exit 1
fi

if ! command -v jq >/dev/null; then
    echo "Error: jq is required to read $COLORS_FILE reliably." >&2
    exit 1
fi

# --- 1. Extract active wallpaper hex color ------------------------------

hex_input=$(jq -r "$MATUGEN_KEY" "$COLORS_FILE" 2>/dev/null | tr '[:upper:]' '[:lower:]')

if [[ -z "$hex_input" || "$hex_input" == "null" || ! "$hex_input" =~ ^#[0-9a-f]{6}$ ]]; then
    echo "Error: could not extract a valid hex color using key '$MATUGEN_KEY' from $COLORS_FILE" >&2
    echo "Run 'jq . \"$COLORS_FILE\"' to inspect the schema and set MATUGEN_KEY accordingly." >&2
    exit 1
fi

echo "Active wallpaper color: $hex_input"

# --- 2. Match to closest pre-built theme via CIEDE2000 -------------------
match_stderr=$(mktemp)
if ! nearest_theme=$(python3 "$COLOR_MATCH_PY" "$hex_input" "$THEMES_JSON" 2>"$match_stderr"); then
    echo "Error: color_match.py failed:" >&2
    cat "$match_stderr" >&2
    rm -f "$match_stderr"
    exit 1
fi
cat "$match_stderr" >&2
rm -f "$match_stderr"

if [[ -z "$nearest_theme" ]]; then
    echo "Error: no matching theme returned" >&2
    exit 1
fi

THEME_NAME="Bibata-Material-$nearest_theme"

# --- 3. Verify the theme is actually installed before switching ----------
if [[ ! -d "$INSTALL_DIR/$THEME_NAME" ]]; then
    echo "Error: matched theme '$THEME_NAME' but it isn't compiled at $INSTALL_DIR/$THEME_NAME" >&2
    echo "Run compile_matugen_packs.fish first (or check BIBATA_MATUGEN_INSTALL_DIR matches in both scripts)." >&2
    exit 1
fi

# --- 4. Apply the chosen theme --------------------------------------------
if command -v gsettings >/dev/null; then
    gsettings set org.gnome.desktop.interface cursor-theme "$THEME_NAME"
    echo "✓ Switched to: $THEME_NAME (GNOME)"
else
    echo "Warning: gsettings not available, skipped GNOME cursor-theme switch." >&2
fi

# Hyprland doesn't read gsettings for its own cursor rendering — if you're
# on Hyprland, also update hyprcursor via hyprctl so both toolkits agree:
if command -v hyprctl >/dev/null; then
    hyprctl setcursor "$THEME_NAME" 24 >/dev/null 2>&1 \
        && echo "✓ Switched to: $THEME_NAME (Hyprland)" \
        || echo "Warning: hyprctl setcursor failed" >&2
fi
