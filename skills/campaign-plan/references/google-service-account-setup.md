# Google Service-Account Setup (one-time)

This is the one-time auth so the campaign-plan / scorecard / leaderboard skills can write
directly into Google Sheets in the `spicedigital.co` Workspace. Done once by a Workspace
**admin** (Maxx). ~15 minutes. After this, the team never touches it — they just prompt the skill.

A **service account** is a robot Google identity. The skill logs in as the robot; the robot
has edit access to the client Drive folders. No expiring tokens, no consent popups mid-run.

---

## What you'll end up with
- A service account (e.g. `spice-sheets-writer@<project>.iam.gserviceaccount.com`)
- A JSON key file stored locally (NOT in git, NOT in the skill repo)
- That robot email shared into each client's Drive folder as Editor

---

## Steps

### 1. Create / pick a Google Cloud project
- Go to https://console.cloud.google.com (sign in as a `spicedigital.co` admin).
- Top bar → project dropdown → **New Project** → name it `spice-sheets-writer` → Create.
  (Or reuse an existing Spice project if one exists.)

### 2. Enable the two APIs
- In the project: **APIs & Services → Library**.
- Search **Google Sheets API** → Enable.
- Search **Google Drive API** → Enable.

### 3. Create the service account
- **APIs & Services → Credentials → Create Credentials → Service account**.
- Name: `spice-sheets-writer`. → Create and Continue → Done (skip the optional role steps).
- Copy its email address — looks like `spice-sheets-writer@spice-sheets-writer.iam.gserviceaccount.com`.

### 4. Make a key
- Click the service account → **Keys** tab → **Add Key → Create new key → JSON** → Create.
- A `.json` file downloads. This is the credential. Treat it like a password.
- Move it to: `~/.config/spice/google-sheets-writer.json`
  ```bash
  mkdir -p ~/.config/spice && mv ~/Downloads/<that-file>.json ~/.config/spice/google-sheets-writer.json
  ```
  (The skills read it from this fixed path. Never commit it.)

### 5. Share the client Drive folders with the robot
- For each client, open their Drive folder (e.g. goop's) → Share → paste the service-account
  email from step 3 → give it **Editor** → Send.
- The robot can now create/update Sheets inside that folder. That's the whole permission model:
  it can only touch folders you've explicitly shared with it.

---

## That's it
- One-time. The team never repeats any of this.
- Ongoing, they run a Cowork prompt ("update goop's campaign plan") and the skill writes the Sheet.
- If the key ever needs rotating (rare), repeat step 4 and replace the file — an eng task, not a team one.

## Notes
- **Scope of access:** the robot only sees folders you share with it. It is not a login to your
  whole Drive.
- **Where the key lives:** `~/.config/spice/google-sheets-writer.json`, local to the machine
  running the skill. Not in the repo, not in Notion, not in chat.
- **Per-client wiring:** each `clients/<slug>.json` will gain a `sheet_id` (the persistent Sheet
  the writer updates in place) once the writer is built.
