#!/usr/bin/env fish
# Compiles themes from themes.json into installed Bibata cursor packs.
#
# Usage:
#   compile_bibata_material.fish [theme-name] [--exclude Name1,Name2] [--only-light] [--only-dark]
#
#   No argument: compiles every theme in themes.json.
#   With a theme name (e.g. "Coral"): compiles only that one — much
#   faster when testing a new color you just added.
#   --exclude: comma-separated theme names to skip.
#   --only-light / --only-dark: only build "-Light" themes, or only
#   the non-"-Light" set (includes Classic). Mutually exclusive.
#
#   Each compiled theme also gets a cursors_scalable/ SVG export (the
#   format KDE Plasma 6.2+ and GNOME 51+ render instead of Xcursor
#   bitmaps). Those are written to $XDG_DATA_HOME/icons by default
#   (override with BIBATA_MATERIAL_SCALABLE_DIR), since GNOME only
#   searches data dirs for SVG cursors, never ~/.icons.

argparse 'exclude=' 'only-light' 'only-dark' -- $argv
or exit 1

if set -q _flag_only_light; and set -q _flag_only_dark
    echo "Error: --only-light and --only-dark can't be used together." >&2
    exit 1
end

set -l requested_theme $argv[1]

set -l script_dir (dirname (readlink -f (status filename)))
set -l repo_root (dirname $script_dir)
set -l build_dir "$script_dir/bibata_cursor"
# Pin the upstream build source so theme output does not change silently.
set -l upstream_commit "f4ccfe8abb63fddc7b3ce51a866fd8378395cb3d"
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
    echo "Cloning bibata_cursor source at $upstream_commit..."
    if not git clone https://github.com/rtgiskard/bibata_cursor $build_dir
        echo "Error: failed to clone bibata_cursor" >&2
        exit 1
    end
else if not test -f "$build_dir/src/cursor_utils.py"
    # Directory exists but looks incomplete/empty — likely a previous
    # clone got interrupted. Re-clone instead of failing cryptically
    # later at the cp step.
    rm -rf $build_dir
    echo "Existing bibata_cursor/ looks incomplete, re-cloning..."
    if not git clone https://github.com/rtgiskard/bibata_cursor $build_dir
        echo "Error: failed to clone bibata_cursor" >&2
        exit 1
    end
end

# Existing clones must use the same known-good revision as fresh clones.
# Fetching/checking out fails safely if local changes prevent the checkout.
if not git -C $build_dir fetch --quiet origin $upstream_commit
    echo "Error: could not fetch pinned bibata_cursor commit $upstream_commit" >&2
    exit 1
end
if not git -C $build_dir checkout --quiet --detach $upstream_commit
    echo "Error: could not check out pinned bibata_cursor commit. Check for local changes in $build_dir." >&2
    exit 1
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

# Apply --only-light / --only-dark filtering
if set -q _flag_only_light
    set theme_names (for t in $theme_names; string match -q '*-Light' -- $t; and echo $t; end)
else if set -q _flag_only_dark
    set theme_names (for t in $theme_names; string match -qv '*-Light' -- $t; and echo $t; end)
end

# Apply --exclude filtering
if set -q _flag_exclude
    set -l exclude_names (string split ',' $_flag_exclude)
    set -l filtered
    for t in $theme_names
        if not contains $t $exclude_names
            set -a filtered $t
        else
            echo "Excluding '$t' (--exclude)" >&2
        end
    end
    set theme_names $filtered
end

if test (count $theme_names) -eq 0
    echo "Error: no themes to build after filtering" >&2
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
import json, re, sys, tomllib
try:
    with open('config/render.json') as f:
        d = json.load(f)
    t = 'Bibata-Modern-Classic'
    d[t]['colors'][0]['replace'] = '$BODY'
    d[t]['colors'][1]['replace'] = '$PRIMARY'
    d[t]['colors'][2]['replace'] = '$WATCH'
    with open('config/render.json', 'w') as f:
        json.dump(d, f, indent=2)

    # Expand the existing X11 sizes without depending on upstream's exact
    # formatting or original size list. Keep upstream sizes and add the
    # values needed for fractional display scaling.
    config_path = 'config/build.toml'
    with open(config_path, 'rb') as f:
        config = tomllib.load(f)
    sizes = config.get('cursor_defaults', {}).get('x11_sizes')
    if not isinstance(sizes, list) or not sizes or any(type(n) is not int or n <= 0 for n in sizes):
        raise ValueError('cursor_defaults.x11_sizes is missing or invalid')
    extra_sizes = [12, 18, 30, 36, 42, 54, 60, 66]
    merged_sizes = sorted(set(sizes).union(extra_sizes))
    with open(config_path, 'r', encoding='utf-8') as f:
        build_toml = f.read()
    pattern = r'(?m)^(\s*x11_sizes\s*=\s*)\[[^\]]*\]'
    build_toml, replacements = re.subn(
        pattern,
        lambda match: match.group(1) + '[' + ', '.join(map(str, merged_sizes)) + ']',
        build_toml,
        count=1,
    )
    if replacements != 1:
        raise ValueError('could not locate cursor_defaults.x11_sizes assignment')
    with open(config_path, 'w', encoding='utf-8') as f:
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
            if python3 "$script_dir/generate_svg_cursors.py" \
                    --theme "$NAME" \
                    --install-dir "$install_dir" \
                    --themes-json "$themes_json" >/dev/null 2>svg_err.log
                set ok_count (math $ok_count + 1)
            else
                echo "Theme compiled but generate_svg_cursors.py failed for $NAME:" >&2
                cat svg_err.log >&2
                set fail_count (math $fail_count + 1)
            end
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
