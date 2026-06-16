# GM setup — enabling the live in-place write (one-time, ~10 min)

For the skill to write the tracker **in place** (instead of pasting or making a `_W##` copy), the machine running it needs the service-account key + the Google libs. Do this once per GM machine.

## 1. Service-account key
Get `google-sheets-writer.json` from Maxx via a **secure channel** — 1Password, AirDrop, or a one-time-secret link. **Never Slack or email** (it's a private key). Save it and lock it down:
```bash
mkdir -p ~/.config/spice && chmod 700 ~/.config/spice
# save the JSON to ~/.config/spice/google-sheets-writer.json, then:
chmod 600 ~/.config/spice/google-sheets-writer.json
```

## 2. Update the skill
```
/plugin marketplace update
```
You want **spice-marketplaces ≥ 0.2.4** — that's the version that writes in place (no copies).

## 3. Verify the Sheets API works for you
Libs auto-install on first run, but confirm access now:
```bash
python3 -m venv ~/.spice-venv && ~/.spice-venv/bin/pip install -q google-api-python-client google-auth
~/.spice-venv/bin/python - <<'EOF'
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
c=service_account.Credentials.from_service_account_file(os.path.expanduser("~/.config/spice/google-sheets-writer.json"),scopes=["https://www.googleapis.com/auth/spreadsheets"])
m=build("sheets","v4",credentials=c,cache_discovery=False).spreadsheets().get(spreadsheetId="1C75jl5NBmGjTHOhUcf9Pky9eLzI3uYh4R6JlTT34kZA",fields="properties.title").execute()
print("OK —", m["properties"]["title"])
EOF
```
`OK — goop kitchen — Campaign Tracker` means the API works for you and the tracker is reachable.

## 4. Run it
> "Run weekly reporting for goop Kitchen, week of [Mon] – [Sun]"

Drop in the export files. The skill writes the Campaign Tracker in place per the tab rules in SKILL.md — no copy, no paste step.

## Troubleshooting
- **`FileNotFoundError … google-sheets-writer.json`** → key isn't saved at the path in step 1.
- **`403 / PERMISSION_DENIED`** → that client's tracker isn't shared with `spice-sheets-writer@spice-sheets-writer.iam.gserviceaccount.com` as **Editor**. Ask Maxx to share it (one-time per client).
- **It made a copy / printed paste columns** → you're on an old skill version; re-run step 2.
- **Wrote the wrong sheet** → the client's tracker ID comes from `references/client-registry.md` (Tracker URL) or the Notion `Data Dashboard` property; fix it there.
- **Libs missing at run time** → the skill creates its own venv; if it can't, run the `pip install` from step 3.
