#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEMES_JSON="$SCRIPT_DIR/themes.json"
if [[ ! -f "$THEMES_JSON" ]]; then
    THEMES_JSON="$SCRIPT_DIR/../themes.json"
fi
COLOR_MATCH_PY="$SCRIPT_DIR/color_match.py"

INSTALL_DIR="${BIBATA_MATUGEN_INSTALL_DIR:-$HOME/.icons}"
COLORS_FILE="${BIBATA_MATUGEN_COLORS_FILE:-$HOME/.config/colors.json}"
MATUGEN_KEY="${MATUGEN_KEY:-.colors.color13}"

# --- Preflight checks --------------------------------------------------

if [[ ! -f "$COLORS_FILE" ]]; then
    echo "Error: color profile missing at $COLORS_FILE" >&2
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

# --- 1. Extract active wallpaper hex color -----------------------------

hex_input=""

if command -v jq >/dev/null 2>&1 && jq empty "$COLORS_FILE" 2>/dev/null; then
    hex_input="$(jq -r "$MATUGEN_KEY // ." "$COLORS_FILE" 2>/dev/null \
        | tr '[:upper:]' '[:lower:]')"
fi

# Support files containing only a raw hex color as well.
if [[ -z "$hex_input" || "$hex_input" == "null" ||
      ! "$hex_input" =~ ^#[0-9a-f]{6}$ ]]; then
    hex_input="$(tr -d '[:space:]"' < "$COLORS_FILE" \
        | tr '[:upper:]' '[:lower:]')"
fi

if [[ ! "$hex_input" =~ ^#[0-9a-f]{6}$ ]]; then
    echo "Error: could not extract a valid 6-digit hex color from $COLORS_FILE" >&2
    exit 1
fi

echo "Active wallpaper color: $hex_input"

# --- 2. Match the closest pre-built theme using CIEDE2000 -------------

match_stderr="$(mktemp)"

if ! nearest_theme="$(python3 "$COLOR_MATCH_PY" "$hex_input" "$THEMES_JSON" \
    2>"$match_stderr")"; then
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

# --- 3. Verify that the matched theme is installed ---------------------

FOUND_DIR=""

for candidate_dir in \
    "$INSTALL_DIR" \
    "$HOME/.local/share/icons" \
    "/usr/share/icons"; do
    if [[ -d "$candidate_dir/$THEME_NAME" ]]; then
        FOUND_DIR="$candidate_dir"
        break
    fi
done

if [[ -z "$FOUND_DIR" ]]; then
    echo "Error: matched theme '$THEME_NAME' was not found in:" >&2
    echo "  - $INSTALL_DIR" >&2
    echo "  - $HOME/.local/share/icons" >&2
    echo "  - /usr/share/icons" >&2
    exit 1
fi

INSTALL_DIR="$FOUND_DIR"

echo "Matched cursor theme: $THEME_NAME"
echo "Theme directory: $INSTALL_DIR/$THEME_NAME"

# Preserve the current cursor size where possible. XCURSOR_SIZE is the
# common cross-desktop override; Hyprland's live setting and GNOME's
# configured size are fallbacks. Use 24 only when no valid size is available.
CURSOR_SIZE="${XCURSOR_SIZE:-}"
if ! [[ "$CURSOR_SIZE" =~ ^[1-9][0-9]*$ ]] &&
   command -v hyprctl >/dev/null 2>&1 &&
   pgrep -x Hyprland >/dev/null 2>&1 &&
   command -v jq >/dev/null 2>&1; then
    CURSOR_SIZE="$(hyprctl getoption cursor:size -j 2>/dev/null | jq -r '.int // empty' 2>/dev/null || true)"
fi
if ! [[ "$CURSOR_SIZE" =~ ^[1-9][0-9]*$ ]] &&
   command -v gsettings >/dev/null 2>&1; then
    CURSOR_SIZE="$(gsettings get org.gnome.desktop.interface cursor-size 2>/dev/null | tr -d "'" || true)"
fi
if ! [[ "$CURSOR_SIZE" =~ ^[1-9][0-9]*$ ]]; then
    CURSOR_SIZE=24
fi

# --- 4A. GNOME and GTK applications -----------------------------------

if command -v gsettings >/dev/null 2>&1; then
    if gsettings set org.gnome.desktop.interface cursor-theme "$THEME_NAME" \
        2>/dev/null; then
        echo "✓ Set GNOME cursor theme: $THEME_NAME"
    fi
fi

# --- 4B. KDE Plasma ---------------------------------------------------

# plasma-apply-cursortheme updates the active Plasma cursor theme and is
# preferred over editing kcminputrc directly. Only run it in a Plasma
# session so other desktops with KDE utilities installed are unaffected.
if [[ -n "${KDE_SESSION_VERSION:-}" ]] &&
   command -v plasma-apply-cursortheme >/dev/null 2>&1; then
    if plasma-apply-cursortheme "$THEME_NAME" >/dev/null 2>&1; then
        echo "✓ Set KDE Plasma cursor theme: $THEME_NAME"
    else
        echo "Warning: plasma-apply-cursortheme failed" >&2
    fi
fi

# --- 4C. Hyprland ------------------------------------------------------

if command -v hyprctl >/dev/null 2>&1 &&
   pgrep -x Hyprland >/dev/null 2>&1; then
    if hyprctl setcursor "$THEME_NAME" "$CURSOR_SIZE" >/dev/null 2>&1; then
        echo "✓ Set Hyprland cursor theme: $THEME_NAME"
    else
        echo "Warning: hyprctl setcursor failed" >&2
    fi
fi

# --- 4D. Sway -----------------------------------------------------------
# Sway's seat command supports changing the active XCursor theme and size.
if command -v swaymsg >/dev/null 2>&1 &&
   pgrep -x sway >/dev/null 2>&1; then
    if swaymsg seat '*' xcursor_theme "$THEME_NAME" "$CURSOR_SIZE" >/dev/null 2>&1; then
        echo "✓ Set Sway cursor theme: $THEME_NAME (size $CURSOR_SIZE)"
    else
        echo "Warning: swaymsg failed to set the cursor theme" >&2
    fi
fi

# --- 4E. Niri ----------------------------------------------------------
#
# One-time user setup:
# Add this to the main Niri config:
#
#     include "cursor-theme.kdl"
#
# The generated file lives beside the main config. We only update it
# when that include is present, so Niri users opt in explicitly.

NIRI_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/niri"
NIRI_CONFIG_PATH="${NIRI_CONFIG:-$NIRI_CONFIG_DIR/config.kdl}"

if [[ -f "$NIRI_CONFIG_PATH" ]]; then
    NIRI_CONFIG_DIR="$(dirname "$NIRI_CONFIG_PATH")"
    NIRI_CURSOR_CONFIG="$NIRI_CONFIG_DIR/cursor-theme.kdl"

    # Recognize the documented relative include, optionally with a
    # leading ./ and an optional trailing KDL comment.
    if grep -Eq \
        '^[[:space:]]*include[[:space:]]+"(\./)?cursor-theme\.kdl"[[:space:]]*(//.*)?$' \
        "$NIRI_CONFIG_PATH"; then

        NIRI_CURSOR_TMP="$(mktemp "$NIRI_CURSOR_CONFIG.XXXXXX")"

        if printf 'cursor {\n    xcursor-theme "%s"\n}\n' "$THEME_NAME" \
            > "$NIRI_CURSOR_TMP" &&
           mv -f -- "$NIRI_CURSOR_TMP" "$NIRI_CURSOR_CONFIG"; then
            echo "✓ Updated Niri cursor configuration: $THEME_NAME"
        else
            rm -f -- "$NIRI_CURSOR_TMP"
            echo "Warning: failed to update Niri cursor configuration" >&2
        fi
    fi
fi

# --- 4F. XCursor fallback ----------------------------------------------
#
# Provides the default cursor theme for applications that consult
# the XCursor default-theme file.

mkdir -p "$HOME/.icons/default"
DEFAULT_CURSOR_FILE="$HOME/.icons/default/index.theme"

# Do not silently replace a user's custom XCursor fallback configuration.
# The Comment marker identifies the file managed by this hook.
if [[ -f "$DEFAULT_CURSOR_FILE" ]] &&
   ! grep -Fqx 'Comment=Default Cursor Theme' "$DEFAULT_CURSOR_FILE"; then
    echo "Warning: preserving existing $DEFAULT_CURSOR_FILE; it is not managed by this hook" >&2
else
    DEFAULT_CURSOR_TMP="$(mktemp "$HOME/.icons/default/index.theme.XXXXXX")"

    if cat > "$DEFAULT_CURSOR_TMP" <<EOF
[Icon Theme]
Name=Default
Comment=Default Cursor Theme
Inherits=$THEME_NAME
EOF
    then
        mv -f -- "$DEFAULT_CURSOR_TMP" "$DEFAULT_CURSOR_FILE"
        echo "✓ Updated ~/.icons/default/index.theme"
    else
        rm -f -- "$DEFAULT_CURSOR_TMP"
        echo "Warning: failed to update XCursor fallback configuration" >&2
    fi
fi
