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
  "trend_weekly": null,
  "daypart": null,
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
neutral defaults. `funnel` and `storefront_audit` are **optional** — when a
key is absent the corresponding chart is honestly skipped (printed, never
fabricated) exactly like `trend_weekly`/`daypart`, and the Menu & Storefront
toggle still renders text-only.

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

### Action plan
`timeline:[{when,what,sub,now?}]`,
`action_plan:{this_week_lane, this_week:[{title,meta}], review_lane:{lane,body}}`.

### tier_health
`{lines:[HTML…], note:"…pre-Spice baseline, not a Spice scorecard"}`.

### what_moved
First cycle: `{first_cycle_note:true, note?}`. Else
`{deltas:[{name,current,prior,delta,direction}]}`.

### Pending notes
`trend_pending_note`, `daypart_pending_note` — used when
metrics.trend_weekly / metrics.daypart absent (honest, no fabrication).

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
