#!/usr/bin/env python3
"""Stage, validate, and safely replace one compiled Bibata-Material theme."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def run(command):
    result = subprocess.run(command)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(map(str, command))}")



def validate_compiled_theme(theme_dir: Path, scalable_theme: Path) -> None:
    """Reject incomplete Xcursor, Hyprcursor, or scalable output before promotion."""
    required_shapes = ("left_ptr", "xterm", "wait", "bottom_right_corner")
    cursors_dir = theme_dir / "cursors"
    for shape in required_shapes:
        cursor = cursors_dir / shape
        if not cursor.is_file():
            raise RuntimeError(f"compiled Xcursor shape is missing: {cursor}")
        if not cursor.read_bytes().startswith(b"Xcur"):
            raise RuntimeError(f"compiled Xcursor file has an invalid header: {cursor}")

    manifest = theme_dir / "manifest.hl"
    hypr_dir = theme_dir / "hyprcursors"
    if not manifest.is_file():
        raise RuntimeError(f"compiled Hyprcursor manifest is missing: {manifest}")
    for shape in required_shapes:
        archive = hypr_dir / f"{shape}.hlc"
        if not archive.is_file() or not zipfile.is_zipfile(archive):
            raise RuntimeError(f"compiled Hyprcursor archive is missing or invalid: {archive}")
        try:
            with zipfile.ZipFile(archive) as zipped:
                entries = zipped.namelist()
                if "meta.hl" not in entries or len(entries) < 2:
                    raise RuntimeError(f"compiled Hyprcursor archive is incomplete: {archive}")
        except zipfile.BadZipFile as exc:
            raise RuntimeError(f"compiled Hyprcursor archive is invalid: {archive}") from exc

    scalable_dir = scalable_theme / "cursors_scalable"
    for shape in required_shapes:
        shape_dir = scalable_dir / shape
        metadata_path = shape_dir / "metadata.json"
        if not shape_dir.is_dir() or not metadata_path.is_file():
            raise RuntimeError(f"compiled scalable cursor shape is missing: {shape_dir}")
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"invalid scalable cursor metadata {metadata_path}: {exc}") from exc
        if not isinstance(metadata, list) or not metadata:
            raise RuntimeError(f"scalable cursor metadata has no frames: {metadata_path}")
        for frame in metadata:
            if not isinstance(frame, dict) or not isinstance(frame.get("filename"), str):
                raise RuntimeError(f"invalid frame entry in {metadata_path}")
            filename = Path(frame["filename"])
            if filename.is_absolute() or ".." in filename.parts:
                raise RuntimeError(f"unsafe SVG frame path in {metadata_path}: {filename}")
            svg_path = shape_dir / filename
            if not svg_path.is_file():
                raise RuntimeError(f"SVG frame referenced by {metadata_path} is missing: {svg_path}")
            try:
                ET.parse(svg_path)
            except (OSError, ET.ParseError) as exc:
                raise RuntimeError(f"invalid SVG frame {svg_path}: {exc}") from exc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--theme", required=True)
    parser.add_argument("--install-dir", required=True, type=Path)
    parser.add_argument("--scalable-dir", required=True, type=Path)
    parser.add_argument("--themes-json", required=True, type=Path)
    parser.add_argument("--script-dir", required=True, type=Path)
    args = parser.parse_args()

    name = f"Bibata-Material-{args.theme}"
    install_dir = args.install_dir.expanduser().resolve()
    scalable_dir = args.scalable_dir.expanduser().resolve()
    install_dir.mkdir(parents=True, exist_ok=True)
    scalable_dir.mkdir(parents=True, exist_ok=True)
    same_root = install_dir == scalable_dir
    stage_roots = []
    targets = []
    backups = []
    promoted = []

    try:
        install_stage_root = Path(tempfile.mkdtemp(prefix=f".{name}.stage-", dir=install_dir))
        stage_roots.append(install_stage_root)
        staged_install = install_stage_root if same_root else install_stage_root / "icons"
        staged_install.mkdir(parents=True, exist_ok=True)
        staged_theme = staged_install / name
        shutil.move(str(args.source), str(staged_theme))

        if same_root:
            staged_scalable = staged_install
        else:
            scalable_stage_root = Path(tempfile.mkdtemp(prefix=f".{name}.stage-", dir=scalable_dir))
            stage_roots.append(scalable_stage_root)
            staged_scalable = scalable_stage_root
            staged_scalable.mkdir(parents=True, exist_ok=True)

        run([sys.executable, str(args.script_dir / "metadata_generator.py"),
             "--install-dir", str(staged_install), "--themes-json", str(args.themes_json),
             "--theme", args.theme])
        svg_cmd = [sys.executable, str(args.script_dir / "generate_svg_cursors.py"),
                   "--theme", args.theme, "--install-dir", str(staged_install),
                   "--scalable-dir", str(staged_scalable), "--fallback-install-dir", str(install_dir),
                   "--themes-json", str(args.themes_json)]
        run(svg_cmd)

        if not (staged_theme / "cursors").is_dir() or not any((staged_theme / "cursors").iterdir()):
            raise RuntimeError("staged Xcursor theme has no cursors")
        if not (staged_theme / "index.theme").is_file():
            raise RuntimeError("staged Xcursor theme has no index.theme")
        svg_theme = staged_scalable / name
        if not (svg_theme / "cursors_scalable").is_dir() or not any((svg_theme / "cursors_scalable").iterdir()):
            raise RuntimeError("staged scalable theme has no SVG cursors")
        validate_compiled_theme(staged_theme, svg_theme)

        targets.append((staged_theme, install_dir / name))
        if not same_root:
            targets.append((svg_theme, scalable_dir / name))

        # Each rename is same-filesystem. Keep backups until every target has
        # been promoted, then remove them. Roll back earlier promotions on error.
        for staged, target in targets:
            # Never delete a pre-existing backup from an interrupted earlier
            # install. Choose a fresh name so recovery data remains intact.
            backup = target.with_name(f".{target.name}.backup-{os.getpid()}")
            suffix = 1
            while backup.exists() or backup.is_symlink():
                backup = target.with_name(
                    f".{target.name}.backup-{os.getpid()}-{suffix}"
                )
                suffix += 1
            if target.exists() or target.is_symlink():
                target.rename(backup)
                backups.append((target, backup))
            else:
                backups.append((target, None))
            staged.rename(target)
            promoted.append(target)

        print(f"Installed {name} with Xcursor and scalable files.")
        # Promotion is complete. Backup cleanup is best-effort: a cleanup
        # error must never trigger rollback after another backup was deleted.
        for _, backup in backups:
            if backup is None or not (backup.exists() or backup.is_symlink()):
                continue
            try:
                if backup.is_dir() and not backup.is_symlink():
                    shutil.rmtree(backup)
                else:
                    backup.unlink()
            except OSError as cleanup_error:
                print(f"Warning: could not remove old theme backup {backup}: {cleanup_error}",
                      file=sys.stderr)
    except Exception as exc:
        for target in reversed(promoted):
            if target.exists() or target.is_symlink():
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                else:
                    target.unlink()
        for target, backup in reversed(backups):
            if backup is not None and (backup.exists() or backup.is_symlink()):
                backup.rename(target)
        print(f"Safe install failed for {name}: {exc}", file=sys.stderr)
        return 1
    finally:
        for root in stage_roots:
            if root.exists():
                shutil.rmtree(root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
