#!/usr/bin/env fish
# Compiles themes from themes.json into installed Bibata cursor packs.
# Usage: compile_bibata_material.fish [theme-name]
#   No argument: compiles every theme in themes.json.
#   With a theme name (e.g. "Coral"): compiles only that one — much
#   faster when testing a new color you just added.

set -l requested_theme $argv[1]

set -l script_dir (dirname (readlink -f (status filename)))
set -l repo_root (dirname $script_dir)
set -l build_dir "$script_dir/bibata_cursor"
set -l themes_json "$repo_root/themes.json"
set -l install_dir $BIBATA_MATERIAL_INSTALL_DIR
if test -z "$install_dir"
    set install_dir "$HOME/.icons"
end
mkdir -p $install_dir

if not command -v jq >/dev/null
    echo "Error: jq is required." >&2
    exit 1
end

if not test -f $themes_json
    echo "Error: themes.json not found at $themes_json" >&2
    exit 1
end

if not test -d $build_dir
    echo "Cloning bibata_cursor source..."
    if not git clone https://github.com/rtgiskard/bibata_cursor $build_dir
        echo "Error: failed to clone bibata_cursor" >&2
        exit 1
    end
else if not test -f "$build_dir/src/cursor_utils.py"
    # Directory exists but looks incomplete/empty — likely a previous
    # clone got interrupted. Re-clone instead of failing cryptically
    # later at the cp step.
    echo "Existing bibata_cursor/ looks incomplete, re-cloning..."
    rm -rf $build_dir
    if not git clone https://github.com/rtgiskard/bibata_cursor $build_dir
        echo "Error: failed to clone bibata_cursor" >&2
        exit 1
    end
end

set -l theme_names
if test -n "$requested_theme"
    if not jq -e --arg n "$requested_theme" 'has($n)' $themes_json >/dev/null
        echo "Error: '$requested_theme' not found in themes.json" >&2
        exit 1
    end
    set theme_names $requested_theme
else
    set theme_names (jq -r 'keys[]' $themes_json)
end

if test (count $theme_names) -eq 0
    echo "Error: themes.json contains no themes" >&2
    exit 1
end

set -l fail_count 0
set -l ok_count 0

for NAME in $theme_names
    set -l BODY (jq -r --arg n "$NAME" '.[$n].body' $themes_json)
    set -l PRIMARY (jq -r --arg n "$NAME" '.[$n].primary' $themes_json)
    set -l WATCH (jq -r --arg n "$NAME" '.[$n].watch' $themes_json)

    if test -z "$BODY" -o -z "$PRIMARY" -o -z "$WATCH" -o "$BODY" = "null"
        echo "Skipping '$NAME': missing colors in themes.json" >&2
        set fail_count (math $fail_count + 1)
        continue
    end

    set -l theme_name "Bibata-Material-$NAME"
    echo "Processing: $theme_name ($BODY / $PRIMARY / $WATCH)"

    set -l temp_run_dir "$build_dir/run_$NAME"
    rm -rf $temp_run_dir
    mkdir -p $temp_run_dir
    cp -r $build_dir/src $temp_run_dir/
    cp -r $build_dir/svg $temp_run_dir/
    cp -r $build_dir/config $temp_run_dir/
    cd $temp_run_dir

    set -l py_status (python3 -c "
import json, sys
try:
    with open('config/render.json') as f:
        d = json.load(f)
    t = 'Bibata-Modern-Classic'
    d[t]['colors'][0]['replace'] = '$BODY'
    d[t]['colors'][1]['replace'] = '$PRIMARY'
    d[t]['colors'][2]['replace'] = '$WATCH'
    with open('config/render.json', 'w') as f:
        json.dump(d, f, indent=2)

    # Expand X11 cursor sizes beyond the upstream default so fractional
    # display scaling (125%, 150%, etc.) gets an exact-match bitmap
    # instead of a blurry nearest-size scale. Sizes are 24px-base scaled
    # 0.5x-3x in 0.25x steps, merged with upstream's original list.
    # See: https://blogs.kde.org/2024/10/09/cursor-size-problems-in-wayland-explained/
    with open('config/build.toml') as f:
        build_toml = f.read()
    old_sizes = 'x11_sizes = [16, 20, 22, 24, 28, 32, 48, 64, 72, 84, 96]'
    new_sizes = 'x11_sizes = [12, 16, 18, 20, 22, 24, 28, 30, 32, 36, 42, 48, 54, 60, 64, 66, 72, 84, 96]'
    if old_sizes not in build_toml:
        print('build.toml sizes line not found in expected format, skipping size expansion', file=sys.stderr)
    else:
        build_toml = build_toml.replace(old_sizes, new_sizes)
        with open('config/build.toml', 'w') as f:
            f.write(build_toml)
except Exception as e:
    print(f'config patch failed: {e}', file=sys.stderr)
    sys.exit(1)
"; echo $status)

    if test "$py_status" != "0"
        echo "Failed to patch render.json for $NAME" >&2
        cd $build_dir
        rm -rf $temp_run_dir
        set fail_count (math $fail_count + 1)
        continue
    end

    if not ./src/cursor_utils.py --x11 --hypr --theme "Bibata-Modern-Classic" --out-dir "out" >/dev/null 2>compile_err.log
        echo "cursor_utils.py failed for $NAME:" >&2
        cat compile_err.log >&2
        cd $build_dir
        rm -rf $temp_run_dir
        set fail_count (math $fail_count + 1)
        continue
    end

    if test -d "out/Bibata-Modern-Classic"
        rm -rf "$install_dir/$theme_name"
        mv "out/Bibata-Modern-Classic" "$install_dir/$theme_name"

        if python3 "$script_dir/metadata_generator.py" \
                --install-dir "$install_dir" \
                --themes-json "$themes_json" \
                --theme "$NAME" >/dev/null 2>metadata_err.log
            set ok_count (math $ok_count + 1)
        else
            echo "Theme compiled but metadata_generator.py failed for $NAME:" >&2
            cat metadata_err.log >&2
            set fail_count (math $fail_count + 1)
        end
    else
        echo "Expected output dir missing for $NAME" >&2
        set fail_count (math $fail_count + 1)
    end

    cd $build_dir
    rm -rf $temp_run_dir
end

echo ""
echo "Finished: $ok_count succeeded, $fail_count failed."
echo "Installed to: $install_dir"

if test $fail_count -gt 0
    exit 1
end
