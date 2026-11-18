# Windows cursors

Windows `.cur`/`.ani` cursor files are generated separately using
`scripts/build_windows.py`. This requires Python 3.12 or newer,
`rsvg-convert` (librsvg), and the Python Pillow package. Install the Python
dependency from the Windows-only requirements file:

```bash
python3 -m pip install -r requirements-win.txt
```

The pinned upstream Bibata source is vendored in `scripts/bibata_cursor/`, so
no network clone is needed. Windows archive packaging additionally requires
`zip`.

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

## Windows support matrix

This records what is validated in CI and what still needs a real Windows
session. See [the support matrix](SUPPORT.md) for the project-wide view.

| Area | Status | Evidence / note |
|---|---|---|
| Windows 10 / 11 runtime rendering | **Not validated here** | No Windows session in CI or this dev environment |
| Standard / high-DPI / mixed-DPI layouts | **Not validated here** | `.cur` files include 16–128px sizes; OS picks the size |
| Per-user / all-users `Install.inf` paths | Structure validated | INF generated with `%10%` paths; admin right-click install not run here |
| Animated `Wait` / `AppStarting` (`.ani`) | Assets validated | Frame sequence/delay and transparency checked in CI (`validate_animations.py`) |
| Diagonal resize orientation (`SizeNWSE`/`SizeNESW`) | Mapping validated in source | Report from RC pending (#5) |
| `.cur`/`.ani` build determinism | Validated | Full 57-theme serial vs parallel builds byte-identical |
| Hotspot behavior at fractional scaling | Partially validated | Hotspot drift ≤1px in built assets; manual click testing done on GNOME only (#38) |

**Known limitations:** Windows-only shapes `person` and `pin` have no Linux
`x11_name` and are not part of the Linux parity checks. The animated and
static cursors are generated from the same pinned Bibata SVG sources, but
final on-screen appearance depends on Windows version and DPI settings.

If you validate a Windows configuration, record the Windows version, DPI
configuration, installer path used, and results here and in #69.

## Package a release

See [Packaging for redistribution](PACKAGING.md) for creating distributable
Windows ZIP archives.
