# Vendored Bibata source

This directory contains a pinned copy of the upstream
[Bibata_Cursor](https://github.com/rtgiskard/bibata_cursor) source needed to
build Material Bibata Cursor cursors. It is vendored so builds do not require
a network clone and so the project can fix and extend the source
independently (see #40).

- **Upstream repository:** https://github.com/rtgiskard/bibata_cursor
- **Fork point / pinned commit:** `f4ccfe8abb63fddc7b3ce51a866fd8378395cb3d`
- **Vendored subtrees:** `svg/`, `config/`, `src/` (the self-contained renderer
  `src/cursor_utils.py` uses only the Python standard library)
- **Last synced:** 2026-11-18

The builders patch a **per-theme copy** of these files into a temporary work
directory (for color replacement and deterministic archives); the vendored
originals here are never modified by a build.

## License and attribution

The upstream Bibata artwork and renderer are licensed under
**GPL-3.0-or-later** (see the upstream `readme.adoc` license section and
https://www.gnu.org/licenses/gpl-3.0.html). Material Bibata Cursor's build
scripts and `themes.json` are MIT-licensed; the compiled cursor themes are
derivative of Bibata_Cursor and remain GPL-3.0-or-later. See the repository
root `LICENSE` and the release archive `CREDITS.txt` for the full notice.

To refresh the pin, run `just vendor` (see `scripts/vendor_bibata.py`), review
the diff, and update the fork point above.
