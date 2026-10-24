# Hotspot QA at fractional scaling

This checklist verifies that critical cursor hotspots remain on the
expected tip/handle when the desktop uses fractional scaling
(125%, 150%, and 200%).

## Semi-automated report

After building a theme, run:

```bash
python3 scripts/qa_hotspots.py \
  --theme Peach \
  --scalable-dir ~/.local/share/icons
```

The script reads `cursors_scalable/<shape>/metadata.json`, computes the
hotspot for each QA scale, and reports the rounding drift from the ideal
scaled position. Use `--fail-over 1` to make the command exit non-zero
when any critical hotspot drifts by more than one device pixel.

## Manual checklist

For each scale (125%, 150%, 200%), check:

- [ ] `left_ptr`: clicks land on the arrow tip.
- [ ] `xterm`: clicks land on the text I-beam center.
- [ ] `wait` / `left_ptr_watch`: the busy indicator remains centered and
      its hotspot does not jump between animation frames.
- [ ] `bottom_right_corner`, `bottom_left_corner`, `top_right_corner`,
      and `top_left_corner`: resize drags begin at the visible corner.
- [ ] `bd_double_arrow` and `fd_double_arrow`: drags begin on the
      diagonal handle, not offset into empty canvas.

## Filing a problem

If a hotspot is wrong, file an issue with:

- Theme name (for example, `Peach`).
- Shape name (for example, `bottom_right_corner`).
- Desktop and scale (for example, GNOME at 150%).
- Expected versus observed click point.
- Output of `scripts/qa_hotspots.py` if available.
