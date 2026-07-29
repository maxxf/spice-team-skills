#!/usr/bin/env python3
"""Render the Spend-Pacing Flash card from a JSON data file.

The card layout is NOT hand-authored. Describing a layout in prose produces a
different card every run, which is why two people running this skill on the same
week used to get two different images. This script owns the geometry so the
output is byte-comparable given the same data.

Usage
-----
    python3 render_flash_card.py data.json outdir/

Writes `<outdir>/flash-card.html` and, if Chrome is available,
`<outdir>/flash-card.png` (760 logical px wide, rendered at 2x, autocropped).

Why 760px: Slack renders an inline image at roughly 700px wide and scales the
whole card to fit. A 2400px-wide card gets squashed to about 29% and the type
becomes unreadable. Orientation is not the problem; width is.

Data contract
-------------
See `assets/flash-card-example.json` for a filled-in example. Fields:

    client, week, date        strings for the header chips
    headline                  may contain <g>lapsed-colour</g> and <o>new-colour</o>
    dek                       one line under the headline; <b> allowed
    axis_max                  chart axis ceiling; bars beyond it are clipped and
                              drawn with an arrowhead, and the axis is labelled
                              as clipped
    paired[]                  store, lapsed, new (ROAS as numbers, no % sign),
                              lapsed_budget, new_budget (strings),
                              lapsed_paced, new_paced (numbers, percent)
    others[]                  location, audience, budget, paced (number or null),
                              roas (number), tone: lapsed | new | info | neutral
    footnote                  count line under the others table
    bottom_line               may contain <b>
    foot                      provenance and window caveats

Every number is rendered exactly as given. The script does no arithmetic on
performance figures beyond chart geometry, so it cannot invent a value.
"""

import json
import os
import shutil
import subprocess
import sys

LAPSED = "#0f6e56"
NEW = "#a8620a"
INFO = "#185fa5"
NEUTRAL = "#57514c"
TONE = {"lapsed": LAPSED, "new": NEW, "info": INFO, "neutral": NEUTRAL}

CARD_W = 760          # logical px; do not raise (see module docstring)
PAD_X = 34
CHART_W = 692         # CARD_W - 2*PAD_X
LABEL_W = 130         # left gutter for store names
TRACK_R = 420         # right edge of the plotted track
BUDGET_X = 588        # right-aligned budget column
PACED_X = 692         # right-aligned pacing column
ROW_H = 29
ROW_Y0 = 46


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def rich(s):
    """Allow only the inline tags the data contract documents."""
    out = esc(s)
    for frm, to in (
        ("&lt;g&gt;", f'<tspan style="fill:{LAPSED}">'), ("&lt;/g&gt;", "</tspan>"),
        ("&lt;o&gt;", f'<tspan style="fill:{NEW}">'), ("&lt;/o&gt;", "</tspan>"),
        ("&lt;b&gt;", "<b>"), ("&lt;/b&gt;", "</b>"),
    ):
        out = out.replace(frm, to)
    return out


def rich_html(s):
    out = esc(s)
    for frm, to in (
        ("&lt;g&gt;", f'<span style="color:{LAPSED}">'), ("&lt;/g&gt;", "</span>"),
        ("&lt;o&gt;", f'<span style="color:{NEW}">'), ("&lt;/o&gt;", "</span>"),
        ("&lt;b&gt;", "<b>"), ("&lt;/b&gt;", "</b>"),
    ):
        out = out.replace(frm, to)
    return out


def build_chart(paired, axis_max):
    """Dumbbell rows. One row per store, New dot to Lapsed dot."""
    span = TRACK_R - LABEL_W

    def x(v):
        return LABEL_W + min(v, axis_max) / axis_max * span

    height = ROW_Y0 + ROW_H * len(paired) + 4
    ticks = 4
    grid, tick_labels = [], []
    for i in range(ticks):
        v = axis_max * i / (ticks - 1)
        gx = round(x(v), 1)
        grid.append(f'<line x1="{gx}" y1="28" x2="{gx}" y2="{height - 32}"/>')
        tick_labels.append(f'<text x="{gx}" y="{height - 14}">{round(v)}%</text>')

    rows = []
    for i, p in enumerate(paired):
        y = ROW_Y0 + ROW_H * i
        xn, xl = round(x(p["new"]), 1), round(x(p["lapsed"]), 1)
        clipped = p["lapsed"] > axis_max
        marker = (f'<path d="M{xl} {y - 10} L{xl + 8} {y - 4} L{xl} {y + 2} Z" fill="{LAPSED}"/>'
                  if clipped else
                  f'<circle cx="{xl}" cy="{y - 4}" r="5.5" fill="{LAPSED}"/>')
        lab_x = xl + (14 if clipped else 13)
        rows.append(f'''<g>
      <text x="0" y="{y}" font-size="13" font-weight="620" fill="#14110f">{esc(p["store"])}</text>
      <line x1="{xn}" y1="{y - 4}" x2="{xl}" y2="{y - 4}" stroke="#ddd8d1" stroke-width="2"/>
      <circle cx="{xn}" cy="{y - 4}" r="5.5" fill="{NEW}"/>
      {marker}
      <text x="{xn - 11}" y="{y}" font-size="12" fill="{NEW}" font-weight="640" text-anchor="end">{p["new"]}%</text>
      <text x="{lab_x}" y="{y}" font-size="12" fill="{LAPSED}" font-weight="700">{p["lapsed"]}%</text>
      <text x="{BUDGET_X}" y="{y}" font-size="12" fill="#57514c" text-anchor="end">{esc(p["lapsed_budget"])} vs {esc(p["new_budget"])}</text>
      <text x="{PACED_X}" y="{y}" font-size="12" fill="#57514c" text-anchor="end">{p["lapsed_paced"]} / {p["new_paced"]}%</text>
    </g>''')

    return f'''<svg viewBox="0 0 {CHART_W} {height}" width="{CHART_W}" height="{height}" role="img" aria-label="Return on ad spend for the Lapsed and New audience campaign at each store that runs both, with each store's weekly budget and pacing.">
    <g stroke="#eceae5" stroke-width="1">{''.join(grid)}</g>
    <g font-size="10.5" fill="#8b857f" text-anchor="middle" font-family="ui-sans-serif,system-ui,sans-serif">{''.join(tick_labels)}</g>
    <g font-size="10" fill="#8b857f" font-weight="640" letter-spacing="0.4" font-family="ui-sans-serif,system-ui,sans-serif">
      <text x="{BUDGET_X}" y="18" text-anchor="end">BUDGET/WK &#183; L vs N</text>
      <text x="{PACED_X}" y="18" text-anchor="end">PACED &#183; L vs N</text>
    </g>
    <g font-family="ui-sans-serif,system-ui,sans-serif">{''.join(rows)}</g>
  </svg>'''


def build_others(others):
    rows = []
    for o in others:
        colour = TONE.get(o.get("tone", "neutral"), NEUTRAL)
        weight = "660" if o.get("tone") in ("lapsed", "new") else "400"
        if o.get("paced") is None:
            paced = '<span class="num" style="color:#8b857f">n/a</span>'
        else:
            bar_colour = TONE.get(o.get("tone", "neutral"), NEUTRAL)
            paced = (f'<span class="pb"><span style="width:{o["paced"]}%;background:{bar_colour}"></span></span>'
                     f'<span class="num">{o["paced"]}%</span>')
        budget = o["budget"]
        budget_cell = (f'<td class="num" style="font-size:12px;color:#8b857f">{esc(budget)}</td>'
                       if not str(budget).startswith("$")
                       else f'<td class="num">{esc(budget)}</td>')
        rows.append(
            f'<tr><td>{esc(o["location"])} <span class="aud">{esc(o["audience"])}</span></td>'
            f'{budget_cell}<td>{paced}</td>'
            f'<td class="num" style="color:{colour};font-weight:{weight}">{o["roas"]}%</td></tr>'
        )
    return "\n      ".join(rows)


def build_html(d):
    chips = "".join(
        f'<span class="chip">{esc(v)}</span>' for v in (d["week"], "Spend-pacing flash", d["date"])
    )
    clip_note = (f'ROAS &#183; axis clipped at {d["axis_max"]}%'
                 if any(p["lapsed"] > d["axis_max"] for p in d["paired"])
                 else "Return on ad spend")
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(d["client"])} — {esc(d["week"])} flash</title>
<style>
  :root{{--ink:#14110f;--ink-2:#57514c;--ink-3:#8b857f;--line:#e7e2dc;--line-soft:#f2eee9;
    --lapsed:{LAPSED};--new:{NEW};--info:{INFO};--track:#eceae5}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{width:{CARD_W}px;background:#fff;color:var(--ink);
    font:15px/1.45 ui-sans-serif,-apple-system,"Segoe UI",Inter,system-ui,sans-serif;
    -webkit-font-smoothing:antialiased}}
  .num{{font-variant-numeric:tabular-nums}}
  .wrap{{padding:26px {PAD_X}px 22px}}
  .top{{display:flex;align-items:baseline;gap:9px;margin-bottom:12px;flex-wrap:wrap}}
  .brand{{font-size:19px;font-weight:700;letter-spacing:-.02em}}
  .chip{{font-size:11px;font-weight:640;letter-spacing:.07em;text-transform:uppercase;
    color:var(--ink-2);border:1px solid var(--line);border-radius:999px;padding:3px 9px}}
  h1{{font-size:25px;line-height:1.2;font-weight:700;letter-spacing:-.025em;margin-bottom:6px}}
  .dek{{font-size:14.5px;color:var(--ink-2);margin-bottom:16px;line-height:1.5}}
  .dek b{{font-weight:660;color:var(--ink)}}
  h2{{font-size:11px;font-weight:660;letter-spacing:.08em;text-transform:uppercase;
    color:var(--ink-3);margin:20px 0 9px}}
  .legend{{display:flex;gap:16px;font-size:13px;color:var(--ink-2);margin-bottom:2px;flex-wrap:wrap}}
  .legend i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}}
  table{{width:100%;border-collapse:collapse}}
  th{{font-size:10.5px;font-weight:640;letter-spacing:.05em;text-transform:uppercase;color:var(--ink-3);
    text-align:right;padding:0 7px 7px;border-bottom:1px solid var(--line)}}
  th:first-child{{text-align:left;padding-left:0}} th:last-child{{padding-right:0}}
  td{{font-size:13.5px;padding:7px;border-bottom:1px solid var(--line-soft);text-align:right}}
  td:first-child{{text-align:left;font-weight:580;padding-left:0}} td:last-child{{padding-right:0}}
  .aud{{font-size:11.5px;color:var(--ink-3);font-weight:520}}
  .pb{{display:inline-block;width:56px;height:5px;border-radius:3px;background:var(--track);
    overflow:hidden;vertical-align:1px;margin-right:7px}}
  .pb span{{display:block;height:100%;border-radius:3px}}
  .note{{color:var(--ink-3);font-size:12.5px;padding-top:9px}}
  .bl{{margin-top:18px;background:var(--ink);color:#f6f3ef;border-radius:10px;padding:15px 18px;
    font-size:15px;line-height:1.45}}
  .bl b{{color:#fff;font-weight:680}}
  .foot{{margin-top:11px;font-size:12px;color:var(--ink-3);line-height:1.45}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top"><span class="brand">{esc(d["client"])}</span>{chips}</div>
  <h1>{rich_html(d["headline"])}</h1>
  <p class="dek">{rich_html(d["dek"])}</p>
  <div class="legend">
    <span><i style="background:var(--lapsed)"></i>Lapsed</span>
    <span><i style="background:var(--new)"></i>New audience</span>
    <span style="color:var(--ink-3)">{clip_note}</span>
  </div>
  {build_chart(d["paired"], d["axis_max"])}
  <h2>Every other active Uber location</h2>
  <table>
    <thead><tr><th>Location</th><th>Budget/wk</th><th>Paced</th><th>ROAS</th></tr></thead>
    <tbody>
      {build_others(d["others"])}
      <tr><td colspan="4" style="border-bottom:0;text-align:left" class="note">{esc(d["footnote"])}</td></tr>
    </tbody>
  </table>
  <div class="bl">{rich_html(d["bottom_line"])}</div>
  <p class="foot">{esc(d["foot"])}</p>
</div>
</body>
</html>
'''


def find_chrome():
    for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        if os.path.exists(c):
            return c
    return shutil.which("google-chrome") or shutil.which("chromium")


def render_png(html_path, png_path):
    chrome = find_chrome()
    if not chrome:
        print("chrome not found — HTML written, PNG skipped", file=sys.stderr)
        return False
    raw = png_path + ".raw.png"
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                    "--force-device-scale-factor=2", "--virtual-time-budget=5000",
                    f"--window-size={CARD_W},2600", f"--screenshot={raw}",
                    "file://" + os.path.abspath(html_path)],
                   check=True, capture_output=True)
    try:
        from PIL import Image
    except ImportError:
        os.replace(raw, png_path)
        print("Pillow not installed — PNG not autocropped (trailing whitespace left in)",
              file=sys.stderr)
        return True
    im = Image.open(raw).convert("RGB")
    w, h = im.size
    px = im.load()
    bg = px[w - 5, h - 5]
    bottom = next((y for y in range(h - 1, -1, -1)
                   if not all(px[x, y] == bg for x in range(0, w, 16))), h - 1)
    im.crop((0, 0, w, min(h, bottom + 48))).save(png_path)
    os.remove(raw)
    return True


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: render_flash_card.py <data.json> <outdir>")
    with open(sys.argv[1]) as f:
        data = json.load(f)
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    html_path = os.path.join(outdir, "flash-card.html")
    with open(html_path, "w") as f:
        f.write(build_html(data))
    png_path = os.path.join(outdir, "flash-card.png")
    ok = render_png(html_path, png_path)
    print(html_path)
    if ok:
        print(png_path)


if __name__ == "__main__":
    main()
