# Material Bibata Cursor — task runner
#
# Wraps the underlying fish/bash/python scripts so you don't need to
# know which script does what, or be comfortable with fish. Run `just`
# with no arguments to see this list.

# List available commands
default:
    @just --list

# Build all 57 themes and install to ~/.icons (or $BIBATA_MATERIAL_INSTALL_DIR)
build:
    fish scripts/compile_bibata_material.fish

# Build a single theme by name, e.g. `just build-one Apricot`
build-one theme:
    fish scripts/compile_bibata_material.fish {{theme}}

# Build a comma-separated subset, e.g. `just build-selected Apricot,Coral,Classic`
build-selected themes:
    fish scripts/compile_bibata_material.fish --themes {{themes}}

# Build only the 28 dark themes + Classic (skips the -Light set, faster)
build-dark:
    fish scripts/compile_bibata_material.fish --only-dark

# Build only the 28 -Light themes (skips the dark set, faster)
build-light:
    fish scripts/compile_bibata_material.fish --only-light

# (Re)generate cursors_scalable/ SVG cursors for all installed themes (GNOME 51 / KDE Plasma 6.2+)
svg:
    python3 scripts/generate_svg_cursors.py

# Regenerate SVG cursors for one installed theme, e.g. `just svg-one Apricot`
svg-one theme:
    python3 scripts/generate_svg_cursors.py --theme {{theme}}

# Build Windows .cur cursor themes (all 57)
build-win:
    python3 scripts/build_windows.py

# Build a single Windows theme, e.g. `just build-win-one Coral`
build-win-one theme:
    python3 scripts/build_windows.py {{theme}}

# Check prerequisites for building and packaging Windows cursor themes
check-win-deps:
    #!/usr/bin/env bash
    set -euo pipefail
    missing=0
    for cmd in python3 rsvg-convert zip; do
        if command -v "$cmd" >/dev/null 2>&1; then
            echo "✓ $cmd"
        else
            echo "✗ $cmd (missing)"
            missing=1
        fi
    done
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
            echo "✓ Python 3.11+"
        else
            echo "✗ Python 3.11+ required (tomllib is part of the standard library)"
            missing=1
        fi
        if python3 -c 'from PIL import Image' >/dev/null 2>&1; then
            echo "✓ Pillow"
        else
            echo "✗ Pillow (install with: python3 -m pip install Pillow)"
            missing=1
        fi
    fi
    if [ ! -f scripts/bibata_cursor/config/build.toml ] || [ ! -d scripts/bibata_cursor/svg ]; then
        echo "✗ upstream Bibata source missing (run 'just build' first)"
        missing=1
    else
        echo "✓ upstream Bibata source"
    fi
    if [ "$missing" -eq 1 ]; then
        echo ""
        echo "Install the missing prerequisites before running 'just build-win'."
        exit 1
    fi

# Remove Windows build artifacts (out_win/)
clean-win:
    rm -rf out_win

# Package already-compiled themes into a release archive, e.g. `just package v1.0.0`
package version:
    bash scripts/package_release.sh {{version}}

# Package Windows .cur themes for release, e.g. `just package-win v1.0.0`
package-win version:
    bash scripts/package_release.sh {{version}} --win

# Package Windows .cur themes for release (dark only), e.g. `just package-win-dark v1.0.0`
package-win-dark version:
    bash scripts/package_release.sh {{version}} --win --only-dark

# Package Windows .cur themes for release (light only), e.g. `just package-win-light v1.0.0`
package-win-light version:
    bash scripts/package_release.sh {{version}} --win --only-light

# List all theme names defined in themes.json
list:
    @jq -r 'keys[]' themes.json

# Show the Body/Primary/Watch colors for one theme, e.g. `just show Coral`
show theme:
    @jq --arg n "{{theme}}" '.[$n] // "not found"' themes.json

# Remove build artifacts: cloned bibata_cursor source, dist/, __pycache__ (leaves ~/.icons untouched)
clean:
    rm -rf scripts/bibata_cursor
    rm -rf dist
    rm -rf scripts/__pycache__

# Check the tools required for the Linux build
check-deps:
    #!/usr/bin/env bash
    set -euo pipefail
    missing=0
    for cmd in fish jq git python3 rsvg-convert xcursorgen; do
        if command -v "$cmd" >/dev/null 2>&1; then
            echo "✓ $cmd"
        else
            echo "✗ $cmd (missing)"
            missing=1
        fi
    done
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
            echo "✓ Python 3.11+"
        else
            echo "✗ Python 3.11+ required (tomllib is part of the standard library)"
            missing=1
        fi
    fi
    if [ "$missing" -eq 1 ]; then
        echo ""
        echo "Install the missing tools above before running 'just build'."
        echo "The upstream Bibata build also requires its documented dependencies:"
        echo "https://github.com/rtgiskard/bibata_cursor"
        exit 1
    fi
