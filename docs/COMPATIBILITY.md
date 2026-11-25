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
| `all-resize` | Legacy fallback | `grabbing` | Resolves through the theme name index to the grabbing cursor art |

## Zoom

| CSS name | Status | Underlying shape | Notes |
|---|---|---|---|
| `zoom-in` | Real art | `zoom-in` | Dedicated zoom-in magnifier |
| `zoom-out` | Real art | `zoom-out` | Dedicated zoom-out magnifier |

## Wayland cursor-shape-v1

The `wp_cursor_shape_device_v1` protocol uses underscore names. Except for
`dnd_ask` and `all_resize`, each protocol shape has a direct CSS equivalent
already resolved above; compositors convert the protocol name to that CSS
cursor.

| Wayland shape | CSS equivalent | Material Bibata resolution |
|---|---|---|
| `default` | `default` | Alias → `left_ptr` |
| `context_menu` | `context-menu` | Real art → `context-menu` |
| `help` | `help` | Alias → `question_arrow` |
| `pointer` | `pointer` | Alias → `hand2` |
| `progress` | `progress` | Alias → `left_ptr_watch` |
| `wait` | `wait` | Real art → `wait` |
| `cell` | `cell` | Alias → `plus` |
| `crosshair` | `crosshair` | Real art → `crosshair` |
| `text` | `text` | Alias → `xterm` |
| `vertical_text` | `vertical-text` | Real art → `vertical-text` |
| `alias` | `alias` | Alias → `dnd-link` |
| `copy` | `copy` | Real art → `copy` |
| `move` | `move` | Real art → `move` |
| `no_drop` | `no-drop` | Alias → `dnd_no_drop` |
| `not_allowed` | `not-allowed` | Alias → `crossed_circle` |
| `grab` | `grab` | Alias → `hand1` |
| `grabbing` | `grabbing` | Real art → `grabbing` |
| `e_resize` | `e-resize` | Alias → `right_side` |
| `n_resize` | `n-resize` | Alias → `top_side` |
| `ne_resize` | `ne-resize` | Alias → `top_right_corner` |
| `nw_resize` | `nw-resize` | Alias → `top_left_corner` |
| `s_resize` | `s-resize` | Alias → `bottom_side` |
| `se_resize` | `se-resize` | Alias → `bottom_right_corner` |
| `sw_resize` | `sw-resize` | Alias → `bottom_left_corner` |
| `w_resize` | `w-resize` | Alias → `left_side` |
| `ew_resize` | `ew-resize` | Alias → `sb_h_double_arrow` |
| `ns_resize` | `ns-resize` | Alias → `sb_v_double_arrow` |
| `nesw_resize` | `nesw-resize` | Alias → `fd_double_arrow` |
| `nwse_resize` | `nwse-resize` | Alias → `bd_double_arrow` |
| `col_resize` | `col-resize` | Alias → `sb_h_double_arrow` |
| `row_resize` | `row-resize` | Alias → `sb_v_double_arrow` |
| `all_scroll` | `all-scroll` | Alias → `move` |
| `zoom_in` | `zoom-in` | Real art → `zoom-in` |
| `zoom_out` | `zoom-out` | Real art → `zoom-out` |
| `dnd_ask` | `dnd-ask` | Real art → `dnd-ask` |
| `all_resize` | `all-resize` | Legacy fallback → `grabbing` |

## Qt and X11 aliases

Qt does **not** look up enum names like `up_arrow` or `whatsthis` in a cursor
theme. Its XCB backend maps each `Qt::CursorShape` to a standard X11 cursor
name (source:
[`qxcbcursor.cpp`](https://github.com/qt/qtbase/blob/dev/src/plugins/platforms/xcb/qxcbcursor.cpp),
`cursorIdForShape()`). The table below shows the actual X11 names a theme must
provide; every one resolves in Material Bibata.

| Qt cursor shape | X11 name requested | Material Bibata resolution |
|---|---|---|
| `Qt::ArrowCursor` | `left_ptr` | Real art → `left_ptr` |
| `Qt::UpArrowCursor` | `center_ptr` | Real art → `center_ptr` |
| `Qt::CrossCursor` | `crosshair` | Real art → `crosshair` |
| `Qt::WaitCursor` | `watch` | Alias → `wait` |
| `Qt::IBeamCursor` | `xterm` | Real art → `xterm` |
| `Qt::SizeVerCursor` | `sb_v_double_arrow` | Real art → `sb_v_double_arrow` |
| `Qt::SizeHorCursor` | `sb_h_double_arrow` | Real art → `sb_h_double_arrow` |
| `Qt::SizeBDiagCursor` | `top_right_corner` | Real art → `top_right_corner` |
| `Qt::SizeFDiagCursor` | `bottom_right_corner` | Real art → `bottom_right_corner` |
| `Qt::SizeAllCursor` | `fleur` | Alias → `move` |
| `Qt::SplitVCursor` | `sb_v_double_arrow` | Real art → `sb_v_double_arrow` |
| `Qt::SplitHCursor` | `sb_h_double_arrow` | Real art → `sb_h_double_arrow` |
| `Qt::PointingHandCursor` | `hand2` | Real art → `hand2` |
| `Qt::OpenHandCursor` | `hand1` | Real art → `hand1` |
| `Qt::ClosedHandCursor` | `grabbing` | Real art → `grabbing` |
| `Qt::WhatsThisCursor` | `question_arrow` | Real art → `question_arrow` |
| `Qt::BusyCursor` | `watch` | Alias → `wait` |
| `Qt::ForbiddenCursor` | `circle` | Real art → `circle` |

Qt's drag cursors (`Qt::DragCopyCursor`, `DragMoveCursor`, `DragLinkCursor`) use
the freedesktop DND names (`dnd-copy`, `dnd-move`, `dnd-link`) on Wayland and
the X11 fallback on XCB; all three are aliased in the theme
(`dnd-copy`, `grabbing`/`move`, `dnd-link`).

## Gaps

- `person` and `pin` are Windows-oriented upstream cursor names with no
  `x11_name`, so they are not generated for Linux. See issue #37 for the
  Linux parity decision.
- `all-resize` is classified as a legacy fallback by the validator, but its
  current name-index resolution selects `grabbing` art.
- Earlier revisions of this matrix listed Qt enum names (`up_arrow`,
  `split_v`, `split_h`, `whatsthis`) as gaps. That was incorrect: Qt XCB maps
  them to standard X11 names (`center_ptr`, `sb_v_double_arrow`,
  `sb_h_double_arrow`, `question_arrow`), all of which have art in this theme.
  No new art or aliases are needed.
- Every CSS and Wayland cursor-shape-v1 name has either dedicated art or an
  explicit alias, so no name renders as an unintended plain arrow.
