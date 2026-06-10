# Campaign Plan — Per-GM Setup & Weekly Run

How a GM runs the campaign-plan refresh from their own Cowork and gets the exact same sheet
output. One-time setup, then a ~5-minute weekly run.

## One-time setup (per GM machine)

1. **Cowork installed** and signed in.
2. **Notion MCP connected** in Cowork (the skill pulls planned campaigns from the Campaign
   Planning DB). Confirm `/mcp` shows Notion.
3. **Service-account key.** Place the Spice Sheets robot key at:
   `~/.config/spice/google-sheets-writer.json`  then `chmod 600` it.
   Maxx distributes this file securely — do NOT paste it into chat, commit it, or email it.
   It is the same robot for every client (`spice-sheets-writer@spice-sheets-writer.iam.gserviceaccount.com`).
4. **Python deps** (the engine runs Python under the hood). One time:
   `python3 -m pip install --user google-api-python-client google-auth google-auth-httplib2`
   (Python 3.9+.)
5. **Pull the skill:** type `update spice skills` in Cowork.

## Sharing the robot needs (per client — already done for goop)

The service-account email must have access to all three, or the run shows blanks / errors:
- The client's **campaign-plan Google Sheet** (Editor).
- The client's **weekly sales sheet** (Viewer) — source of net sales + store tiers.
- The Drive **`1. Active / <Client> / Campaign Plan Inputs /`** folder (Viewer) — where the
  weekly ad/offer exports go.

## Weekly run (~5 min)

1. **Drop the week's data in Drive.** In `1. Active / <Client> / Campaign Plan Inputs /`, make a
   folder named the **Monday** of the week (e.g. `2026-05-25`) and add:
   - `ads_detail.csv` — `Campaign, Platform, Audience, Location, Impressions, Clicks, Spend, Orders, Attributed Sales`
   - `offers.csv` — `Promotion, Platform, Locations, Audience, Threshold, Discount, Redemptions, Promo Spend, Attributed Sales, New Customers, % New, Status`
2. **Run it in Cowork:** "Run the campaign-plan refresh for `<client>`, week of `<Monday>`."
   The skill pulls planned campaigns (Notion) + the Drive exports + net sales/tiers (sales sheet),
   rewrites every tab in place, runs a QA gate, and writes a Slack draft.
3. **Check QA + the Dashboard.** The run prints `QA: structure valid`. Eyeball the hero tiles.
4. **Ship:** review the Slack draft and send it to the client channel.

## Rules

- Don't hand-edit the skill-owned tabs (Dashboard / Active Campaigns / Ads / Offers) — they're
  rewritten each run. Put strategy + notes in the Q2/Q3/Q4 Plan, Notes & Definitions, or
  Account Learnings tabs (the skill never touches those).
- Re-running the same week is safe (History de-dupes, charts delete-and-recreate).
- New client: add `clients/<slug>.json` (copy goop-kitchen.json), set the sheet id, the
  `net_sales_sheet_id`, and the `location_aliases` map (canonical store names from that client's
  By Location tab).

## Quick troubleshooting

| Symptom | Cause / fix |
|---|---|
| `% metrics show "—"` | Net sales not reachable — share the sales sheet with the robot, or check `net_sales_sheet_id`. |
| `service-account key missing` | Key not at `~/.config/spice/google-sheets-writer.json`. |
| `No module named 'google'` | Deps not installed (step 4) — install into the Python the skill runs. |
| `By Location % blank for a store` | Export location label doesn't map — add it to `location_aliases`. |
| Skill changes not showing | Run `update spice skills` (pulls from GitHub `main`). |
