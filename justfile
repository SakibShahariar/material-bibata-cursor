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

# Build a single theme by name, e.g. `just build-one Coral`
build-one theme:
    fish scripts/compile_bibata_material.fish {{theme}}

# Build only the 28 dark themes + Classic (skips the -Light set, faster)
build-dark:
    fish scripts/compile_bibata_material.fish --only-dark

# Build only the 28 -Light themes (skips the dark set, faster)
build-light:
    fish scripts/compile_bibata_material.fish --only-light

# (Re)generate cursors_scalable/ SVG cursors for all installed themes (GNOME 51 / KDE Plasma 6.2+)
svg:
    python3 scripts/generate_svg_cursors.py

# Regenerate SVG cursors for one installed theme, e.g. `just svg-one Coral`
svg-one theme:
    python3 scripts/generate_svg_cursors.py --theme {{theme}}

# Build Windows .cur cursor themes (all 57)
build-win:
    python3 scripts/build_windows.py

# Build a single Windows theme, e.g. `just build-win-one Coral`
build-win-one theme:
    python3 scripts/build_windows.py {{theme}}

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

# Check that required tools (fish, jq, git, python3) are installed
check-deps:
    #!/usr/bin/env bash
    set -euo pipefail
    missing=0
    for cmd in fish jq git python3; do
        if command -v "$cmd" >/dev/null; then
            echo "✓ $cmd"
        else
            echo "✗ $cmd (missing)"
            missing=1
        fi
    done
    if [ "$missing" -eq 1 ]; then
        echo ""
        echo "Install the missing tool(s) above before running 'just build'."
        exit 1
    fi
