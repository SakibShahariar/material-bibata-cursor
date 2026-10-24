# Cursor compatibility matrix

This is the definitive lookup for every freedesktop/CSS cursor name GNOME
51+ and KDE Plasma 6.2+ can request, and how Material Bibata resolves it.
It complements the [shape inventory](CURSOR_SHAPES.md) by marking each name
as **real art** (dedicated Bibata SVG) or **alias** (symlink to another
shape's art).

Resolution follows `generate_svg_cursors.py`: an exact match in the theme's
name index (x11_name or x11_symlink) wins; otherwise the legacy X11 name
from Mutter's mapping is used.

## Pointer and selection

| CSS name | Status | Underlying shape | Notes |
|---|---|---|---|
| `default` | Alias | `left_ptr` | Standard arrow |
| `context-menu` | Real art | `context-menu` | Dedicated context-menu arrow |
| `help` | Alias | `question_arrow` | Question-mark arrow |
| `pointer` | Alias | `hand2` | Pointing hand |
| `cell` | Alias | `plus` | Plus-shaped cell selector |
| `crosshair` | Real art | `crosshair` | Precision crosshair |
| `text` | Alias | `xterm` | I-beam text caret |
| `vertical-text` | Real art | `vertical-text` | Vertical text caret |
| `grab` | Alias | `hand1` | Open hand |
| `grabbing` | Real art | `grabbing` | Closed hand |
| `all-scroll` | Alias | `move` | Dedicated move art, not a plain arrow |

## Busy and progress

| CSS name | Status | Underlying shape | Notes |
|---|---|---|---|
| `progress` | Alias | `left_ptr_watch` | Animated: arrow + spinner, 54 frames at 40ms |
| `wait` | Real art | `wait` | Animated spinner, 54 frames at 40ms |

## Drag and drop

| CSS name | Status | Underlying shape | Notes |
|---|---|---|---|
| `alias` | Alias | `dnd-link` | Link on drop |
| `copy` | Real art | `copy` | Copy on drop |
| `move` | Real art | `move` | Move on drop |
| `no-drop` | Alias | `dnd_no_drop` | Drop not allowed |
| `not-allowed` | Alias | `crossed_circle` | Action blocked |
| `dnd-ask` | Real art | `dnd-ask` | Dedicated ask-on-drop art |

## Resize

| CSS name | Status | Underlying shape | Notes |
|---|---|---|---|
| `e-resize` | Alias | `right_side` | Resize east |
| `n-resize` | Alias | `top_side` | Resize north |
| `ne-resize` | Alias | `top_right_corner` | Resize northeast |
| `nw-resize` | Alias | `top_left_corner` | Resize northwest |
| `s-resize` | Alias | `bottom_side` | Resize south |
| `se-resize` | Alias | `bottom_right_corner` | Resize southeast |
| `sw-resize` | Alias | `bottom_left_corner` | Resize southwest |
| `w-resize` | Alias | `left_side` | Resize west |
| `ew-resize` | Alias | `sb_h_double_arrow` | Horizontal resize |
| `ns-resize` | Alias | `sb_v_double_arrow` | Vertical resize |
| `nesw-resize` | Alias | `fd_double_arrow` | Diagonal resize (NE-SW) |
| `nwse-resize` | Alias | `bd_double_arrow` | Diagonal resize (NW-SE) |
| `col-resize` | Alias | `sb_h_double_arrow` | Column resize |
| `row-resize` | Alias | `sb_v_double_arrow` | Row resize |
| `all-resize` | Legacy fallback | `move` | Only name without exact theme art; falls back via `dnd-move` |

## Zoom

| CSS name | Status | Underlying shape | Notes |
|---|---|---|---|
| `zoom-in` | Real art | `zoom-in` | Dedicated zoom-in magnifier |
| `zoom-out` | Real art | `zoom-out` | Dedicated zoom-out magnifier |

## Gaps

- `person` and `pin` are Windows-oriented upstream cursor names with no
  `x11_name`, so they are not generated for Linux. See issue #37 for the
  Linux parity decision.
- `all-resize` is the only CSS name resolved through the legacy fallback
  rather than dedicated or aliased theme art.
- Every other CSS name has either dedicated art or an explicit alias,
  so no name renders as an unintended plain arrow.
