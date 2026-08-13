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
except Exception as e:
    print(f'render.json patch failed: {e}', file=sys.stderr)
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

            # KDE Plasma 6.2+ SVG cursor variant — additive, non-fatal:
            # a failure here doesn't invalidate the theme, since the
            # core Xcursor/hyprcursor output already succeeded above.
            if not python3 "$script_dir/generate_kde_svg_cursors.py" \
                    --install-dir "$install_dir" \
                    --themes-json "$themes_json" \
                    --theme "$NAME" >/dev/null 2>kde_svg_err.log
                echo "Warning: KDE SVG cursor generation failed for $NAME:" >&2
                cat kde_svg_err.log >&2
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
