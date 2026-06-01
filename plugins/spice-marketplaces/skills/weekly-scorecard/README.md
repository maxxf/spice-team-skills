# Weekly Scorecard Skill — Install & Use Guide

Quick-start for team members who need to spin up the scorecard in their own Cowork session.

## What this skill gives you

- The **live Cowork artifact** — interactive scorecard in your sidebar, multi-client picker, AI Signal drafter, expand-to-platform breakouts
- The **bridge script** — turns weekly-reporting skill outputs into long-format rows for the master Sheet
- The **client export script** — turns master Sheet data into a branded HTML file you can email a client
- Reference templates and per-client examples

## Install (5 minutes per team member)

### 1. Get Cowork access

If you don't have Cowork installed yet, ping Maxx. You need:
- Cowork desktop app
- Drive MCP authenticated (Google account with read access to the master Sheet)
- Notion MCP authenticated (Spice workspace)

### 2. Drop this folder into your Cowork Skills directory

Path: `~/Desktop/Cowork/Skills/weekly-scorecard/`

If you got this as a `.skill` zip, unzip it into the Skills folder. Cowork picks it up automatically on next session.

### 3. Verify install

In a new Cowork conversation, ask: **"show me the scorecard"**. Claude should call `mcp__cowork__create_artifact` and the scorecard should appear in your sidebar within a few seconds.

If it doesn't appear, check that:
- The skill folder is at the right path
- Drive MCP is connected
- You can open the master Sheet manually: https://docs.google.com/spreadsheets/d/1kL39_lOQYsYkUN4h1iZGqdgnkjOu1OfD1SdjI0g2Ajo

## Common workflows

### "Show me the scorecard" (GMs, Santi)

In Cowork, ask: "open the weekly scorecard" or "spin up the scorecard for [client]". Claude creates the artifact in your sidebar.

The artifact:
- Reads live from the master Sheet on every open
- Shows the 5-section format (Money / Efficiency / Operations / Reputation / Discoverability)
- Lets you click any metric to expand the platform breakout (UE / DD / GH)
- Has a "Draft with AI" button on the Signal callout — generates a 2-paragraph read of the week
- Auto-saves the Signal to the Spice Weekly Signals Notion DB on blur

### "Generate scorecard rows for [client]" (Manish, Dulari)

After running the existing weekly-reporting skill, you have `platform_overview.csv` and `by_location.csv` in your output folder. To produce the master Sheet rows:

```bash
python3 ~/Desktop/Cowork/Skills/weekly-scorecard/scripts/generate_scorecard_rows.py \
  --platform-csv path/to/platform_overview.csv \
  --location-csv path/to/by_location.csv \
  --client fresh_kitchen \
  --week-start 2026-04-20 \
  --week-end 2026-04-26 \
  --pulled-by Manish \
  --active-platforms UE,DD \
  --thresholds-csv references/fresh_kitchen_thresholds.csv \
  --output ./scorecard_rows.csv
```

Open the master Sheet's `data` tab, click the first empty row, paste.

### "Send [client] their scorecard" (GM, Client Services Lead)

```bash
python3 ~/Desktop/Cowork/Skills/weekly-scorecard/scripts/scorecard-export.py \
  --csv path/to/scorecard_rows.csv \
  --client fresh_kitchen \
  --week-end 2026-04-26 \
  --output ~/Desktop/Cowork/Clients/Fresh-Kitchen/scorecards/fk-W17.html \
  --signal-file path/to/signal.txt
```

Open the HTML file in your browser to preview. Email or upload to client portal.

### "How do I onboard a new client?"

See the [Process Owner Guide in Notion](https://app.notion.com/p/353d3ff018e78165b7d9faa22fda25b3) for the 6-step checklist.

TL;DR: confirm tracker schema, add row to master Sheet `clients` tab, copy threshold template into client Reporting Profile, create matching CSV in `references/`, backfill 4 weeks, validate.

## Asking for help

- Process / accountability questions → Santi
- Data filling / weekly cadence → Manish or Dulari
- Threshold tuning / Signal callouts → GM for that client
- Bug in the bridge script or artifact → file in `#spice-ops`, Maxx will route

## Last updated

April 30, 2026.
