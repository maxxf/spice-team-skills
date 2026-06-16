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
SHEET = "<canonical tracker id from Notion profile / client registry>"   # e.g. goop = 1C75jl5N...

# 1. Append the OUTGOING week to the History tab BEFORE overwriting current-week cells.
#    (read current-week values, write them as a dated block to 'History')
# 2. Write each section's values into its tab's current-week column, exact row order:
svc.spreadsheets().values().update(
    spreadsheetId=SHEET, range="'Weekly Platform Overview'!<col>2",
    valueInputOption="RAW", body={"values": [[v] for v in ue_values]}).execute()
#    Repeat for DD/GH platform sections and each location block on the location tab.
#    OVERVIEW tabs are formulas — do not write values there.
```

## Rules
- **Resolve the canonical sheet ID from the client profile** — never guess, never create.
- **Populate every section**; if a platform export is missing write `n/a`/flag, don't leave a tab half-empty (the W24 bug).
- **Idempotent**: re-running a week overwrites that week's cells; no duplicate rows, no new files.
- `clear()` wipes values but NOT formatting/merges — to fully rebuild a tab, delete+recreate it (version history makes it reversible). For weekly value writes, `values().update` in place is correct.
