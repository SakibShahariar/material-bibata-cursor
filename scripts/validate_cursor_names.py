#!/usr/bin/env python3
"""validate_cursor_names.py — checks CSS cursor name resolution and docs sync.

Part 1 (#34): every freedesktop/CSS name in generate_svg_cursors.py must
resolve to the intended Bibata shape — no unexpected left_ptr fallback.
Part 2 (#53): every row in docs/COMPATIBILITY.md must match the computed
resolution (name set, status, and underlying shape).

Run after build_linux.py has cloned the upstream source:
    python scripts/validate_cursor_names.py
"""

import re
import sys
import tomllib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import generate_svg_cursors as gen  # noqa: E402

REPO_ROOT = SCRIPT_DIR.parent
DOCS_MATRIX = REPO_ROOT / "docs" / "COMPATIBILITY.md"
BIBATA_DIR = SCRIPT_DIR / "bibata_cursor"

# Names allowed to resolve to the plain arrow; everything else must have
# dedicated or aliased art.
LEFT_PTR_ALLOWED = {"default", "context-menu"}

ROW_RE = re.compile(
    r"^\|\s*`([a-z0-9-]+)`\s*\|\s*([^|]+?)\s*\|\s*`([a-z0-9_-]+)`\s*\|",
)


def load_index():
    with open(BIBATA_DIR / "config" / "build.toml", "rb") as f:
        cfg = tomllib.load(f)
    index = gen.build_name_index(cfg)
    shape_x11 = {
        key: params.get("x11_name", "")
        for key, params in cfg["cursors"].items()
    }
    shape_symlinks = {
        key: set(params.get("x11_symlinks", []))
        for key, params in cfg["cursors"].items()
    }
    return index, shape_x11, shape_symlinks


def classify(css_name, shape_key, shape_x11, shape_symlinks):
    x11 = shape_x11[shape_key]
    if css_name == x11:
        return "Real art", x11
    if css_name in shape_symlinks[shape_key]:
        return "Alias", x11
    return "Legacy fallback", x11


def parse_docs():
    rows = {}
    for line in DOCS_MATRIX.read_text(encoding="utf-8").splitlines():
        m = ROW_RE.match(line)
        if m:
            rows[m.group(1)] = (m.group(2), m.group(3))
    return rows


def main():
    errors = []
    index, shape_x11, shape_symlinks = load_index()

    # Part 1: resolution checks.
    resolved = {}
    for css in gen.CSS_CURSOR_NAMES:
        shape_key = gen.resolve_css_name(css, index)
        if shape_key is None:
            errors.append(f"{css}: no resolution found")
            continue
        status, x11 = classify(css, shape_key, shape_x11, shape_symlinks)
        resolved[css] = (status, x11)
        if x11 == "left_ptr" and css not in LEFT_PTR_ALLOWED:
            errors.append(
                f"{css}: unexpectedly resolves to left_ptr (via {shape_key})"
            )

    # Part 2: docs sync checks.
    docs = parse_docs()
    missing = set(gen.CSS_CURSOR_NAMES) - set(docs)
    extra = set(docs) - set(gen.CSS_CURSOR_NAMES)
    if missing:
        errors.append(f"docs missing rows for: {sorted(missing)}")
    if extra:
        errors.append(f"docs has unknown rows: {sorted(extra)}")
    for css in gen.CSS_CURSOR_NAMES:
        if css not in docs or css not in resolved:
            continue
        doc_status, doc_shape = docs[css]
        status, x11 = resolved[css]
        if doc_shape != x11:
            errors.append(
                f"{css}: docs says `{doc_shape}` but resolution is `{x11}`"
            )
        if doc_status != status:
            errors.append(
                f"{css}: docs status '{doc_status}' but computed '{status}'"
            )

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {len(resolved)} CSS names validated; docs matrix in sync.")


if __name__ == "__main__":
    main()
