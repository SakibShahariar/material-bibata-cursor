#!/usr/bin/env python3
"""Stage, validate, and safely replace one compiled Bibata-Material theme."""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command):
    result = subprocess.run(command)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(map(str, command))}")


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

        targets.append((staged_theme, install_dir / name))
        if not same_root:
            targets.append((svg_theme, scalable_dir / name))

        # Each rename is same-filesystem. Keep backups until every target has
        # been promoted, then remove them. Roll back earlier promotions on error.
        for staged, target in targets:
            backup = target.with_name(f".{target.name}.backup-{os.getpid()}")
            if backup.exists() or backup.is_symlink():
                if backup.is_dir() and not backup.is_symlink():
                    shutil.rmtree(backup)
                else:
                    backup.unlink()
            if target.exists() or target.is_symlink():
                target.rename(backup)
                backups.append((target, backup))
            else:
                backups.append((target, None))
            staged.rename(target)
            promoted.append(target)

        for _, backup in backups:
            if backup is not None and (backup.exists() or backup.is_symlink()):
                if backup.is_dir() and not backup.is_symlink():
                    shutil.rmtree(backup)
                else:
                    backup.unlink()
        print(f"Installed {name} with Xcursor and scalable files.")
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
