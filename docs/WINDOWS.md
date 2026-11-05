# Windows cursors

Windows `.cur`/`.ani` cursor files are generated separately using
`scripts/build_windows.py`. This requires Python 3.12 or newer,
`rsvg-convert` (librsvg), and the Python Pillow package. Install the Python
dependency from the Windows-only requirements file:

```bash
python3 -m pip install -r requirements-win.txt
```

The upstream Bibata source must also be present in `scripts/bibata_cursor/`;
running the Linux build first clones it automatically. Windows archive
packaging additionally requires `zip`.

```bash
python3 scripts/build_windows.py             # all themes
python3 scripts/build_windows.py --only-dark  # dark themes only
python3 scripts/build_windows.py --only-light # light themes only
```

Each theme gets a folder under `out_win/` containing a `.cur` file
(16, 24, 32, 48, 64, and 128px) for every static cursor, plus animated
`wait.ani` and `left_ptr_watch.ani` files.

## Install on Windows

Open any `Bibata-Material-*` folder, right-click `Install.inf`, and choose
**Install**. It copies the `.cur` and `.ani` files into a per-theme
`C:\Windows\Cursors\<theme>\` subfolder and registers the scheme in the
registry, so multiple themes can be installed side by side. An administrator
prompt is required.

Alternatively, copy the theme folder into `%LOCALAPPDATA%\Icons\` and set
the cursors in **Settings → Devices → Mouse → Additional mouse settings →
Pointers**.

## Windows cursor scheme mapping

The Windows registry mapping is maintained in `WIN_SCHEME` in
[`scripts/build_windows.py`](../scripts/build_windows.py). Change the
X11 cursor name in that table when changing a Windows scheme assignment;
the builder writes the corresponding `Install.inf` entries from generated
`.cur` / `.ani` files. Missing outputs are omitted rather than registered
as broken paths, and animated `.ani` files take precedence over static
`.cur` files.

| Windows scheme value | Material Bibata cursor |
|---|---|
| `Arrow` | `left_ptr` |
| `Help` | `question_arrow` |
| `AppStarting` | `left_ptr_watch` (animated) |
| `Wait` | `wait` (animated) |
| `Crosshair` | `crosshair` |
| `IBeam` | `xterm` |
| `NWPen` | `pencil` |
| `No` | `crossed_circle` |
| `SizeNS` | `sb_v_double_arrow` |
| `SizeWE` | `sb_h_double_arrow` |
| `SizeNWSE` | `bd_double_arrow` |
| `SizeNESW` | `fd_double_arrow` |
| `SizeAll` | `move` |
| `UpArrow` | `sb_up_arrow` |
| `Hand` | `hand2` |

### Windows smoke checklist

After building and installing a theme on Windows, verify:

- [ ] The `SizeNWSE` and `SizeNESW` diagonal resize cursors point in the
      expected opposite diagonal directions; report any swap with the
      Windows version and application.
- [ ] `Wait` uses the animated `wait.ani` cursor.
- [ ] `AppStarting` uses the animated `left_ptr_watch.ani` cursor.
- [ ] The generated `Install.inf` references only files present in the
      installed theme directory.

These are manual runtime checks; the source mapping and generated INF
structure can be inspected on Linux, but Windows orientation and animation
must not be marked verified without a Windows session.

## Package a release

See [Packaging for redistribution](PACKAGING.md) for creating distributable
Windows ZIP archives.
