# Cursor shape inventory

This documents every cursor name the scalable SVG generator emits, and how
each resolves to actual cursor art. It is the reference for the
[compatibility matrix](COMPATIBILITY.md) and for identifying art gaps.

## How names resolve

`generate_svg_cursors.py` produces two naming schemes from the same SVG
sources:

- One real directory per X11 shape (e.g. `left_ptr`, `xterm`), used by KDE
  and X11 apps.
- Symlinked directories for freedesktop/CSS names (e.g. `pointer`, `text`,
  `ew-resize`), used by GNOME/Mutter.

For each CSS name, the generator first checks whether the theme defines an
exact match (an `x11_name` or `x11_symlink` in Bibata's build config). If
not, it falls back to the legacy X11 name from Mutter's
`meta_cursor_get_legacy_name()`. This means a CSS name can render different
art than its legacy fallback when the theme provides a dedicated shape — for
example, `cell` uses the plus-shaped `plus` art rather than `crosshair`.

## Pointer and selection

| CSS name | Legacy X11 fallback | Notes |
|---|---|---|
| `default` | `left_ptr` | Standard arrow |
| `context-menu` | `left_ptr` | Same art as default |
| `help` | `question_arrow` | Question-mark arrow |
| `pointer` | `hand` | Pointing hand |
| `cell` | `crosshair` | Plus-shaped cell selector |
| `crosshair` | `cross` | Precision crosshair |
| `text` | `xterm` | I-beam text caret |
| `vertical-text` | `xterm` | Vertical text caret |
| `grab` | `hand2` | Open hand |
| `grabbing` | `hand2` | Closed hand |
| `all-scroll` | `left_ptr` | Scrollable area |

## Busy and progress

| CSS name | Legacy X11 fallback | Notes |
|---|---|---|
| `progress` | `left_ptr_watch` | Animated: arrow + spinner, 54 frames at 40ms |
| `wait` | `watch` | Animated: spinner, 54 frames at 40ms |

Both animated cursors keep their full frame sequences in the scalable SVG
tree, with per-frame delay metadata.

## Drag and drop

| CSS name | Legacy X11 fallback | Notes |
|---|---|---|
| `alias` | `dnd-link` | Link on drop |
| `copy` | `dnd-copy` | Copy on drop |
| `move` | `dnd-move` | Move on drop |
| `no-drop` | `dnd-none` | Drop not allowed |
| `not-allowed` | `crossed_circle` | Action blocked |
| `dnd-ask` | `dnd-copy` | Ask on drop |

## Resize

| CSS name | Legacy X11 fallback | Notes |
|---|---|---|
| `e-resize` | `right_side` | Resize east |
| `n-resize` | `top_side` | Resize north |
| `ne-resize` | `top_right_corner` | Resize northeast |
| `nw-resize` | `top_left_corner` | Resize northwest |
| `s-resize` | `bottom_side` | Resize south |
| `se-resize` | `bottom_right_corner` | Resize southeast |
| `sw-resize` | `bottom_left_corner` | Resize southwest |
| `w-resize` | `left_side` | Resize west |
| `ew-resize` | `h_double_arrow` | Horizontal resize |
| `ns-resize` | `v_double_arrow` | Vertical resize |
| `nesw-resize` | `fd_double_arrow` | Diagonal resize (NE-SW) |
| `nwse-resize` | `bd_double_arrow` | Diagonal resize (NW-SE) |
| `col-resize` | `h_double_arrow` | Column resize |
| `row-resize` | `v_double_arrow` | Row resize |
| `all-resize` | `dnd-move` | Resize in all directions |

## Zoom

| CSS name | Legacy X11 fallback | Notes |
|---|---|---|
| `zoom-in` | `left_ptr` | Zoom in |
| `zoom-out` | `left_ptr` | Zoom out |

## Known gaps

- `person` and `pin` are Windows-oriented upstream cursor names and are not
  part of the freedesktop/CSS set generated for Linux. See issue #37 for the
  Linux parity decision.
- See the [compatibility matrix](COMPATIBILITY.md) for which names have
dedicated art versus aliases; only `all-resize` uses the legacy fallback.
