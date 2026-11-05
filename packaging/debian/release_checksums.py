#!/usr/bin/env python3
"""Read SHA-256 digests for the Linux archives attached to a GitHub Release."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPOSITORY = "SakibShahariar/material-bibata-cursor"
REQUIRED_ASSETS = (
    "bibata-material-dark-{tag}.tar.gz",
    "bibata-material-light-{tag}.tar.gz",
)
SHA256_RE = re.compile(r"^sha256:([0-9a-f]{64})$")


def release_archive_checksums(tag: str, opener=urlopen) -> dict[str, str]:
    """Return the two Linux archive SHA-256 values advertised by GitHub."""
    url = f"https://api.github.com/repos/{REPOSITORY}/releases/tags/{tag}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "material-bibata-cursor-debian-packager",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with opener(request, timeout=30) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read GitHub release metadata for {tag}: {exc}") from exc

    if payload.get("tag_name") != tag:
        raise ValueError(
            f"GitHub returned release tag {payload.get('tag_name')!r}, expected {tag!r}"
        )

    assets = {
        asset.get("name"): asset.get("digest")
        for asset in payload.get("assets", [])
        if isinstance(asset, dict)
    }
    checksums = {}
    for template in REQUIRED_ASSETS:
        filename = template.format(tag=tag)
        digest = assets.get(filename)
        match = SHA256_RE.fullmatch(digest or "")
        if not match:
            raise ValueError(
                f"release {tag} is missing a valid SHA-256 digest for {filename}"
            )
        checksums[filename] = match.group(1)
    return checksums


def write_checksum_manifest(tag: str, destination: Path, opener=urlopen) -> None:
    checksums = release_archive_checksums(tag, opener=opener)
    destination.write_text(
        "".join(f"{checksums[name]}  {name}\n" for name in sorted(checksums)),
        encoding="utf-8",
    )


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {Path(sys.argv[0]).name} <release-tag> <output-checksum-file>", file=sys.stderr)
        return 2
    try:
        write_checksum_manifest(sys.argv[1], Path(sys.argv[2]))
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
