#!/usr/bin/env python3
"""Validate generated cursor themes and Linux release archives without a desktop."""
from __future__ import annotations

import argparse
import configparser
import json
import struct
import sys
import tarfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path, PurePosixPath

THEME_PREFIX = "Bibata-Material-"


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_xcursor(theme_dir: Path) -> None:
    require(theme_dir.is_dir(), f"missing Xcursor theme directory: {theme_dir}")
    index = theme_dir / "index.theme"
    require(index.is_file(), f"missing index.theme: {index}")
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(index, encoding="utf-8")
    except (OSError, configparser.Error) as exc:
        raise ValidationError(f"cannot parse {index}: {exc}") from exc
    require(parser.has_section("Icon Theme"), f"{index} has no [Icon Theme] section")
    require(parser.get("Icon Theme", "Name", fallback="").strip(), f"{index} has no Name")
    cursors = theme_dir / "cursors"
    require(cursors.is_dir(), f"missing Xcursor assets directory: {cursors}")
    cursor_files = [path for path in cursors.iterdir() if path.is_file()]
    require(cursor_files, f"no Xcursor assets in {cursors}")
    valid = 0
    for path in cursor_files:
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ValidationError(f"cannot read Xcursor asset {path}: {exc}") from exc
        require(data.startswith(b"Xcur"), f"invalid Xcursor magic in {path}")
        require(len(data) >= 16, f"truncated Xcursor file: {path}")
        valid += 1
    require(valid > 0, f"no valid Xcursor files found in {cursors}")

    manifest = theme_dir / "manifest.hl"
    hypr = theme_dir / "hyprcursors"
    require(manifest.is_file(), f"missing Hyprcursor manifest: {manifest}")
    require(hypr.is_dir(), f"missing Hyprcursor assets directory: {hypr}")
    archives = list(hypr.glob("*.hlc"))
    require(archives, f"no .hlc cursor archives in {hypr}")
    for archive in archives:
        require(zipfile.is_zipfile(archive), f"invalid Hyprcursor archive: {archive}")
        try:
            with zipfile.ZipFile(archive) as zipped:
                require("meta.hl" in zipped.namelist(), f"{archive} has no meta.hl")
                require(len(zipped.namelist()) > 1, f"{archive} contains no cursor frames")
        except (OSError, zipfile.BadZipFile) as exc:
            raise ValidationError(f"cannot inspect Hyprcursor archive {archive}: {exc}") from exc


def validate_scalable(theme_dir: Path) -> None:
    scalable = theme_dir / "cursors_scalable"
    require(scalable.is_dir(), f"missing scalable cursor assets: {scalable}")
    shapes = [path for path in scalable.iterdir() if path.is_dir()]
    require(shapes, f"no scalable cursor shapes in {scalable}")
    checked = 0
    for shape in shapes:
        metadata_path = shape / "metadata.json"
        require(metadata_path.is_file(), f"missing SVG metadata: {metadata_path}")
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError(f"invalid JSON metadata {metadata_path}: {exc}") from exc
        require(isinstance(metadata, list) and metadata, f"empty/invalid frame list: {metadata_path}")
        for frame in metadata:
            require(isinstance(frame, dict), f"invalid frame entry in {metadata_path}")
            filename = frame.get("filename")
            require(isinstance(filename, str) and filename, f"missing frame filename in {metadata_path}")
            relative = PurePosixPath(filename)
            require(not relative.is_absolute() and ".." not in relative.parts,
                    f"unsafe frame path {filename!r} in {metadata_path}")
            svg_path = shape.joinpath(*relative.parts)
            require(svg_path.is_file(), f"missing SVG frame referenced by {metadata_path}: {svg_path}")
            for field in ("hotspot_x", "hotspot_y", "nominal_size"):
                value = frame.get(field)
                require(type(value) is int and value >= 0,
                        f"invalid {field} in {metadata_path}: {value!r}")
            nominal_size = frame["nominal_size"]
            require(nominal_size > 0, f"nominal_size must be positive in {metadata_path}")
            require(frame["hotspot_x"] < nominal_size and frame["hotspot_y"] < nominal_size,
                    f"hotspot is outside nominal canvas in {metadata_path}")
            if "delay" in frame:
                require(type(frame["delay"]) is int and frame["delay"] >= 0,
                        f"invalid frame delay in {metadata_path}")
            try:
                ET.parse(svg_path)
            except (OSError, ET.ParseError) as exc:
                raise ValidationError(f"invalid SVG {svg_path}: {exc}") from exc
            checked += 1
    require(checked > 0, f"no SVG frames validated in {scalable}")


def validate_windows(theme_dir: Path) -> None:
    require(theme_dir.is_dir(), f"missing Windows theme directory: {theme_dir}")
    require((theme_dir / "index.theme").is_file(), f"missing Windows index.theme in {theme_dir}")
    require((theme_dir / "install.inf").is_file(), f"missing install.inf in {theme_dir}")
    curs = list(theme_dir.glob("*.cur"))
    anis = list(theme_dir.glob("*.ani"))
    require(curs, f"no .cur files in {theme_dir}")
    require((theme_dir / "wait.ani").is_file(), f"missing animated wait.ani in {theme_dir}")
    require((theme_dir / "left_ptr_watch.ani").is_file(),
            f"missing animated left_ptr_watch.ani in {theme_dir}")
    for path in curs:
        data = path.read_bytes()
        require(len(data) >= 22 and data[:4] == b"\x00\x00\x02\x00",
                f"invalid/truncated Windows cursor file: {path}")
        count = struct.unpack_from("<H", data, 4)[0]
        require(count > 0 and len(data) >= 6 + count * 16, f"invalid cursor directory: {path}")
        for index in range(count):
            entry_offset = 6 + index * 16
            size, offset = struct.unpack_from("<II", data, entry_offset + 8)
            require(size > 0 and offset >= 6 + count * 16 and offset + size <= len(data),
                    f"invalid image offset/size in {path}")
    for path in anis:
        data = path.read_bytes()
        require(len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"ACON",
                f"invalid ANI RIFF header: {path}")
        require(b"anih" in data and b"rate" in data and b"fram" in data,
                f"ANI file lacks required animation chunks: {path}")


def validate_archive(path: Path) -> None:
    require(path.is_file(), f"archive does not exist: {path}")
    try:
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                raw_names = archive.namelist()
                names = {name.rstrip("/") for name in raw_names}
                require(raw_names, f"empty release archive: {path}")
                roots = {PurePosixPath(name).parts[0] for name in names if PurePosixPath(name).parts}
                require(len(roots) == 1, f"archive must contain one top-level directory: {path}")
                root = next(iter(roots))
                for doc in ("INSTALL.txt", "LICENSE", "README.md", "CREDITS.txt"):
                    require(f"{root}/{doc}" in names, f"{path} missing {root}/{doc}")
                themes = sorted(
                    name for name in names
                    if name.startswith(f"{root}/{THEME_PREFIX}")
                    and len(PurePosixPath(name).parts) == 2
                )
                require(themes, f"{path} contains no packaged theme directories")
                for theme in themes:
                    require(
                        any(name.startswith(theme + "/") and name.endswith(".cur") for name in names),
                        f"{path} contains no .cur files for {theme}",
                    )
                    require(
                        any(name.startswith(theme + "/") and name.endswith(".ani") for name in names),
                        f"{path} contains no .ani files for {theme}",
                    )
                    require(f"{theme}/install.inf" in names, f"{path} missing {theme}/install.inf")
        else:
            with tarfile.open(path, "r:gz") as archive:
                members = archive.getmembers()
                names = {member.name.rstrip("/") for member in members}
                require(members, f"empty release archive: {path}")
                roots = {PurePosixPath(name).parts[0] for name in names if PurePosixPath(name).parts}
                require(len(roots) == 1, f"archive must contain one top-level directory: {path}")
                root = next(iter(roots))
                for doc in ("INSTALL.txt", "LICENSE", "README.md", "CREDITS.txt"):
                    require(f"{root}/{doc}" in names, f"{path} missing {root}/{doc}")
                themes = sorted(
                    name for name in names
                    if name.startswith(f"{root}/{THEME_PREFIX}")
                    and len(PurePosixPath(name).parts) == 2
                )
                require(themes, f"{path} contains no packaged theme directories")
                for theme in themes:
                    for required in ("index.theme", "cursors", "hyprcursors", "cursors_scalable"):
                        prefix = f"{theme}/{required}"
                        require(
                            any(name == prefix or name.startswith(prefix + "/") for name in names),
                            f"{path} missing {prefix}",
                        )
    except (OSError, tarfile.TarError, zipfile.BadZipFile) as exc:
        raise ValidationError(f"cannot inspect release archive {path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--themes-json", type=Path, default=Path(__file__).resolve().parent.parent / "themes.json")
    parser.add_argument("--themes", help="Comma-separated theme names to validate")
    parser.add_argument("--install-dir", type=Path, help="Xcursor/Hyprcursor install root")
    parser.add_argument("--scalable-dir", type=Path, help="Scalable SVG install root")
    parser.add_argument("--windows-dir", type=Path, help="Windows build output root")
    parser.add_argument("--archive", type=Path, action="append", default=[], help="Linux tar.gz archive to smoke-test (repeatable)")
    args = parser.parse_args()

    try:
        if args.install_dir or args.scalable_dir or args.windows_dir:
            require(args.install_dir is not None and args.scalable_dir is not None and args.themes,
                    "--install-dir, --scalable-dir, and --themes must be provided together")
            with args.themes_json.open(encoding="utf-8") as stream:
                themes = json.load(stream)
            names = [name.strip() for name in args.themes.split(",") if name.strip()]
            require(names, "--themes did not contain any names")
            for name in names:
                require(name in themes, f"unknown theme in validator arguments: {name}")
                folder = f"{THEME_PREFIX}{name}"
                validate_xcursor(args.install_dir / folder)
                svg_root = args.install_dir if args.scalable_dir.resolve() == args.install_dir.resolve() else args.scalable_dir
                validate_scalable(svg_root / folder)
                if args.windows_dir:
                    validate_windows(args.windows_dir / folder)
                print(f"Validated generated assets: {folder}")
        for archive in args.archive:
            validate_archive(archive)
            print(f"Validated release archive: {archive}")
        require(args.archive or args.install_dir or args.windows_dir or args.scalable_dir,
                "provide generated asset paths and/or at least one --archive")
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
