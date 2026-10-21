#!/usr/bin/env fish
# Backward-compatible entry point; the implementation lives in Python.
# New installations do not require Fish: use python3 scripts/build_linux.py.
set -l script_dir (dirname (readlink -f (status filename)))
exec python3 "$script_dir/build_linux.py" $argv
