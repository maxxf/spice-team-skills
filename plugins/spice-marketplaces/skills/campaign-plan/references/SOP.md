# Campaign Plan — Team SOP

**One live Google Sheet per client.** Updates every Monday. Driven by a Cowork prompt — no code.
**Source of truth:** Notion Campaign Planning DB. If a campaign isn't in the DB, it's not in the plan.

---

## Who does what

| Role | Job |
|---|---|
| **GM** (Ro) | Keeps Notion DB current. Author strategy. Trigger Monday refresh. Sign Signal. Lead client meeting. |
| **Ops** (Manish / Dulari) | Sunday night or Monday AM: drop platform exports into the client's Drive folder. |
| **Maxx / eng** | One-time setup, auth, error escalation. Not weekly. |

---

## Cadence — refresh as-needed, communicate Monday

- **Sheet refresh = as-needed.** Trigger when something material moved (campaign hit decline, new test started, launch landed). No fixed "every Monday" rule.
- **Monday = communication day.** GM sends a short Slack note to the client every Monday with this week's plan changes + key moves. Point at the Sheet only if it was refreshed.
- **Friday = GM strategy day.** Update Notion DB statuses. Queue Proposed campaigns. Changes land in Monday's note.

## Weekly loop in practice

### 1. Friday (GM)
Keep the **Notion Campaign Planning DB** current — every campaign logged with the right Status, Segment, Locations, Start/End Date, ROAS Target. If it lands in Client Review, set **Client Review Since**.

### 2. When fresh data is in (Ops, typically Sun night or Mon AM)
Drop the platform exports into the client's Drive folder, **not** as Cowork attachments. The skill reads from there.

**Where:**
```
1. Active / <Client> / Campaign Plan Inputs / <weekstart>/
```
*(Weekstart = the Monday date, e.g. `2026-06-09`. Create the weekstart subfolder if it doesn't exist.)*

**What to drop** (filename = `<platform>_<type>_<weekstart>.csv`):

| File | Where from | Skip if |
|---|---|---|
| `ue_ads_<weekstart>.csv` | `advertiser.uber.com` → Reports → Create report v2 → Campaign Summary by Location | No UE Ads Manager access |
| `ue_offers_<weekstart>.csv` | UE Manager → Marketing → Offers → All Offers → Export | — |
| `dd_ads_<weekstart>.csv` | DD Portal → Marketing → Sponsored Listings → Export | — |
| `dd_offers_<weekstart>.csv` | DD Portal → Marketing → Promotions → All Promotions → Export | — |
| `gh_ads_<weekstart>.csv` | GH Portal → Marketing → Sponsored Listings → Export | No GH paid placement |

All exports = trailing 7 days (Mon → Sun). Full details + required columns in `references/SKILL.md` Phase 1.

### 3. When changes warrant — trigger refresh (GM)
In Cowork:
> **"Update the campaign plan for [client]."**

The skill pulls the campaigns from Notion, downloads your inputs from the Drive folder, refreshes the live Sheet in place, **and produces a Slack draft** for you in Ro's bullet format.

### 4. Monday — communicate (GM)
Review the skill's Slack draft, edit, send to `#ext-[client]-spice`. The Sheet link is stable; the note explains what moved this week.

**Format (Ro's bullet style — 4 bullets max):**

```
Team sharing campaign updates

• **[bold lead-in: key metric/move].** [Context]. [Recommended action].
• **[Specific result].** [Numbers]. [Hold/shift/test directive].
• **[Campaign wrap or launch].** [Numbers + date]. [Backfill or next step].
• **[Strategic decision or upcoming item].** [Deadline or context].
```

Bold lead-in = the headline. Sentence after = numbers + context. End with an active verb (hold, shift, pause, approve, review). Strategist voice, not data dump.

Monthly Store-Ops Leaderboard = first Monday of the month (separate skill, separate cadence).

### Variant prompts (mid-week, granular refreshes)

You don't always need to run the full refresh. The skill supports three variants:

| Prompt | What runs | Use case |
|---|---|---|
| *"Update the campaign plan for [client]"* | Full: Notion pull + Drive pull + render all auto tabs | Standard Monday refresh |
| *"Update the campaign plan **strategy** for [client]"* | Notion pull only → Active Campaigns + Dashboard plan cells. Reporting tabs untouched. | After editing Notion mid-week (status change, new Proposed campaign) |
| *"Update **campaign reporting** for [client]"* | Drive pull only → Ads + Offers + Dashboard performance cells. Plan stays. | New numbers landed, plan hasn't changed |

For tactical mid-week one-off refreshes (rare), *"refresh ads only for [client]"* or *"refresh offers only for [client]"* hits just that tab.

---

## Onboarding a new client

In Cowork:
> **"Set up the campaign plan config for [client]."**

The skill runs `references/new_client.py`, which:
- Writes `clients/<slug>.json`
- **Creates the `Campaign Plan Inputs` folder** in the client's Drive folder (under `1. Active`)
- Runs the first refresh → creates the live Sheet, records `sheet_id`

After this, the client is in the standard weekly loop.

---

## Reading the live Sheet

11 tabs:
- **Dashboard** — headline KPIs, Top/Bottom 5, Decline Alerts, Portfolio Trend, Location Tier
- **Active Campaigns** — every running campaign with WTD performance
- **Ads Reporting** — paid-placement funnel
- **Offers Reporting** — promos + audience split
- **Q2 / Q3 / Q4 Plan** — forward calendar (GM-authored, the skill never touches)
- **Archive** — ended campaigns + hypothesis/outcome
- **Notes** — definitions + status legend + trigger-action rules
- **History** *(hidden)* — append-only weekly snapshots powering Lifetime cols + L4W/L13W trends. Don't edit.
- **Account Learnings** *(GM-authored)* — institutional memory for THIS client: patterns, preferences, failed tests, strategic decisions. Skill never touches. Promoted to global playbooks at QBR.

**Status colors:** 🟢 Live · 🟦 Approved · 🔵 Proposed · 🟠 Blocked-on-client · ⚪ Ended

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Campaign not showing | Not in Notion DB, or wrong Entry Type / Client. Fix in Notion. |
| "Days in queue" blank for Blocked item | Set **Client Review Since** on the Notion row. |
| Performance columns empty on Live campaign | The platform export wasn't in this week's Drive folder, or filename doesn't match. Skill prints unmatched rows — map or add. |
| Ad funnel empty | Drop `*_ads_*.csv` for the platform in the Drive folder. |
| Sheet won't update / auth error | Ping Maxx. Service-account key issue, not something you fix in Cowork. |
| "Where do I find weekstart?" | The Monday of the reporting week (e.g. for the W23 refresh on 6/9, weekstart = `2026-06-09`). |

---

## Hard rules

- **Source of truth = Notion DB.** Never maintain campaigns in side docs or your head.
- **Drop files in Drive, not Cowork attachments.** Persistent + auditable.
- **Don't hand-edit the live Sheet's auto-managed tabs** (Dashboard / Active Campaigns / Ads Reporting / Offers Reporting). The next refresh overwrites them. Change campaigns in Notion.
- **Don't track Meta here.** Marketplace only (UE/DD/GH).
- **Don't share a stale Sheet.** Always run the refresh before posting the heads-up.

---

*Full architecture, strategy playbooks, and per-tab input map: `references/SKILL.md`.*
