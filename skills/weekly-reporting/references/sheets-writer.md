# Sheets writer — update the canonical tracker IN PLACE

**Golden rule: edit the ONE canonical tracker. Never create a new spreadsheet, never Drive-copy the tracker.** A per-week copy (`*_W##`) fragments the source of truth and strands plan edits — it is the failure this skill must not repeat. The weekly *snapshot* belongs in the tracker's own **`History` tab**, not a new file.

## Auth
- Service account: `spice-sheets-writer@spice-sheets-writer.iam.gserviceaccount.com`, creds at `~/.config/spice/google-sheets-writer.json`. Each client tracker is shared with it as Editor.
- If the creds file is absent or the SA can't edit the tracker → **stop the in-place write, emit the paste-ready columns, flag it.** Do NOT copy the sheet.

## Setup (system python has no Google libs)
```bash
python3 -m venv /tmp/gs-venv && /tmp/gs-venv/bin/pip install -q google-api-python-client google-auth
```

## Write recipe
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
creds = service_account.Credentials.from_service_account_file(
    "/Users/<user>/.config/spice/google-sheets-writer.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"])
svc = build("sheets","v4",credentials=creds,cache_discovery=False)
SHEET = "<client Campaign Tracker id — registry / Notion Data Dashboard property>"   # goop = 1C75jl5N... ("goop kitchen — Campaign Tracker")

# Campaign Tracker tabs — each updated by its OWN rule (not a single paste column):
# History          → APPEND this week's campaign×location rows (Weekstart, Campaign, Platform, Location, Spend, Sales, Orders, ROAS)
svc.spreadsheets().values().append(
    spreadsheetId=SHEET, range="'History'!A1",
    valueInputOption="RAW", insertDataOption="INSERT_ROWS",
    body={"values": history_rows}).execute()
# Active Campaigns → REPLACE with this week's live campaigns grouped by location (label the week)
# Ads Reporting / Offers Reporting → refresh the "This Week" column (shift prior → Last Week);
#     platform-reported, intentionally differ from the Dashboard's settled figures
# Dashboard / _ChartData → formulas/charts, recompute automatically — DO NOT write
# Q2 / Q3 / Q4 Plan → the campaign PLAN — DO NOT touch
```

## Rules
- **Resolve the canonical sheet ID from the client profile** — never guess, never create.
- **Populate every section**; if a platform export is missing write `n/a`/flag, don't leave a tab half-empty (the W24 bug).
- **Idempotent**: re-running a week overwrites that week's cells; no duplicate rows, no new files.
- `clear()` wipes values but NOT formatting/merges — to fully rebuild a tab, delete+recreate it (version history makes it reversible). For weekly value writes, `values().update` in place is correct.
