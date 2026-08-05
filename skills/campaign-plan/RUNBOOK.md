# Campaign Plan — the Runbook

**This is the one true document for running campaign reporting.** One live Google Sheet per
client, refreshed by whoever is on it that week. If something here disagrees with an older doc,
this one wins — `references/SOP.md` and `RUN-LOCALLY.md` are retired pointers to this file.

**Source of truth for campaigns is the Notion Campaign Planning DB.** If a campaign isn't in the
DB, it doesn't exist as far as the Sheet is concerned.

Four sections, in the order you'll need them: [one-time setup](#1-one-time-setup),
[the weekly run](#2-the-weekly-run), [adding a client](#3-adding-a-client),
[troubleshooting](#4-troubleshooting).

---

## Where this runs, and where it doesn't

Run it from **Claude Code on your own Mac**, or from a terminal on your own Mac. That's the
supported path. There is one thing to know before you try anything else:

**Cowork cannot run this.** The refresh writes to a live Google Sheet, which needs a Google
credential and an outbound network connection to Google's OAuth endpoint. Cowork's cloud sandbox
has neither. A Cowork run now fails fast and tells you so rather than half-finishing. Don't try to
fix this with the org sandbox or an allowlist — the sandbox can't reach the container network, and
changing it would restrict everyone on the CLI. Cowork is fine for editing Notion and reading the
Sheet; it cannot write the Sheet.

**The Mac Mini is not a supported path.** It was announced as a shared runner twice, on 2026-07-01
and again on 2026-07-07, and was never validated. Its weekly job failed every single week from
April 12 through July 21 before the job was killed. If someone tells you to "just Slack the Mini,"
that is folklore, not a runbook step. Use your own Mac.

**Santi's `run_campaign_refresh.sh` is retired.** For a stretch, the only reliably working path was
a shell script on one person's Desktop, which meant nobody else could run a refresh and nobody
could review what it did. Everything it did is now in `run_local.sh` and `references/provision.py`,
both of which live in the skill. If you still have a copy on your Desktop, delete it — it predates
the HQ config move and the preflight gate, and running it will skip both.

---

## 1. One-time setup

About five minutes, once per person.

**1. Claude Code on your Mac.** Run `update spice skills` to make sure you're on the current
version of the skill.

**2. Python with the Google libraries.** The skill needs three packages:

```bash
python3 -m pip install --user google-api-python-client google-auth openpyxl
```

If you'd rather keep them out of your system Python, use a virtualenv and point the skill at it
by exporting `SPICE_PY=/path/to/venv/bin/python`. That variable is how the skill finds a Python
that has what it needs, so if you use a venv, put the export in your shell profile — otherwise
every run needs it set by hand.

**3. Two credentials — from HQ secrets. Nothing to install, nothing to hand over.**

Both live in HQ and get injected for the length of a single command. Ask Maxx to grant you
read access once, then prefix any run with `hq secrets exec`:

```bash
hq secrets exec --company spice \
  --only SHARED/GOOGLE_SHEETS_WRITER \
  --only SHARED/NOTION_CAMPAIGN_PLAN \
  -- ./run_local.sh <client>
```

| Credential | HQ path | What it powers |
|---|---|---|
| Google service-account key | `SHARED/GOOGLE_SHEETS_WRITER` | Reading Drive inputs and writing the client Sheet |
| Notion token | `SHARED/NOTION_CAMPAIGN_PLAN` | Pulling planned campaigns from the Campaign Planning DB |

The Google robot is the same for every client (`spice-sheets-writer@…`) — there is no
per-client key. If a run says the credential is missing, you don't have the grant yet; ask
Maxx rather than hunting for a key file.

**Key files still work as a fallback.** If you already keep the key at
`~/.config/spice/google-sheets-writer.json` and the token at `~/.config/spice/notion-token`,
those are still read, and `chmod 600` both. HQ secrets take priority when present, so an
injected credential always beats a stale local copy. Never put either in Slack, in email, or
in a commit.

**4. Verify before you trust it.** Don't discover a broken setup halfway through a client refresh:

```bash
python3 references/doctor.py
```

The doctor checks your credential, your Python deps, config resolution, the Notion token, and then
every client's Drive folder, campaign Sheet, and weekly tracker. It names the exact fix for each
failure. Green here means a refresh will work. It exits 0 when everything passes, 1 when any client
fails, and 2 if the doctor itself broke.

---

## 2. The weekly run

### Who does what

| Role | Job |
|---|---|
| **GM** (Ro) | Keeps the Notion DB current. Authors strategy. Triggers the refresh. Sends the Monday client note. Leads the client meeting. |
| **Ops** (Manish / Dulari) | Sunday night or Monday morning: drop the platform exports into the client's Drive folder. |
| **Maxx / eng** | One-time setup, credentials, escalation. Not part of the weekly loop. |

### Cadence

The **sheet refresh is as-needed**, not a fixed Monday ritual — trigger it when something material
moved: a campaign hit decline, a test started, a launch landed. **Monday is communication day**: the
GM sends a short Slack note to the client every Monday regardless, and links the Sheet only if it was
actually refreshed. **Friday is GM strategy day**: update Notion statuses, queue Proposed campaigns,
and those changes show up in Monday's note.

Never share a stale Sheet. Refresh first, then post.

### Step 1 — Ops drops the exports in Drive

They go in the client's Drive folder, **not** as Cowork attachments — Drive is persistent and
auditable, and the skill reads from there:

```
1. Active / <Client> / Campaign Plan Inputs / <weekstart>/
```

`weekstart` is the **Monday** of the reporting week, as `YYYY-MM-DD` — so the refresh you run on
Tuesday 2026-07-28 for the prior week uses `2026-07-20`. Create the weekstart subfolder if it isn't
there yet.

All exports cover the trailing 7 days, Monday through Sunday:

| Export | Where it comes from | Skip when |
|---|---|---|
| Uber Eats ads | `advertiser.uber.com` → Reports → Create report v2 → **Campaign Summary** | No UE Ads Manager access |
| Uber Eats offers | UE Manager → Marketing → Offers → All Offers → Export | — |
| DoorDash ads | DD Portal → Marketing → Sponsored Listings → Export | — |
| DoorDash offers | DD Portal → Marketing → Promotions → All Promotions → Export | — |
| Grubhub ads | GH Portal → Marketing → Sponsored Listings → Export | No GH paid placement |

**Filenames don't matter.** The skill recognizes exports by their column signature, not their name,
so platform-default filenames are fine. What matters is dropping the *right* export: for Uber Eats
ads it needs the per-campaign **Campaign Summary**, and the by-location summary won't work — the
input gate will tell you so by name if you get it wrong.

### Step 2 — Run the refresh

From Claude Code, say:

> "refresh the campaign plan for `<client>`"

Or run it directly from the skill folder:

```bash
./run_local.sh <client>
```

For a specific week, pass the Monday:

```bash
./run_local.sh <client> --as-of 2026-07-20
```

**See exactly what would change without writing anything:**

```bash
./run_local.sh <client> --dry-run
```

Use `--dry-run` any time you're unsure. It renders the full diff for every tab and writes nothing.
There is no reason not to run it first on a client you haven't done before.

What a run actually does, in order: checks your key and deps, runs the preflight doctor, pulls this
week's exports from Drive, validates them, pulls the plan from Notion, pulls net sales and store
tiers, snapshots each tab it's about to touch, rewrites the live Sheet in place, runs a QA gate, and
drops two Slack drafts — the client note and the internal key-takeaways — into
`/tmp/campaign-data-<slug>/`. Review those before sending; they are drafts, not outbound messages.

The Drive pull reuses files it already downloaded for the same week, so a second run costs a couple
of seconds instead of re-downloading everything. Re-running the same week is safe in general —
History de-dupes and charts are recreated rather than duplicated.

**Useful flags:**

| Flag | When you want it |
|---|---|
| `--dry-run` | See every change as a diff, write nothing |
| `--as-of YYYY-MM-DD` | Refresh a specific week (pass that week's Monday) |
| `--no-drive-pull` | Skip Drive entirely and use whatever is already in the local data dir — the escape hatch when Drive is the problem or you were handed files directly |
| `--force-drive-pull` | Re-download every input, ignoring what's cached from an earlier run this week (use when someone re-uploaded a file) |
| `--no-push` | Build the workbook file only, don't touch the live Sheet |
| `--skip-doctor` | Bypass the preflight gate. Debugging only — the gate exists because silent failures cost real runs |
| `--force-inputs` | Publish despite the input gate's objections. Only when you know the objection is wrong |
| `--force-shrink` | Allow a large row-count drop, when the shrink is genuine (campaigns ended, locations closed) |

The last three override safety gates. If you find yourself reaching for them routinely, something
upstream is broken — say so rather than making the override a habit.

### Step 3 — Monday, send the note

Take the skill's Slack draft, edit it, send it to `#ext-<client>-spice`. The Sheet link is stable;
the note explains what moved.

Ro's format, four bullets maximum:

```
Team sharing campaign updates

• **[bold lead-in: the key metric or move].** [Context]. [Recommended action].
• **[Specific result].** [Numbers]. [Hold / shift / test directive].
• **[Campaign wrap or launch].** [Numbers + date]. [Backfill or next step].
• **[Strategic decision or upcoming item].** [Deadline or context].
```

The bold lead-in is the headline; the sentence after it carries the numbers. End each bullet on an
active verb — hold, shift, pause, approve, review. Strategist voice, not a data dump.

The monthly Store-Ops Leaderboard is a separate skill on a separate cadence — first Monday of the
month.

### Partial refreshes

You don't always need the whole thing:

| Ask for | What runs | Use when |
|---|---|---|
| "Update the campaign plan for `<client>`" | Everything | The standard refresh |
| "Update the campaign plan **strategy** for `<client>`" | Notion pull only → Active Campaigns + Dashboard plan cells. Reporting tabs untouched. | You edited Notion mid-week |
| "Update **campaign reporting** for `<client>`" | Drive pull only → Ads + Offers + Dashboard performance cells. Plan untouched. | New numbers landed, plan didn't change |

For a one-off, "refresh ads only for `<client>`" or "refresh offers only for `<client>`" hits just
that tab.

---

## 3. Adding a client

One command, and it's safe to run more than once:

```bash
python3 references/provision.py --slug <slug> --display-name "<Client Name>" \
  --drive-folder-id <client Drive folder id>
```

**Always run `--check` first** to see what it would do before it does it:

```bash
python3 references/provision.py --slug <slug> --check
```

Provisioning validates that the robot can write the client's Drive folder, creates a **native Google
Sheet** in that folder if one isn't already there, ensures the 11 canonical tabs exist, creates the
`Campaign Plan Inputs` folder, finds the client's weekly tracker and detects its actual tab names,
writes the config into HQ, and finishes by running the doctor.

Two things worth knowing about why this is simpler than it used to be:

**There is no Share step.** Client folders live in a shared drive, so a Sheet created inside one is
already reachable by the robot through drive membership. If you ever find yourself needing to share
a file with `spice-sheets-writer@…` by hand, that's the signal the file was created in the wrong
place — a personal My Drive instead of the client folder. Fix the location; don't paper over it with
a permission grant.

**It reads real tab names instead of guessing.** Client trackers aren't consistent — goop's is
`By Location 2.0`, Tiff's is `By Location`. Provisioning detects the actual names, because a wrong
guess makes the join return nothing rather than failing loudly.

`references/new_client.py` still works but is now just a thin wrapper over `provision.py`, kept so
old muscle memory and old docs don't break. There's one provisioning path.

---

## 4. Troubleshooting

**Start here for anything unexplained:**

```bash
python3 references/doctor.py --client <slug>
```

Most failures are a setup problem the doctor can name in one line.

### If a write went wrong

Every destructive write is snapshotted to local disk *before* the tab is cleared, so a bad write is
recoverable without digging through Google's version history:

```bash
python3 references/write_guard.py list    --sheet-id <id>                 # snapshots for that Sheet
python3 references/write_guard.py list    --sheet-id <id> --tab <tab>     # narrow to one tab
python3 references/write_guard.py show    --sheet-id <id> --tab <tab>     # inspect the newest
python3 references/write_guard.py restore --sheet-id <id> --tab <tab>     # roll it back
```

The Sheet id is the long string in the Sheet's URL between `/d/` and `/edit`. It's also in
`clients/<slug>.json` as `sheet_id`.

`restore` takes the newest snapshot by default; `--at <timestamp>` picks an older one, and `--yes`
skips the confirmation prompt. It snapshots the current state before restoring, so a restore is
itself reversible. Google's own version history remains the deeper backstop — these snapshots exist
because they're faster and scriptable.

This machinery is here for a specific reason: on 2026-06-16 the first live run wrote goop's Sheet
blank, and it was only recovered because a person happened to notice. That class of failure is now
gated, but the snapshots are the seatbelt.

### Common symptoms

| Symptom | What's actually wrong |
|---|---|
| `CAN'T WRITE THE LIVE SHEET — key not on this machine` | You're in Cowork, or you have no credential. Run on your Mac, under `hq secrets exec` (setup step 3). |
| `No module named 'google...'` | The Python being used doesn't have the deps. Install them, or set `SPICE_PY` to one that does. |
| `No Google service-account credential` | You don't have the HQ grant yet, or you forgot the `hq secrets exec` prefix. Setup step 3. |
| `429 ... Quota exceeded ... Read requests per minute` | You ran several clients back to back and hit Google's 60-reads-per-minute cap. Wait a minute and re-run — nothing is broken and nothing was half-written. |
| Refresh refuses to publish, lists inputs | The input gate. Read what it names — usually a missing export or the UE by-location file instead of Campaign Summary. Fix the file in Drive and re-run; `--force-inputs` only if the gate is genuinely wrong. |
| `no 'Campaign Plan Inputs / <date>/' folder yet` | Ops hasn't dropped this week's files, or the weekstart date is wrong. It's the **Monday** of the reporting week. |
| Campaign missing from the Sheet | It's not in the Notion DB, or has the wrong Entry Type / Client. Fix it in Notion. |
| "Days in queue" blank on a Blocked item | Set **Client Review Since** on the Notion row. |
| Performance columns empty on a Live campaign | That platform's export wasn't in this week's folder. The skill prints unmatched rows. |
| `%` metrics showing `—` | The robot can't read the client's weekly sales sheet, or `net_sales_sheet_id` in the config is wrong. |
| `By Location` blank for one store | The export's store label doesn't map. Add it to `location_aliases` in `clients/<slug>.json`. |
| A tab looks wrong after a run | Snapshot restore, above. Then figure out why. |
| Skill changes not showing up | `update spice skills`. |

### Escalate to Maxx when

The doctor is green, the inputs are right, and it still fails — or anything involving credentials.
Don't spend an afternoon on an auth error; that's an eng problem, not a run problem.

---

## Hard rules

- **Notion DB is the source of truth for campaigns.** Not side docs, not your head.
- **Exports go in Drive, not Cowork attachments.**
- **Don't hand-edit the auto-managed tabs** — Dashboard, Active Campaigns, Ads Reporting, Offers
  Reporting. The next refresh overwrites them. Strategy and notes belong in the Q-Plan, Notes &
  Definitions, or Account Learnings tabs, which the skill never touches.
- **Marketplace only.** No Meta here — UE, DD, GH.
- **Never share a stale Sheet.** Refresh, then post.
- **Never put a credential in Slack, email, or a commit.**

---

## Reading the live Sheet

Eleven tabs:

- **Dashboard** — headline KPIs, Top/Bottom 5, Decline Alerts, Portfolio Trend, Location Tier
- **Active Campaigns** — every running campaign with week-to-date performance
- **Ads Reporting** — paid-placement funnel
- **Offers Reporting** — promos and audience split
- **Q2 / Q3 / Q4 Plan** — forward calendar, GM-authored, never touched by the skill
- **Archive** — ended campaigns with hypothesis and outcome
- **Notes** — definitions, status legend, trigger-action rules
- **History** *(hidden)* — append-only weekly snapshots powering the Lifetime columns and L4W/L13W
  trends. Don't edit it.
- **Account Learnings** *(GM-authored)* — institutional memory for this client: patterns,
  preferences, failed tests, decisions. Promoted to global playbooks at QBR.

Status colors: 🟢 Live · 🟦 Approved · 🔵 Proposed · 🟠 Blocked-on-client · ⚪ Ended

---

*Architecture, strategy playbooks, and the full per-tab input map: `SKILL.md`.*
