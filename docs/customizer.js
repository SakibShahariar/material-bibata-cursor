/* Live theme customizer for the gallery. Recolors SVG templates that carry
   {{BODY}} / {{PRIMARY}} / {{WATCH}} / {{SPINNER0..3}} / {{CORNER0..3}} tokens. */
(function () {
  'use strict';
  const form = document.getElementById('customizer');
  if (!form) return;
  const preview = document.getElementById('custom-preview');
  const output = document.getElementById('custom-output');
  const status = document.getElementById('custom-status');
  const inputs = {
    body: document.getElementById('custom-body'),
    primary: document.getElementById('custom-primary'),
    watch: document.getElementById('custom-watch'),
  };
  const TEMPLATES = ['left_ptr', 'xterm', 'bd_double_arrow', 'wait', 'bottom_right_corner'];
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const templates = window.GALLERY_TEMPLATES || {};

  // --- Colorsys-compatible HLS (matches scripts/spinner_colors.py) --------
  function hexToRgb(hex) {
    const v = hex.replace('#', '');
    return [parseInt(v.slice(0, 2), 16) / 255, parseInt(v.slice(2, 4), 16) / 255, parseInt(v.slice(4, 6), 16) / 255];
  }
  function rgbToHex(r, g, b) {
    const h = (x) => Math.max(0, Math.min(255, Math.round(x * 255))).toString(16).padStart(2, '0');
    return ('#' + h(r) + h(g) + h(b)).toUpperCase();
  }
  function rgbToHls(r, g, b) {
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    const l = (min + max) / 2;
    if (min === max) return [0, l, 0];
    let s = l <= 0.5 ? (max - min) / (max + min) : (max - min) / (2 - max - min);
    const rc = (max - r) / (max - min), gc = (max - g) / (max - min), bc = (max - b) / (max - min);
    let h;
    if (r === max) h = bc - gc;
    else if (g === max) h = 2 + rc - bc;
    else h = 4 + gc - rc;
    h /= 6;
    if (h < 0) h += 1;
    return [h, l, s];
  }
  function hlsToRgb(h, l, s) {
    if (s === 0) return [l, l, l];
    const m2 = l <= 0.5 ? l * (1 + s) : l + s - l * s;
    const m1 = 2 * l - m2;
    return [v(m1, m2, h + 1 / 3), v(m1, m2, h), v(m1, m2, h - 1 / 3)];
  }
  function v(m1, m2, hue) {
    hue = ((hue % 1) + 1) % 1;
    if (hue < 1 / 6) return m1 + (m2 - m1) * hue * 6;
    if (hue < 1 / 2) return m2;
    if (hue < 2 / 3) return m1 + (m2 - m1) * (2 / 3 - hue) * 6;
    return m1;
  }
  const OFFSETS = [-0.18, -0.06, 0.06, 0.18];
  const MIN_L = 0.20, MAX_L = 0.88;
  function shades(primary) {
    const [h, l, s] = rgbToHls(...hexToRgb(primary));
    let spread = OFFSETS.map((o) => l + o);
    if (spread[spread.length - 1] > MAX_L) { const d = spread[spread.length - 1] - MAX_L; spread = spread.map((x) => x - d); }
    if (spread[0] < MIN_L) { const d = MIN_L - spread[0]; spread = spread.map((x) => x + d); }
    return spread.map((x) => rgbToHex(...hlsToRgb(h, x, s)));
  }

  function substitute(svg, colors) {
    let out = svg;
    const map = {
      '{{BODY}}': colors.body, '{{PRIMARY}}': colors.primary, '{{WATCH}}': colors.watch,
    };
    colors.spinner.forEach((c, i) => { map['{{SPINNER' + i + '}}'] = c; });
    colors.spinner.forEach((c, i) => { map['{{CORNER' + i + '}}'] = c; });
    for (const [token, value] of Object.entries(map)) out = out.split(token).join(value);
    return out;
  }

  function swatch(label, value) {
    return '<div class="color"><i style="background:' + value + '"></i><code>' + label + ' ' + value + '</code></div>';
  }

  function update() {
    const colors = {
      body: inputs.body.value.toUpperCase(),
      primary: inputs.primary.value.toUpperCase(),
      watch: inputs.watch.value.toUpperCase(),
      spinner: shades(inputs.primary.value),
    };
    preview.replaceChildren();
    if (Object.keys(templates).length === 0) { status.textContent = 'Could not load customizer templates.'; return; }
    for (const shape of TEMPLATES) {
      const wrap = document.createElement('div');
      wrap.className = 'custom-shape';
      wrap.innerHTML = substitute(templates[shape], colors);
      wrap.setAttribute('aria-label', shape.replaceAll('_', ' ') + ' preview');
      preview.append(wrap);
    }
    const shadeList = colors.spinner.join(', ');
    output.innerHTML = '<div class="colors">' + swatch('Body', colors.body) + swatch('Primary', colors.primary) +
      swatch('Watch', colors.watch) + '</div><p class="shades">Derived shades: <code>' + shadeList + '</code></p>' +
      '<pre>' + escapeHtml(JSON.stringify({ 'My Theme': { label: 'My Theme', body: colors.body, primary: colors.primary, watch: colors.watch } }, null, 2)) + '</pre>';
    status.textContent = 'Live preview of your palette.';
  }
  function escapeHtml(s) { return s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c])); }

  Object.values(inputs).forEach((el) => el.addEventListener('input', update));
  reduceMotion.addEventListener('change', update);
  update();
})();
