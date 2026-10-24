# Windows cursors

Windows `.cur`/`.ani` cursor files are generated separately using
`scripts/build_windows.py`. This requires Python 3.12 or newer,
`rsvg-convert` (librsvg), and the Python Pillow package. The upstream
Bibata source must also be present in `scripts/bibata_cursor/`; running
the Linux build first clones it automatically. Windows archive packaging
additionally requires `zip`.

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

## Package a release

See [Packaging for redistribution](PACKAGING.md) for creating distributable
Windows ZIP archives.
