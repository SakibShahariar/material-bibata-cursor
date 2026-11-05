#!/usr/bin/env bash
# Build a Debian package from checksummed Linux release archives.
set -euo pipefail
usage() { echo "Usage: $0 <version> [--archive-tag TAG] [--archives-dir DIR] [--output-dir DIR]" >&2; exit 2; }
[[ $# -ge 1 ]] || usage
version="${1#v}"; archive_tag="v$version"; shift
[[ "$version" =~ ^[0-9][A-Za-z0-9.+:~_-]*$ ]] || { echo "Invalid package version: $version" >&2; exit 2; }
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
archives_dir=""; output_dir="$repo_root/dist"; expected_themes=57
while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive-tag) [[ $# -ge 2 ]] || usage; archive_tag="$2"; shift 2 ;;
    --archives-dir) [[ $# -ge 2 ]] || usage; archives_dir="$2"; shift 2 ;;
    --output-dir) [[ $# -ge 2 ]] || usage; output_dir="$2"; shift 2 ;;
    --expected-themes) [[ $# -ge 2 ]] || usage; expected_themes="$2"; shift 2 ;;
    *) usage ;;
  esac
done
[[ "$archive_tag" =~ ^[A-Za-z0-9.+_-]+$ ]] || { echo "Invalid archive tag: $archive_tag" >&2; exit 2; }
for command in dpkg-deb dpkg sha256sum tar; do command -v "$command" >/dev/null || { echo "Missing required command: $command" >&2; exit 1; }; done
dpkg --validate-pkgname material-bibata-cursor
dpkg --validate-version "$version"
work_dir="$(mktemp -d)"; trap 'rm -rf "$work_dir"' EXIT
if [[ -z "$archives_dir" ]]; then
  command -v curl >/dev/null || { echo "curl is required to download release assets" >&2; exit 1; }
  archives_dir="$work_dir/downloads"; mkdir -p "$archives_dir"
  base_url="https://github.com/SakibShahariar/material-bibata-cursor/releases/download/$archive_tag"
  for asset in "bibata-material-dark-$archive_tag.tar.gz" "bibata-material-light-$archive_tag.tar.gz" "SHA256SUMS-$archive_tag.txt"; do
    curl --fail --location --silent --show-error "$base_url/$asset" --output "$archives_dir/$asset"
  done
else
  archives_dir="$(cd "$archives_dir" && pwd)"
fi
dark_archive="bibata-material-dark-$archive_tag.tar.gz"; light_archive="bibata-material-light-$archive_tag.tar.gz"; checksum_file="SHA256SUMS-$archive_tag.txt"
for asset in "$dark_archive" "$light_archive" "$checksum_file"; do [[ -f "$archives_dir/$asset" ]] || { echo "Missing release asset: $archives_dir/$asset" >&2; exit 1; }; done
grep -E "  (bibata-material-(dark|light)-$archive_tag\\.tar\\.gz)$" "$archives_dir/$checksum_file" > "$work_dir/linux-checksums.txt" || { echo "Checksum manifest does not list both Linux archives" >&2; exit 1; }
[[ "$(wc -l < "$work_dir/linux-checksums.txt")" -eq 2 ]] || { echo "Expected exactly two Linux archive checksums" >&2; exit 1; }
(cd "$archives_dir" && sha256sum --check "$work_dir/linux-checksums.txt")
mkdir -p "$work_dir/dark" "$work_dir/light"
tar -xzf "$archives_dir/$dark_archive" -C "$work_dir/dark"; tar -xzf "$archives_dir/$light_archive" -C "$work_dir/light"
mapfile -t dark_roots < <(find "$work_dir/dark" -mindepth 1 -maxdepth 1 -type d -print)
mapfile -t light_roots < <(find "$work_dir/light" -mindepth 1 -maxdepth 1 -type d -print)
[[ ${#dark_roots[@]} -eq 1 && ${#light_roots[@]} -eq 1 ]] || { echo "Unexpected release archive layout" >&2; exit 1; }
pkg_root="$work_dir/package"; install -d "$pkg_root/DEBIAN" "$pkg_root/usr/share/icons" "$pkg_root/usr/share/doc/material-bibata-cursor"
for group_root in "${dark_roots[0]}" "${light_roots[0]}"; do
  while IFS= read -r -d '' theme_dir; do
    theme_name="$(basename "$theme_dir")"
    [[ ! -e "$pkg_root/usr/share/icons/$theme_name" ]] || { echo "Duplicate theme directory: $theme_name" >&2; exit 1; }
    cp -a "$theme_dir" "$pkg_root/usr/share/icons/$theme_name"
  done < <(find "$group_root" -mindepth 1 -maxdepth 1 -type d -name 'Bibata-Material-*' -print0)
done
theme_count="$(find "$pkg_root/usr/share/icons" -mindepth 1 -maxdepth 1 -type d -name 'Bibata-Material-*' | wc -l)"
[[ "$theme_count" -eq "$expected_themes" ]] || { echo "Expected $expected_themes theme directories, found $theme_count" >&2; exit 1; }
dark_root="${dark_roots[0]}"
for doc in LICENSE README.md CREDITS.txt; do [[ -f "$dark_root/$doc" ]] || { echo "Release archive is missing $doc" >&2; exit 1; }; done
for doc in LICENSE README.md CREDITS.txt; do install -m 0644 "$dark_root/$doc" "$pkg_root/usr/share/doc/material-bibata-cursor/$doc"; done
cat > "$pkg_root/DEBIAN/control" <<EOF
Package: material-bibata-cursor
Version: $version
Section: x11
Priority: optional
Architecture: all
Depends: hicolor-icon-theme
Maintainer: Sakib Shahariar <74959773+SakibShahariar@users.noreply.github.com>
Description: Material Design 3 Bibata cursor themes
  57 cursor themes with Xcursor, Hyprcursor, and scalable SVG assets.
  Installs the themes system-wide under /usr/share/icons.
EOF
cat > "$pkg_root/DEBIAN/copyright" <<'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Material Bibata Cursor
Source: https://github.com/SakibShahariar/material-bibata-cursor

Files: usr/share/icons/Bibata-Material-*
Copyright: Bibata Cursor contributors and Sakib Shahariar
License: GPL-3.0-or-later
 The cursor artwork is derived from Bibata_Cursor and is distributed under
 the GNU General Public License, version 3 or (at your option) any later version.
 See the installed CREDITS.txt and upstream license for attribution and terms.

Files: usr/share/doc/material-bibata-cursor/*
Copyright: 2026 Sakib Shahariar and upstream contributors
License: MIT and GPL-3.0-or-later
 See the included LICENSE and CREDITS.txt files for applicable terms.
EOF
mkdir -p "$output_dir"
output="$output_dir/material-bibata-cursor_${version}_all.deb"
dpkg-deb --root-owner-group --build "$pkg_root" "$output"
echo "Built $output with $theme_count package-owned cursor theme directories."
echo "Install: sudo apt install \"$output\""
echo "Remove:  sudo apt remove material-bibata-cursor"
