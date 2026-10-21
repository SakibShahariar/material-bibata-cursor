#!/usr/bin/env python3
"""Build selected Material Bibata cursor themes without Fish or jq.

Examples:
    python3 scripts/build_linux.py
    python3 scripts/build_linux.py Coral
    python3 scripts/build_linux.py --themes Coral,Apricot --jobs 4
    python3 scripts/build_linux.py --only-light --exclude Coral-Light

Python 3.12+ is required. The upstream Bibata source is pinned to a known
revision so fresh builds and existing clones use the same source.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
if sys.version_info < (3, 12):
    print("Error: Python 3.12+ is required by the pinned upstream Bibata source", file=sys.stderr)
    raise SystemExit(1)
import tempfile
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

UPSTREAM_URL = "https://github.com/rtgiskard/bibata_cursor"
UPSTREAM_COMMIT = "f4ccfe8abb63fddc7b3ce51a866fd8378395cb3d"
THEME_PREFIX = "Bibata-Material-"
EXTRA_X11_SIZES = (12, 18, 30, 36, 42, 54, 60, 66)


class BuildError(RuntimeError):
    """A build prerequisite, source, or per-theme operation failed."""


def run(command: list[str], *, cwd: Path | None = None) -> None:
    result = subprocess.run(command, cwd=cwd)
    if result.returncode:
        raise BuildError(
            f"command failed with exit code {result.returncode}: "
            + " ".join(map(str, command))
        )


def load_themes(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as stream:
            themes = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"could not read valid themes JSON at {path}: {exc}") from exc
    if not isinstance(themes, dict) or not themes:
        raise BuildError(f"{path} must contain a non-empty JSON object of themes")
    for name, colors in themes.items():
        if (
            not isinstance(name, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) is None
            or not isinstance(colors, dict)
        ):
            raise BuildError(f"invalid or unsafe theme name/entry in {path}: {name!r}")
        for key in ("body", "primary", "watch"):
            value = colors.get(key)
            if not isinstance(value, str) or re.fullmatch(r"#[0-9A-Fa-f]{6}", value) is None:
                raise BuildError(
                    f"theme {name!r} has a missing or invalid {key!r} color; expected #RRGGBB"
                )
    return themes


def ensure_upstream(build_dir: Path) -> None:
    if not build_dir.exists():
        print(f"Cloning Bibata source into {build_dir}...")
        # Clone away from the final path so an interrupted clone never leaves
        # a partial directory that subsequent runs mistake for a checkout.
        with tempfile.TemporaryDirectory(
            prefix=".bibata_cursor.clone-", dir=build_dir.parent
        ) as temporary_parent:
            clone_path = Path(temporary_parent) / "checkout"
            run(["git", "clone", UPSTREAM_URL, str(clone_path)])
            clone_path.rename(build_dir)
    elif not (build_dir / ".git").is_dir() or not (build_dir / "src" / "cursor_utils.py").is_file():
        raise BuildError(
            f"{build_dir} exists but is not a complete Bibata checkout. "
            "Move it aside or remove it, then rerun the build."
        )

    # Existing clones must use the same pinned revision as fresh clones.
    run(["git", "-C", str(build_dir), "fetch", "--quiet", "origin", UPSTREAM_COMMIT])
    run(["git", "-C", str(build_dir), "checkout", "--quiet", "--detach", UPSTREAM_COMMIT])


def patch_theme_config(work_dir: Path, theme: str, colors: dict) -> None:
    render_path = work_dir / "config" / "render.json"
    try:
        with render_path.open(encoding="utf-8") as stream:
            render = json.load(stream)
        source_theme = render["Bibata-Modern-Classic"]
        color_entries = source_theme["colors"]
        if len(color_entries) < 3:
            raise ValueError("upstream render config has fewer than three color entries")
        for entry, key in zip(color_entries[:3], ("body", "primary", "watch")):
            entry["replace"] = colors[key]
        with render_path.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(render, stream, indent=2)
            stream.write("\n")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise BuildError(f"could not patch render.json for {theme}: {exc}") from exc

    config_path = work_dir / "config" / "build.toml"
    try:
        with config_path.open("rb") as stream:
            config = tomllib.load(stream)
        sizes = config.get("cursor_defaults", {}).get("x11_sizes")
        if (
            not isinstance(sizes, list)
            or not sizes
            or any(type(size) is not int or size <= 0 for size in sizes)
        ):
            raise ValueError("cursor_defaults.x11_sizes is missing or invalid")
        merged_sizes = sorted(set(sizes).union(EXTRA_X11_SIZES))
        text = config_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        section = None
        size_assignments = []
        for line_number, line in enumerate(lines):
            stripped = line.strip()
            section_match = re.fullmatch(r"\\[([^\\]]+)\\](?:\\s*#.*)?", stripped)
            if section_match:
                section = section_match.group(1).strip()
            elif section == "cursor_defaults" and re.match(r"^[ \\t]*x11_sizes[ \\t]*=", line):
                size_assignments.append(line_number)
        if len(size_assignments) != 1:
            raise ValueError(
                "expected exactly one cursor_defaults.x11_sizes assignment; "
                f"found {len(size_assignments)}"
            )
        line_number = size_assignments[0]
        indent = lines[line_number][:len(lines[line_number]) - len(lines[line_number].lstrip())]
        lines[line_number] = indent + "x11_sizes = [" + ", ".join(map(str, merged_sizes)) + "]"
        patched_text = "\\n".join(lines) + ("\\n" if text.endswith("\\n") else "")
        # Parse the patched TOML too; malformed config must fail before any
        # cursor output is generated.
        tomllib.loads(patched_text)
        config_path.write_text(patched_text, encoding="utf-8", newline="\\n")
    except (OSError, tomllib.TOMLDecodeError, ValueError, TypeError) as exc:
        raise BuildError(f"could not patch build.toml for {theme}: {exc}") from exc


def default_scalable_dir(install_dir: Path) -> Path:
    configured = os.environ.get("BIBATA_MATERIAL_SCALABLE_DIR")
    if configured:
        return Path(configured).expanduser()
    try:
        resolved = install_dir.expanduser().resolve()
    except OSError:
        resolved = install_dir.expanduser()
    xdg_icons = Path(
        os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    ).expanduser() / "icons"
    system_roots = (Path("/usr/share/icons"), Path("/usr/local/share/icons"))
    if any(resolved == root or root in resolved.parents for root in system_roots):
        return install_dir.expanduser()
    return xdg_icons


def build_one(
    theme: str,
    colors: dict,
    *,
    script_dir: Path,
    build_dir: Path,
    install_dir: Path,
    scalable_dir: Path,
    themes_json: Path,
) -> tuple[str, bool, str]:
    """Build one theme in an isolated work directory, then safely install it."""
    theme_name = f"{THEME_PREFIX}{theme}"
    try:
        with tempfile.TemporaryDirectory(prefix=f"run-{theme}-", dir=build_dir) as temp:
            work_dir = Path(temp)
            for directory in ("src", "svg", "config"):
                source = build_dir / directory
                if not source.is_dir():
                    raise BuildError(f"upstream source directory is missing: {source}")
                shutil.copytree(source, work_dir / directory)
            patch_theme_config(work_dir, theme, colors)
            output_dir = work_dir / "out"
            run(
                [
                    str(work_dir / "src" / "cursor_utils.py"),
                    "--x11",
                    "--hypr",
                    "--theme",
                    "Bibata-Modern-Classic",
                    "--out-dir",
                    str(output_dir),
                ],
                cwd=work_dir,
            )
            compiled_theme = output_dir / "Bibata-Modern-Classic"
            if not compiled_theme.is_dir():
                raise BuildError(f"upstream build did not produce {compiled_theme}")
            run(
                [
                    sys.executable,
                    str(script_dir / "install_staged_theme.py"),
                    "--source",
                    str(compiled_theme),
                    "--theme",
                    theme,
                    "--install-dir",
                    str(install_dir),
                    "--scalable-dir",
                    str(scalable_dir),
                    "--themes-json",
                    str(themes_json),
                    "--script-dir",
                    str(script_dir),
                ]
            )
        return theme, True, f"Installed {theme_name}"
    except Exception as exc:
        return theme, False, f"Failed {theme_name}: {exc}"


def select_themes(parser: argparse.ArgumentParser, args: argparse.Namespace, themes: dict) -> list[str]:
    if args.only_light and args.only_dark:
        parser.error("--only-light and --only-dark cannot be used together")
    if args.themes is not None and args.theme is not None:
        parser.error("use either a positional theme name or --themes, not both")

    if args.themes is not None:
        selected = args.themes.split(",")
        if any(not name.strip() for name in selected):
            parser.error("--themes requires non-empty comma-separated names")
        selected = [name.strip() for name in selected]
    elif args.theme is not None:
        selected = [args.theme]
    else:
        selected = list(themes)

    if len(set(selected)) != len(selected):
        parser.error("duplicate theme names are not allowed")
    for name in selected:
        if name not in themes:
            parser.error(f"unknown theme {name!r}; see themes.json for valid names")

    if args.only_light:
        selected = [name for name in selected if name.endswith("-Light")]
    elif args.only_dark:
        selected = [name for name in selected if not name.endswith("-Light")]
    excluded = set()
    if args.exclude:
        excluded = {name.strip() for name in args.exclude.split(",")}
        if "" in excluded:
            parser.error("--exclude requires non-empty comma-separated names")
        unknown = excluded.difference(themes)
        if unknown:
            parser.error("unknown theme(s) in --exclude: " + ", ".join(sorted(unknown)))
        selected = [name for name in selected if name not in excluded]
    if not selected:
        parser.error("no themes selected after applying filters")
    return selected


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("theme", nargs="?", help="Build one theme by name")
    parser.add_argument("--themes", help="Comma-separated theme names to build")
    parser.add_argument("--exclude", help="Comma-separated theme names to skip")
    parser.add_argument("--only-light", action="store_true", help="Build only -Light themes")
    parser.add_argument("--only-dark", action="store_true", help="Build only dark themes (and Classic)")
    parser.add_argument("--jobs", type=int, default=1, help="Number of themes to build concurrently (default: 1)")
    parser.add_argument(
        "--install-dir",
        type=Path,
        default=Path(os.environ.get("BIBATA_MATERIAL_INSTALL_DIR", str(Path.home() / ".icons"))),
        help="Xcursor installation directory (default: ~/.icons or BIBATA_MATERIAL_INSTALL_DIR)",
    )
    parser.add_argument(
        "--scalable-dir",
        type=Path,
        default=None,
        help="Scalable SVG installation directory (default: XDG icons dir, or install dir for system installs)",
    )
    parser.add_argument(
        "--themes-json", type=Path, default=repo_root / "themes.json",
        help="Path to themes.json",
    )
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error("Python 3.12+ is required (the build uses the standard-library tomllib module)")
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    themes_json = args.themes_json.expanduser().resolve()
    try:
        themes = load_themes(themes_json)
        selected = select_themes(parser, args, themes)
        build_dir = script_dir / "bibata_cursor"
        ensure_upstream(build_dir)
    except (BuildError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    install_dir = args.install_dir.expanduser().resolve()
    scalable_dir = (
        args.scalable_dir.expanduser().resolve()
        if args.scalable_dir
        else default_scalable_dir(install_dir).resolve()
    )
    print(f"Building {len(selected)} theme(s) with {args.jobs} worker(s)...")
    failures = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {
            executor.submit(
                build_one,
                name,
                themes[name],
                script_dir=script_dir,
                build_dir=build_dir,
                install_dir=install_dir,
                scalable_dir=scalable_dir,
                themes_json=themes_json,
            ): name
            for name in selected
        }
        for future in as_completed(futures):
            name, success, message = future.result()
            print(message, file=sys.stdout if success else sys.stderr)
            failures += not success

    print(f"\nFinished: {len(selected) - failures} succeeded, {failures} failed.")
    print(f"Xcursor themes installed to: {install_dir}")
    print(f"Scalable SVG themes installed to: {scalable_dir}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
