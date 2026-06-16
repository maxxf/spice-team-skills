# Visual Standards

Charts in the executive review MUST use QuickChart, not Mermaid. Mermaid xychart-beta renders 1-2px line widths that disappear in Notion's content width. QuickChart PNGs render bold and consistent across devices.

## Color palette

Use these specific hex values for consistency across all clients:

| Use | Color | Hex | Meaning |
| :-- | :--: | :-: | :-- |
| Marketing spend, "cost-down is good" | Red | `#E63946` | Money out the door |
| ROAS, payout, "growth is good" | Teal | `#2A9D8F` | Returns and margin |
| Sales trajectory primary line | Dark navy | `#264653` | Neutral story line |
| Ratings velocity, "before/after improvement" | Orange | `#F4A261` | Discovery, attention |
| "Before" / baseline / pre-intervention | Slate gray | `#94A3B8` | Anchor for comparison |
| Border / dark outline | Dark slate | `#475569` | Visual definition |

## Chart specifications

All charts:
- **Background**: white (`bkg=white` URL param)
- **Dimensions**: 700×400 px
- **Border width**: 4px on lines, 2px on bar outlines
- **Point radius**: 6px on data points
- **Title font**: 18pt
- **Axis labels**: 14pt
- **Always specify y-axis min/max** (don't auto-scale; sudden 0-baseline charts mislead)
- **Line charts**: include `tension: 0.3` for slight smoothing, `fill: true` for area shading at 10-15% opacity

## Chart type decisions

| Data | Chart type | Notes |
| :-- | :-- | :-- |
| Weekly trajectory over time | Line | Use teal for "improving" metrics, red for "declining is good" (e.g., spend) |
| Before/After comparison (2-bar) | Bar | Gray baseline + colored after-state |
| Per-location comparison (multi-bar) | Bar | Use same colors for same metric type |
| Two metrics on same x-axis (e.g., SJ + Pas sales) | Dual-line | Use complementary colors (red + dark navy) |
| Multi-tier breakdown (stacked) | Stacked bar | Avoid if more than 4 tiers |

## URL construction

Build URLs via `scripts/build_chart_urls.py` rather than hand-rolling. The script ensures consistent styling.

Example pattern for a line chart:
```
https://quickchart.io/chart?bkg=white&w=700&h=400&c={URL-encoded JSON config}
```

Where the JSON config follows this template:
```json
{
  "type": "line",
  "data": {
    "labels": [...],
    "datasets": [{
      "label": "...",
      "data": [...],
      "borderColor": "#E63946",
      "backgroundColor": "rgba(230, 57, 70, 0.1)",
      "borderWidth": 4,
      "pointRadius": 6,
      "pointBackgroundColor": "#E63946",
      "fill": true,
      "tension": 0.3
    }]
  },
  "options": {
    "title": {"display": true, "text": "...", "fontSize": 18},
    "legend": {"display": false},
    "scales": {
      "yAxes": [{"ticks": {"min": ..., "max": ..., "fontSize": 14}}],
      "xAxes": [{"ticks": {"fontSize": 14}}]
    }
  }
}
```

## Embedding in Notion

Use standard markdown image syntax: `![alt text](URL)`

Don't wrap in Notion image blocks via the API: markdown image syntax handles it cleanly.

## When NOT to use a chart

A table is better than a chart when:
- Showing 4+ metrics across 3+ categories (per-store table)
- Showing % deltas alongside absolutes (the High Level Metrics table)
- Showing target-vs-actual KPI tracking (the Forward Plan KPI table)

Use charts only for trajectories (line) or before-after comparisons (bar). Don't render the same data twice (e.g., a chart AND a table with the same numbers).

## Number formatting standards

Per the Weekly Reporting Skill canonical doc:

| Type | Format | Example |
| :-: | :-- | :-- |
| Currency (large) | $X,XXX (no cents) | $581,782 |
| Currency (AOV) | $XX.XX (with cents) | $42.39 |
| Currency (millions) | $X.XXM | $13.42M |
| Currency (thousands) | $XK or $XX.XK | $129K, $13.5K |
| Percentages | X% (no decimals) | 10% |
| Percentage point change | +X pts or +X.X pts | +5 pts, +4.3 pts |
| ROAS | X.Xx (1 decimal + 'x' suffix) | 8.8x |
| Orders | X,XXX (integer) | 1,234 |
| YoY % | +X% or -X% | +60% |
