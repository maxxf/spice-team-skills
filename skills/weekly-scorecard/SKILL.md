---
name: weekly-scorecard
description: Spin up the Spice Weekly Scorecard live artifact in this user's Cowork sidebar, OR run the bridge script to produce scorecard_rows.csv from weekly-reporting skill outputs, OR generate a static client-facing HTML export. Trigger on "show me the scorecard", "open the weekly scorecard", "spin up the scorecard", "scorecard for [client]", "generate scorecard rows", "build client scorecard export", or any request to view, fill, or share the weekly scorecard. Owner: Santi. Reporters: Manish + Dulari. GMs: tune thresholds + write Signal callouts.
---

# Weekly Scorecard Skill

The Spice Weekly Scorecard turns raw platform data into a triage tool — five-question format (Money, Efficiency, Operations, Reputation, Discoverability), status dots, sparklines, GM-authored Signal callout. Lives at three altitudes: the live Cowork artifact (interactive, GMs), the static HTML export (client-facing), and the long-format Google Sheet (canonical data store).

**Process owner:** Santi.
**Data filling:** Manish (8 clients), Dulari (6 clients).
**Strategy + threshold tuning:** GMs.

---

## When this skill triggers

Use this skill whenever a user asks to:

- **"Show me the scorecard"** / "open the weekly scorecard" / "spin up the scorecard" → create the live artifact in their Cowork sidebar
- **"Generate scorecard rows for [client]"** / "run the bridge script" → pivot weekly-reporting skill outputs into the canonical long-format CSV ready to paste
- **"Generate client export for [client]"** / "build the client scorecard PDF" / "send [client] their scorecard" → produce the static, branded HTML for the client
- **"What's the threshold for [metric]?"** → reference `references/threshold-config-template.md`
- **"Audit the scorecard"** / "check master Sheet" → run Santi's Tuesday checklist (see Process Owner Guide in Notion)
- **"How do I onboard [client] to the scorecard?"** → run the per-client onboarding checklist

---

## Three actions this skill performs

### Action 1: Spin up the live artifact (the most common request)

When the user wants to view the scorecard interactively, call the Cowork artifact creation tool with the bundled HTML:

```
mcp__cowork__create_artifact(
  id: "spice-weekly-scorecard",
  html_path: "<absolute path to artifact/scorecard.html>",
  description: "Live weekly scorecard for Spice clients. Reads the master Sheet via Drive MCP, pivots into 5-section format with sparklines, status dots, and GM Signal callout.",
  mcp_tools: [
    "mcp__3cfdef12-aed5-469f-904c-ae7eaeff04dd__read_file_content",
    "mcp__f34fcb36-bc14-4569-bc45-beaff552d0f7__notion-search",
    "mcp__f34fcb36-bc14-4569-bc45-beaff552d0f7__notion-fetch",
    "mcp__f34fcb36-bc14-4569-bc45-beaff552d0f7__notion-create-pages",
    "mcp__f34fcb36-bc14-4569-bc45-beaff552d0f7__notion-update-page"
  ]
)
```

The artifact is self-contained — once created it lives in the user's Cowork sidebar and refreshes from the master Sheet on every open. Each user gets their own personal instance pointing at the same shared data.

**Required for the artifact to work:**
- Drive MCP connected (auth to a Google account that can read the master Sheet)
- Notion MCP connected (auth to the Spice workspace)
- Read access to the master Sheet (`1kL39_lOQYsYkUN4h1iZGqdgnkjOu1OfD1SdjI0g2Ajo`)
- Read/write access to the Spice Weekly Signals DB (`b2add89ee6e14ef3ad9811e941515066`)

If any of these are missing, ask the user to fix the auth before spinning up the artifact.

### Action 2: Generate scorecard rows from weekly-reporting outputs

When Manish or Dulari runs the weekly-reporting skill and needs the long-format rows for the master Sheet:

```bash
python3 scripts/generate_scorecard_rows.py \
  --platform-csv path/to/platform_overview.csv \
  --location-csv path/to/by_location.csv \
  --client [client_slug] \
  --week-start YYYY-MM-DD \
  --week-end YYYY-MM-DD \
  --pulled-by [Manish|Dulari] \
  --active-platforms UE,DD,GH \
  --thresholds-csv references/[client]_thresholds.csv \
  --output ./scorecard_rows.csv
```

The output is paste-ready — open the master Sheet's `data` tab, click into the first empty row, paste.

**Inputs come from the existing weekly-reporting skill** (`/Skills/weekly-reporting/`). It outputs `platform_overview.csv` and `by_location.csv` as part of its standard run. This script bridges them to the scorecard format.

**Per-client thresholds:** if the client has a Notion threshold config (most do), there should be a matching CSV at `references/[client]_thresholds.csv` with the same values. Without `--thresholds-csv`, the script uses defaults from the master Sheet's `thresholds_default` tab.

### Action 3: Generate static client-facing HTML export

When ready to share the scorecard with a client:

```bash
python3 scripts/scorecard-export.py \
  --csv path/to/scorecard_rows_for_client.csv \
  --client [client_slug] \
  --week-end YYYY-MM-DD \
  --output Clients/[client]/scorecards/[client]-W[N]-[date].html \
  --signal-file path/to/signal.txt
```

Outputs a self-contained, brand-colored HTML file. Email it to the client, or upload to their Notion portal.

**Brand colors** are baked in for `fresh_kitchen` and `goop_kitchen`. For other clients, the script falls back to neutral colors. Add brand presets to the script's `BRAND_PRESETS` dict as new clients onboard.

---

## Per-client onboarding (Santi's process)

Roughly 30 minutes per client. Detailed checklist in [Process Owner Guide](https://app.notion.com/p/353d3ff018e78165b7d9faa22fda25b3).

1. Confirm client tracker matches canonical schema (existing weekly-reporting skill produces 20 standard metrics).
2. Add a row to master Sheet's `clients` tab with slug, display name, tracker URL, active platforms, location count, service lead.
3. Create the client's Threshold Config in their Notion Weekly Reporting Profile (copy from `references/threshold-config-template.md`).
4. Create the matching CSV at `references/[client]_thresholds.csv` (same values, machine-readable).
5. Backfill 4 weeks of historical data: Manish/Dulari runs the existing skill for each past week, runs `generate_scorecard_rows.py`, pastes into the master Sheet.
6. Validate by spinning up the artifact, switching to the new client, scanning status dots.

---

## Threshold tuning

Three patterns: default (industry standard), per-client absolute tightening (premium brands), per-client tier-based (multi-unit clients with RED/UNICORN/etc).

When a GM asks for a threshold change:
1. Update the client's Notion Reporting Profile threshold table (human-readable source of truth)
2. Update the matching `references/[client]_thresholds.csv` (machine-readable, fed to the bridge script)
3. Re-run the bridge script for the most recent week so updated statuses propagate

Both files must stay in sync. Future v2 will auto-extract from Notion to CSV.

---

## File inventory in this skill folder

- `SKILL.md` — this file
- `artifact/scorecard.html` — the live Cowork artifact source
- `scripts/generate_scorecard_rows.py` — the bridge from weekly-reporting outputs to master Sheet
- `scripts/scorecard-export.py` — static client-facing HTML generator
- `references/threshold-config-template.md` — copy-paste template for new clients' threshold configs
- `references/example_thresholds.csv` — Fresh Kitchen's threshold CSV as a reference example

## External references (not bundled but linked)

- **Master Sheet:** [Spice Weekly Scorecard Master](https://docs.google.com/spreadsheets/d/1kL39_lOQYsYkUN4h1iZGqdgnkjOu1OfD1SdjI0g2Ajo)
- **Signals DB:** [Spice Weekly Signals](https://app.notion.com/p/b2add89ee6e14ef3ad9811e941515066)
- **Process Guide:** [Process Owner Guide](https://app.notion.com/p/353d3ff018e78165b7d9faa22fda25b3) — the operator's manual
- **Existing skill:** [Delivery Marketplaces | Weekly Reporting Skill](https://www.notion.so/30cd3ff018e781028137de464c4894d8) — produces the inputs this skill consumes

---

## Anti-patterns to avoid

- **Don't create per-client tabs in the master Sheet.** One `data` tab, all clients. Filter by `client_slug` and `week_end`.
- **Don't edit the artifact HTML to hard-code data.** It reads live from the master Sheet on every open. If you need different data, change what's in the Sheet.
- **Don't run the bridge script without --thresholds-csv** if the client has a Notion threshold config. The script falls back to defaults and you'll get wrong status dots.
- **Don't share the master Sheet URL with clients.** Internal-only. Use the static HTML export for client sharing.
- **Don't tune thresholds based on a single bad week.** Wait two weeks, then adjust.
- **Don't add metrics nobody acts on.** If a number lights up red and there's no clear action, kill the metric.

---

## Troubleshooting

- **Artifact won't load data:** Check that Drive MCP is authenticated and the user has read access to the master Sheet.
- **Status dots wrong:** Per-client thresholds CSV missing. Pass `--thresholds-csv` to the bridge script and re-run for the affected week.
- **Per-location ops rows missing:** The bridge script v1 only reads platform-level data. For per-location ops metrics, manually add rows from the W17 recap data tables (DD ops quality, UE accuracy). v2 of the script will read those inputs automatically.
- **Signal not syncing across users:** Each user's artifact is personal but they all read/write to the same Notion Signals DB. If one user can't see another's edit, refresh the artifact.
- **Client export looks unbranded:** Add the client's brand colors to `BRAND_PRESETS` in `scorecard-export.py`.
