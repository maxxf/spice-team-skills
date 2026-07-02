# Report Data Contract — findings.json + metrics.json

`references/build_report.py` and `references/make_charts.py` are **fully
data-driven**. Every number and every line of client-facing narrative comes
from these two files in the run directory. The builder source contains **zero
per-client literals** — enforced by `tests/test_report_conformance.py`. To
change wording or a number, change the JSON, never the Python, never the
generated HTML.

Run-dir layout:

```
<run_dir>/
  findings.json
  metrics.json
  report_style.css        # copied from references/
  assets/spice_icon.svg   # copied from references/assets/ (optional)
  charts/                 # produced by make_charts.py
```

## metrics.json (chart input)

```jsonc
{
  "radar": {
    "AOV": {"current": 9.9, "target": 9},
    "Re-order Rate": {"current": null, "target": 8, "pending": true},
    "Conversion (ad proxy)": {"current": 7.3, "target": 7},
    "Marketing Efficiency": {"current": 6.5, "target": 8},
    "Operations": {"current": 6.7, "target": 9},
    "Traffic (ad proxy)": {"current": 8.0, "target": 7},
    "Campaigns/ROAS*": {"current": 9.5, "target": 7}
  },
  "radar_overall": 8.0,
  "tiers": {"Green":1,"Yellow":1,"Red":1,"New":0,
            "by_store":{"Times Square":"Green","Las Vegas":"Red"}},
  "top15_green": [{"name":"…","gmv":61895,"tier":"Green"}],
  "top15_green_meta": {"title":"…","subtitle":"…"},
  "trend_weekly": {
    "weeks": ["W07","W08","…"],
    "gmv":   [4150.65, 4925.7, "…"],
    "orders":[74, 86, "…"],
    "title": "Weekly Trend — GMV & Orders (90d, DD+GH)",
    "caption": "…optional data-supplied callout / source string…",
    "source": "DD+GH per-order (UE history not pulled this cycle)"
  },
  "daypart": {
    "days":  ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
    "hours": [0,1,2,"…",23],
    "matrix": [[0,0,"…"], "…7 rows total, one per day…"],
    "peak": {"day":"Thu","hour":18,"orders":30},
    "weakest_day": "Tue",
    "title": "Order Daypart — orders by day × hour (90d, DD+GH)",
    "caption": "…optional; if omitted a peak/weakest caption is auto-built…",
    "source": "DD+GH per-order"
  },
  "funnel": {
    "stages": ["Store views","Menu views","Added to cart","Orders"],
    "values": [122096, 8544, 1775, 841],
    "title": "UE Conversion Funnel — 90d blended",
    "caption": "…optional data-supplied callout string…"
  },
  "storefront_audit": {
    "listings": [["UE Times Square", 71, "Good"], ["UE Las Vegas", 49, "Poor"]],
    "portfolio_avg": 62,
    "title": "Storefront Audit — score / 100 (Mar 11 baseline)",
    "subtitle": "…optional data-supplied subtitle…"
  }
}
```

`top15_green_meta` (optional) supplies the bar chart title/subtitle; absent ⇒
neutral defaults. `funnel`, `storefront_audit`, `trend_weekly` and `daypart`
are **optional** — when a key is absent the corresponding chart is honestly
skipped (printed, never fabricated) and the dependent report section degrades
to an explicit text note (never dropped, never falsely labelled "deferred"
when the data is in fact present).

`trend_weekly` — REAL weekly series. `weeks`/`gmv`/`orders` are parallel
arrays (any equal length). **Derived upstream from the per-order DoorDash
financial-transactions + Grubhub finance exports** (one row per order →
bucketed to ISO week), NOT from platform-aggregated summary CSVs. Drives
`make_charts.trend_overlay` (GMV bars + orders line on a twin axis) and the
report's **90-Day Trend** section. `title`/`caption`/`source` optional,
data-supplied — NEVER hardcoded in make_charts.py. When absent, 90-Day Trend
renders `findings.trend_pending_note` (honest, no sparkline fabricated).
**Rule: trend_weekly is derivable whenever per-order transaction exports
exist — only set null if those exports are genuinely absent.**

`daypart` — REAL day×hour order-count matrix. `matrix` is `len(days)` rows ×
`len(hours)` cols of order counts. **Derived upstream from the same per-order
DD/GH transaction exports** (DoorDash `Timestamp local time`; Grubhub
`order_date` + `order_hour_of_day`). `peak` `{day,hour,orders}` ⇒ ringed
cell + caption; `weakest_day` optional. Drives `make_charts.daypart_heatmap`
and the report's **Daypart** section. `title`/`caption`/`source` optional,
data-supplied. When `caption` is omitted the report auto-builds a
peak/weakest caption from `peak`/`weakest_day`. When the whole key is absent
the Daypart section renders `findings.daypart_pending_note`. **Same
derivability rule as trend_weekly.**

`radar_meta` / `tier_donut_meta` (both optional) supply data-driven
title/subtitle overrides for the radar and tier-donut charts; absent ⇒
neutral computed defaults.

`funnel`: `stages`/`values` are parallel arrays (any length). Stage-to-stage
drop-off % is auto-computed. `title`/`caption` optional, data-supplied — NEVER
hardcoded in make_charts.py.

`storefront_audit`: `listings` = `[name, score_0_100, grade]` rows
(`grade ∈ Good|Fair|Poor` drives colour; a missing/unknown grade ⇒ gray).
`portfolio_avg` optional ⇒ dashed reference line. `title`/`subtitle` optional,
data-supplied.

Radar honesty (encoded in make_charts.py): an axis with `current:null` OR
`pending:true` is DATA-PENDING — drawn at 0 with a `(pending)` tick and
EXCLUDED from the overall mean. Proxy-derived axes carry an `(ad proxy)`
suffix in the label key. Overall = mean of measured axes only.

## findings.json (report narrative + structure)

Header: `client, window, platforms, n_locations, locations_line,
cycle|cycle_label, prepared_line, output_html`.

### Hero — canonical 6 slots
`hero.slots` keyed by EXACT canonical labels (order fixed by builder):
`90-Day Gross` · `Orders` · `Blended AOV` · `Net Payout` ·
`Order Completion` · `Customer Sentiment`.

```jsonc
"hero": {
  "slots": {
    "90-Day Gross": {"value":102432,"sub":"…"},
    "Orders": {"value":1882,"sub":"…"},
    "Blended AOV": {"value":54.43,"sub":"…"},
    "Net Payout": {"value":"$44,549","sub":"…"},
    "Order Completion": {"value":"95.5%","sub":"…"},
    "Customer Sentiment": {"value":"7.0 / 10","sub":"…"}
  },
  "na_footnote": "UE payout not in export this cycle."
}
```
`value` may be a number (builder formats) or a preformatted string. If a
metric is unavailable, set `value:null` (or `"n/a"`) and supply
`na_footnote`. Builder renders `n/a*` + footnote — NEVER drops/substitutes a
slot.

### exec_summary
`{headline, bullets:[…], accent?, bg?}`. Omit headline ⇒ derived from
`foundation_gate.triggered`.

### Radar caption
`radar_overall`, `radar_weakest:[[name,{current,target}],…]`,
`radar_notes:[…]` (HTML `<li>` inner strings — carry attribution caveats).

### fro (Foothold/Risk/Opportunity)
`{foothold:{body,fig,action}, risk:{…}, opportunity:{…}}` — HTML strings,
omitted card skipped.

### levers (The Levers — actionable distillation of the opportunity)
Optional. Names the **top 2–4 levers that move the number**, each as
`current → target · mechanism · expected impact`. Rendered as its own block
(cards) right after Foothold/Risk/Opportunity. **Absent ⇒ block skipped**
(backward compatible). The recurring delivery levers are storefront CTR
(Traffic axis), AOV (below $30), and net payout / marketing efficiency — see
`diagnostic-framework.md` §"The Levers".

```jsonc
"levers": {
  "title": "The Three Levers — where the number moves",   // optional
  "intro": "…HTML lead-in…",                              // optional
  "items": [
    {"n": 1, "name": "Storefront click-through",
     "current": "9–10%", "target": "12–18%",              // both optional
     "unit": "storefront → menu CTR vs. benchmark",       // optional sub-label
     "mechanism": "New hero image + higher ratings. <b>Not a menu problem.</b>",
     "impact": "Closing half the gap ≈ +30% revenue, zero new ad spend."}
  ]
}
```
`name`/`unit`/`mechanism`/`impact`/`intro`/`current`/`target` are HTML the
builder emits verbatim; `n` and `title` are escaped. Any field may be omitted
(the card degrades gracefully). Keep levers consistent with the hero strip and
radar — **never state a lever value that contradicts a hero number** (internal-
consistency rule, see framework §"The Levers").

### Action plan
`timeline:[{when,what,sub,now?}]`,
`action_plan:{this_week_lane, this_week:[{title,meta}], review_lane:{lane,body}}`.

### tier_health
`{lines:[HTML…], note:"…pre-Spice baseline, not a Spice scorecard"}`.

### what_moved
First cycle: `{first_cycle_note:true, note?}`. Else
`{deltas:[{name,current,prior,delta,direction}]}`.

### Trend / Daypart narrative (findings.json)
`trend_caption` — optional override for the 90-Day Trend caption when
metrics.trend_weekly IS present (else metrics.trend_weekly.caption/source).
`daypart_caption` — optional override for the Daypart caption when
metrics.daypart IS present (else an auto peak/weakest caption is built).
`trend_pending_note`, `daypart_pending_note` — used ONLY when
metrics.trend_weekly / metrics.daypart are absent (honest, no fabrication).
These are derivable whenever per-order DD/GH transaction exports exist —
they must only be left absent if those exports are genuinely missing.

### data_quality_footer
HTML string.

### Half-2 toggles (ALL required — REQUIRED_TOGGLES)
| toggle | field | shape |
|---|---|---|
| Portfolio Snapshot | `portfolio_snapshot` | `{rows:[{platform,gross,orders,aov,eff_commission,net_pct,est_monthly,mktg_pct}],narrative}` |
| Menu & Storefront | `menu_storefront` | REQUIRED. Structured (see below) or `{html}` legacy. If field absent ⇒ builder emits explicit DATA-PENDING block (funnel + re-order). |
| Ops | `ops_detail` | `{html}` |
| Brand Operational Health | `brand_health_detail` | `{html}` |
| Campaigns | `campaigns_detail` | `{html}` — attribution caveat inline at point of use (campaign-lifetime vs 90d-matched). |
| Location Tiers | `location_tiers_detail` | `{html}` |
| Full Action Plan | `full_action_plan` | `{html}` |
| Appendix | `store_tiers` + `appendix_*` | see below |

`eff_commission/net_pct/mktg_pct` may be null ⇒ `n/a*` (never dropped).

#### Menu & Storefront — structured shape
The builder embeds `charts/storefront_audit.png` and `charts/funnel_ue.png`
inline when present (visible placeholder if pending — never silent), and
renders these optional contract fields around them:

```jsonc
"menu_storefront": {
  "intro": "<b>Storefront baseline …</b> HTML intro paragraph.",
  "storefront_table": {"headers": ["Listing","…","Total /100"],
                        "rows": [["UE Times Square","…","<b>71</b>"]]},
  "storefront_sections": [{"heading":"What the baseline says",
                           "paras":["…"], "bullets":["<b>Strong:</b> …"]}],
  "funnel_table": {"headers": ["Store","Store views","…"],
                   "rows": [["Times Square","59,156","…"]]},
  "funnel_sections": [{"heading":"…","bullets":["…"]}],
  "sections": [{"heading":"…","bullets":["…"]}],
  "html": "…legacy raw-HTML escape hatch (appended last) …"
}
```
All keys optional; cells/bullets are HTML strings the builder emits verbatim
(it never injects its own numbers). Order rendered: intro → storefront chart →
storefront_table → storefront_sections → funnel chart → funnel_table →
funnel_sections → generic sections → legacy `html`. Renders gracefully
text-only if the chart PNGs are absent. A data-pending verification block is
auto-appended unless the body already contains "data-pending"/"data pending".

### Appendix
`store_tiers` list; `appendix_sort_key` (default `blended_gmv`) numeric size
field, desc. Optional `appendix_columns:[{label,field,tier?,kind?}]`
(kind ∈ money|money2|int|raw) supports divergent schemas (e.g. Daily's
net_payout/cancel_rate single-platform). No columns ⇒ schema-agnostic
Store/Tier/<sort-key>. `appendix_note` = caption.

### deck (optional — client-deck-only narrative)
Consumed ONLY by `references/build_deck.js` (the Spice-branded client .pptx).
The report ignores it. Every slide that has a report equivalent reads the
SAME shared field (`hero.slots`, `radar_weakest`, `radar_notes`, `fro`,
`foundation_gate`, `portfolio_snapshot`, `action_plan`, `data_quality_footer`,
etc.). The `deck` object only supplies the few slides that are deck-specific
(title chrome, the headline-finding stat slide, the 3-lane action plan, the
closing "what we need" slide). All keys optional; an absent key ⇒ that slide
(or element) is skipped gracefully — never fabricated.

```jsonc
"deck": {
  "title_kicker": "Spice Digital · Delivery Marketplace Diagnostic",
  "baseline_note": "All data is the pre-Spice baseline — the bar we beat.",
  "sixty_second_title": "Portfolio at a glance — 90 days, all platforms",
  "radar_title": "6.9 / 10 — all axes measured",      // else "<overall> / 10"
  "foundation_gate_title": "…",                         // gate slide H1
  "foundation_gate_rows": [{"label":"DoorDash","detail":"Cancellation high"}],
  "foundation_gate_rule": "No spend until cleared.",    // else foundation_gate.rule
  "headline_finding": {                                  // omit ⇒ slide skipped
    "title": "Ads buy low-intent traffic",
    "stat": "0.69%", "stat_sub": "blended store-to-order conversion",
    "bullets": ["…", "…"]
  },
  "action_lanes": [                                      // ≤3 lanes; else falls
    {"lane": "This week", "items": ["…", "…"]},          //   back to
    {"lane": "Week 2",    "items": ["…"]},               //   action_plan.this_week
    {"lane": "30 days",   "items": ["…"]}
  ],
  "daypart_bullets": ["…optional extra bullets on the trend/daypart slide…"],
  "closing": {
    "kicker": "What we need from you", "title": "To move fast",
    "bullets": ["Close onboarding blockers", "Sign-off to proceed"]
  }
}
```

`foundation_gate.rows` (`[{label,detail}]`) and `foundation_gate.rule` (a
string) are also read by the deck's Foundation Gate slide when present — they
are optional additions to the existing `foundation_gate` object (the report
only uses `foundation_gate.triggered`, unchanged). The Foundation Gate slide
renders ONLY when `foundation_gate.triggered` is true.

## Deck generator (references/build_deck.js)

A second canonical builder, alongside `build_report.py`, that produces the
**Spice-branded client .pptx deck** (the client-shared deliverable).

- **Inputs:** `findings.json` + `metrics.json` (the SAME run-dir contract the
  report consumes — the deck adds no parallel data source), `charts/*.png`
  from the run dir, and the Spice Design System colour tokens **parsed at
  build time from `report_style.css` `:root`** (`--spice`, `--ink-*`,
  `--cream`, `--ok`/`--warn`/`--err`, …) — never hardcoded, so deck and
  report share one palette source and can't drift. Brand wordmarks are
  self-contained in `references/assets/` (no Cowork path dependency).
- **Output:** `<run_dir>/<client-slug>-deck.pptx` (slug from
  `findings.client_slug` else slugified `client`).
- **Data-driven, zero literals:** identical discipline to build_report.py —
  every client name / number / line of prose comes from the JSON contract.
  Enforced by `tests/test_report_conformance.py` (the banned-token list
  covers `build_deck.js` too).
- **Graceful chart degradation:** any `charts/*.png` that is absent is
  skipped (no broken image, no crash); the dependent slide element or whole
  slide is omitted. The Foundation-Gate, Headline-Finding,
  Foothold/Risk/Opportunity, economics, trend/daypart and action-plan slides
  each render only when their backing contract data is present.
- **Dependency:** Node + `pptxgenjs` (`npm install pptxgenjs` in the run
  dir, like other per-run deps).

## Window-trust rule (process)
Source-export date stamps are authoritative over manifest/Slack headers. If
they disagree, use export dates and state the discrepancy in
data_quality_footer.

## Attribution rule (process)
ROAS/attributed-sales must be labeled campaign-lifetime vs 90d-matched. Never
headline attributed sales exceeding window GMV without the caveat inline at
point of use (radar_notes + campaigns_detail).

## Tier "New" rule
`New` ONLY for genuinely newly-opened stores with insufficient history. Full
~90-day-history stores are tiered on actual performance (G/Y/R) and framed as
the pre-Spice baseline (the bar Spice will move), not a Spice scorecard.
Encode framing in tier_health.note + Location Tiers toggle prose.
