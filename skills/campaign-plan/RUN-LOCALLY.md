# Running a campaign-plan refresh locally (the Cowork-sandbox workaround)

**Why:** the Cowork cloud sandbox can't reach Google's auth endpoint, so the Sheet write fails
there. Your **own Mac has open network** — running the refresh from local Claude Code CLI (or a
plain terminal) reaches Google fine and writes the live Sheet. Nothing about the pipeline changes;
it's purely *where* the network call originates. (Do NOT enable the org sandbox / allowlist to
"fix" Cowork — it won't reach the container network and it would add restrictions for CLI users.)

## One-time setup (per teammate)
1. **Clone/pull the skills repo** so you have this folder locally.
2. **Get the Google service-account key** from Maxx/Santi and save it to
   `~/.config/spice/google-sheets-writer.json` (or point `SPICE_SHEETS_KEY` at it). This is the
   `spice-sheets-writer@…` key; it must have Editor on the client's Drive folder.
3. **Install deps** into the Python you'll use:
   `python3 -m pip install --user google-api-python-client google-auth openpyxl`
   (or use a venv and set `SPICE_PY=/path/to/venv/bin/python`).

## Weekly run
From this folder, either just ask Claude Code CLI *"refresh the campaign plan for `<client>`"*, or:
```bash
./run_local.sh <client-slug>            # e.g. ./run_local.sh goop-kitchen
./run_local.sh <client-slug> --as-of 2026-06-22
```
It validates the key + deps, runs `references/refresh.py`, writes the live Sheet, and drops the
Slack drafts (client note + internal key-takeaways) in `/tmp/campaign-data-<slug>/` for you to send.

## The durable, hands-off version (later)
Move this to the **Mac Mini** as a shared always-on runner (open network, key installed): the team
triggers a refresh and it executes there — no one needs the key or the CLI locally. Pending the
Mini coming back online + provisioning. Until then, any teammate with the setup above runs it from
their own Mac.
