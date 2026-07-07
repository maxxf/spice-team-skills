# Campaign Plan — run it on your Mac (any client)

**This is the standard way to run a campaign-plan refresh.** It writes to a live Google Sheet,
which needs a Google credential + open network — so it runs from **Claude Code on your own Mac**,
never from Cowork. Cowork's cloud sandbox can't reach your key or Google's network; a Cowork run
now **fails fast and tells you this** instead of erroring silently. (Don't try to "fix" Cowork with
the org sandbox/allowlist — it can't reach the container network and would restrict CLI users.)

Works for **any configured client** — `clients/<slug>.json` (everytable, fresh-kitchen, goop-kitchen,
pret, tiffs-treats, westville today) plus any client you add below. Nothing here is client-specific.

---

## One-time setup (per teammate, ~5 min)

1. **Claude Code CLI on your Mac** (you have it). The skill ships via the plugin — run
   `update spice skills` to be on the latest.
2. **Google service-account key** — get it from Maxx **securely** (password manager / secure
   transfer — never Slack, email, or commit). Save to `~/.config/spice/google-sheets-writer.json`
   and `chmod 600` it. Same robot for every client: `spice-sheets-writer@…`.
3. **Notion token** — also from Maxx, securely → `~/.config/spice/notion-token`. Powers the
   campaign pull (`notion_campaigns_read.py`, raw REST). Without it the refresh can't pull
   planned campaigns headlessly (the MCP query needs a Notion Business plan). *Want to skip the
   whole key dance? Use the Mini path below — no local secrets.*
4. **Python deps** (once):
   `python3 -m pip install --user google-api-python-client google-auth openpyxl`
   (or use a venv and set `SPICE_PY=/path/to/venv/bin/python`).

## Weekly run

In **Claude Code on your Mac**, just say:

> "refresh the campaign plan for `<client>`"

…or run the wrapper directly from the skill folder:

```bash
./run_local.sh <client>                    # e.g. ./run_local.sh fresh-kitchen
./run_local.sh <client> --as-of 2026-06-22 # a specific week (Monday's date)
```

It validates the key + deps, pulls the week's exports from the client's Drive
`Campaign Plan Inputs / <Monday>/` folder + the Notion plan + net sales/tiers, rewrites the live
Sheet in place, runs a QA gate, and drops the Slack drafts (client note + internal key-takeaways)
in `/tmp/campaign-data-<slug>/`. Review and send.

**Zero-setup alternative:** don't want the key + deps on your Mac? Slack the always-on Mac Mini —
**"@Spicy publish the `<client>` campaign sheet"** — it has the key + open network and runs it for
you. Nothing to install.

## Add a new client (one command)

```bash
python3 references/new_client.py --slug <slug> --display-name "<Client Name>" \
  --drive-folder-id <client Drive folder id> --slack-channel '#ext-<slug>-spice'
```

Writes `clients/<slug>.json`, creates the data folder, and (if the key is present) runs the first
refresh — which creates the client's live Sheet and records its id. After that the weekly run works
for them exactly like any other client.

## Share the robot (per client — do once)

The service-account email must have access or the run shows blanks/errors:

- The client's **campaign-plan Google Sheet** — **Editor**
- The client's **weekly sales sheet** — **Viewer** (source of net sales + store tiers)
- Drive **`1. Active / <Client> / Campaign Plan Inputs /`** — **Viewer** (where weekly exports land)

## Rules

- Don't hand-edit the skill-owned tabs (Dashboard / Active Campaigns / Ads / Offers) — they're
  rewritten every run. Put strategy + notes in the Q-Plan, Notes & Definitions, or Account
  Learnings tabs (the skill never touches those).
- Re-running the same week is safe (History de-dupes; charts delete-and-recreate).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `CAN'T WRITE THE LIVE SHEET — key not on this machine` | You're in Cowork, or the key is missing. Run on your Mac; put the key at `~/.config/spice/google-sheets-writer.json`. |
| `No module named 'google...'` | Install deps (setup step 3) into the Python the skill uses (`SPICE_PY`). |
| `% metrics show "—"` | Share the client's sales sheet with the robot, or check `net_sales_sheet_id` in the config. |
| `By Location % blank for a store` | Export label doesn't map — add it to `location_aliases` in `clients/<slug>.json`. |
| Skill changes not showing | `update spice skills` (pulls the latest from GitHub `main`). |
