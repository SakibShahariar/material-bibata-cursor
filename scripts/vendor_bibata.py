#!/usr/bin/env python3
"""Vendor the pinned upstream Bibata source tree into this repository (#40).

Clones rtgiskard/bibata_cursor at the requested ref, copies the SVG
sources and build configuration into scripts/bibata_cursor/, and records
the fork point in scripts/bibata_cursor/VENDORED.md.

After running this once and committing the result, Linux, Windows, and
scalable-SVG builds no longer need to clone upstream.

Usage:
    python3 scripts/vendor_bibata.py
    python3 scripts/vendor_bibata.py --upstream-commit <sha>
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENDOR_DIR = REPO_ROOT / "scripts" / "bibata_cursor"
UPSTREAM_URL = "https://github.com/rtgiskard/bibata_cursor.git"
UPSTREAM_REF = "main"
COPY_ENTRIES = ("svg", "config")


def run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--upstream-commit",
        default=UPSTREAM_REF,
        help="Upstream commit, tag, or branch to vendor (default: main)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing vendored tree",
    )
    args = parser.parse_args()

    if VENDOR_DIR.exists():
        if not args.force:
            print(f"error: {VENDOR_DIR} already exists; use --force to replace it", file=sys.stderr)
            return 1
        shutil.rmtree(VENDOR_DIR)

    tmp = Path(__file__).resolve().parent / ".bibata_vendor_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)

    print(f"Cloning {UPSTREAM_URL} at {args.upstream_commit}...")
    run(["git", "clone", UPSTREAM_URL, str(tmp)])
    run(["git", "-C", str(tmp), "checkout", args.upstream_commit])
    commit = subprocess.run(
        ["git", "-C", str(tmp), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    VENDOR_DIR.mkdir(parents=True)
    for entry in COPY_ENTRIES:
        src = tmp / entry
        if not src.is_dir():
            print(f"error: upstream is missing required directory: {entry}", file=sys.stderr)
            return 1
        shutil.copytree(src, VENDOR_DIR / entry)

    license_src = tmp / "LICENSE"
    if license_src.is_file():
        shutil.copy2(license_src, VENDOR_DIR / "UPSTREAM_LICENSE")

    date = dt.datetime.now(dt.timezone.utc).date().isoformat()
    (VENDOR_DIR / "VENDORED.md").write_text(
        "# Vendored Bibata sources\n\n"
        "This directory contains a pinned copy of the Bibata cursor SVG\n"
        "sources and build configuration used by the Material Bibata build.\n\n"
        f"- Upstream: {UPSTREAM_URL}\n"
        f"- Fork point: `{commit}`\n"
        f"- Vendored on: {date}\n"
        "- License: see `UPSTREAM_LICENSE`; compiled themes remain derivative\n"
        "  of Bibata_Cursor and are distributed under its GPLv3-or-later terms.\n"
        "- Refresh with: `python3 scripts/vendor_bibata.py --force --upstream-commit <ref>`\n",
        encoding="utf-8",
    )

    shutil.rmtree(tmp)
    print(f"Vendored upstream commit {commit} into {VENDOR_DIR}")
    print("Commit the resulting scripts/bibata_cursor/ tree to make builds offline-capable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
