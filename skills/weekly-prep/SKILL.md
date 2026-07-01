---
name: weekly-prep
description: Sunday-evening operating brief for Maxx that feeds Monday's team standup; plus a Monday "push to standup" sync (Part 4). Trigger on "weekly prep", "prep for the week", "Sunday prep", "get ready for Monday", "push prep to standup", "fill the standup", "Monday standup sync". An action-first operating brief driven off the live CRM, Circleback, Gmail, and Stripe — NOT a newsletter or status digest.
---

# Weekly Prep (Operating Brief)

Generate Maxx's Sunday operating brief by pulling from Circleback (meetings/calendar), Notion (Sales Pipeline + Task Tracker + onboarding), Gmail, and Stripe, then synthesizing into a tight, triaged, action-first brief plus paste-ready standup blocks.

**This is an operating brief, not a status report.** Every line either tells Maxx what to do or gives him the one fact he needs to decide. If a line does neither, cut it.

## Data provenance — the rule that makes this brief trustworthy (READ FIRST)

A brief that *looks* complete but runs on stale data is worse than a short honest one — it gets acted on. So:

- **Every fact is live, or it is labeled.** If you couldn't read a source this run, say so loudly — `[SOURCE] UNAVAILABLE — [next step]` — and name the specific unread item: `[Deal] — unread, check manually`. Never let last week's numbers stand in as this week's.
- **Never emit a false "clean."** "AR clean", "no churn", "nothing overdue" are allowed *only* when you actually read the source and it was empty. A failed read is `UNAVAILABLE`, never `clean`.
- **Banned hedge language** (tells of faked completeness): *"verified subset", "confirm in CRM", "runs clean on the live job", "per the [date] baseline", "layered on the baseline".* If you catch yourself writing one, the underlying read failed — fix the read or flag it unread.

## Runtime + hard guardrails

- Runs on the **Mac Mini (Spicy Nugget), Sunday evening. STAGE ONLY** — never auto-post to Slack or the standup doc. Maxx reviews first.
- **Never source from the "Spice Team Weekly Standup" meeting or page.** This brief feeds INTO the standup; sourcing from it is circular. (Reading its *structure* to map output blocks is fine; reading its *content* as data is banned.)
- **Active team members only.** Never credit anyone departed (see roster step).

## Step 0: Context (light — context only, never metrics)

Vault (for Maxx's current priorities, feeds §1 triage only):
- Path (resolve under whichever user runs it): `$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Vault/` → read `00-home/hot.md` + `00-home/top-of-mind.md`. On the Mac Mini (user `spicy`) this iCloud vault is usually ABSENT — that's expected, not an error.
- If that path isn't mounted (headless Mac Mini iCloud often isn't), try the `obsidian-vault` MCP. If neither works, **proceed without it and note "vault context unavailable"** — do not block, do not invent. **Never source metrics from the vault** (MRR etc. come from Stripe).

Roster (source of truth — verify, don't hardcode from memory):
- Confirm the active roster against Notion + `CLAUDE.md` before crediting anyone.
- **Departed (no credit): Cesar, Rui, Tomas.** Roster changes — re-verify each run; if a status is ambiguous, check before crediting or omitting.

Date math: Monday = tomorrow. "Last week" = previous Mon–Sun. "This week" = upcoming Mon–Fri.

---

## Part 1 — Data Sourcing

### Reading Notion databases — use the REST reader (the workspace can't be queried via MCP)

This Notion plan has **no working MCP query path**: `notion-query-data-sources` is Enterprise-gated, `notion-query-database-view` is Business-gated, `notion-fetch` on a DB returns schema only, and `notion-search` over a source is a lossy semantic sample that **silently drops rows** (verified: it missed both of one week's booked deals). So read DBs with the reader:

1. **PRIMARY — run the reader.** The Mac Mini already exports `NOTION_TOKEN`, so this just works:
   ```
   python3 tools/notion_db_read.py <pipeline|tasks|content|onboarding>
   ```
   (path is relative to this skill's folder). Exit 0 → JSON `{db,count,rows}` with real field values; use it. Add `--filter '<notion filter json>'` to scope server-side.
2. **FALLBACK — only if the reader exits 3 (NO_TOKEN) or 5 (API/sharing error).** Then use search-enumerate: `notion-search` with `data_source_url=<collection>`, `page_size=25`, `max_highlight_length=0` → page IDs → `notion-fetch` each by ID. **This is KNOWN-LOSSY** (drops rows), so cross-catch new items from calendar/Circleback/Gmail, tag anything unconfirmed `— unread, check manually`, and **state in the brief that the read ran in fallback mode.** (Exit 5 usually means the integration isn't shared with that DB — flag it for the token checklist.)
3. Never guess a field you couldn't read. Unread = say unread.

### 1. Calendar (coming week)
`SearchCalendarEvents: startDate=[Monday], endDate=[+7 days], pageIndex=0` — feeds Top Priorities, surfaces sales calls, client meetings, conflicts. No standalone calendar table in the output.

### 2. Meeting notes (last 7 days)
`SearchMeetings: startDate=[7 days ago], endDate=[today], pageIndex=0`; `ReadMeetings` for every client meeting. Extract: wins (with metrics, attributed to the account owner), open action items (what's due, who owns), churn signals, onboarding progress.

Cover ALL clients, not just ones Maxx attends — goop, Capriotti's, Dayglow/AWAN, Everytable, Teleferic, MBFS, Counter Service, Menya Ultra, Temaki, Gertie, Fresh Kitchen, Westville, retention clients (HealthNut, AhiPoki, MBF), plus anyone in onboarding. Also pull the Retention Biweekly. **Exclude the Spice Team Weekly Standup** (circular — see guardrails).

### 3. Onboarding status — delegate to `onboarding-status-check` (do NOT hand-derive from meetings)
Read the onboarding DB: `python3 tools/notion_db_read.py onboarding`. Run only the **read + categorization** logic of `onboarding-status-check`:
- Incomplete tasks (`Status` ≠ Done, has a `Client`); each task's `Due Date` (formula) or compute from `Days After Start` + the client's start date.
- Categorize: 🚨 **Blocker** (5+ days late) / 🔴 **Overdue** (3–4) / ⚠️ **At Risk** (due today/tomorrow or 1–2 past) / ✅ **On Track**. Include the stale-task check (3+ days late still "Not Started").
- **READ-ONLY here** — no form/credential migration, no marking tasks Done, no Slack posts. Weekly-prep only consumes status.

### 3b. Active-client context (Notion)
For active (non-onboarding) clients, look for meeting-note pages from the last 7 days and team-logged decisions/blockers. Cross-reference with meeting notes — Notion may lag reality.

### 4. Sales Pipeline — read it correctly (the section that breaks; follow exactly)
1. **Read it via the reader:** `python3 tools/notion_db_read.py pipeline` → active deals only (New Lead → Agreement Sent), each with real `Deal stage`, `Deal value`, `Locations`, `Last contact date`, `Account owner`, `Notes`. (Fallback per the reader doctrine if it exits 3/5 — and say so.)
2. **Ground truth = the CRM `Deal stage` field. Never infer stage from Circleback or Gmail.** Use calls/emails only to ADD next-step context. If an email implies a different stage than the CRM, report the CRM stage and append `⚠️ CRM says X; [date] email suggests Y — update CRM`.
3. **Stage handling:** active = {New Lead, Reached Out, Qualified, Meeting Booked, Pitched, Proposal Shared, Agreement Sent}. **"Agreement Sent" is NOT "Won."** Won → list under "Recently Won → onboarding" and cross-check Stripe/P&L that billing started (a Won with no contact + no billing → `verify`). Lost/Not a Fit → one line only if it moved this week. Ice Box → omit unless reactivated.
4. **Stale flag:** days since `Last contact date`; any active deal >14 days → `⏳ N days quiet` and onto the chase list.
5. **Data hygiene to Maxx, not the doc:** junk/dupe/test rows (e.g. `[DUPE - DELETE]`) or "Won" rows reading as un-closed go in the **chat summary to Maxx, NOT the Notion doc.** Never include junk rows in the pipeline list.
6. **No hedges** (see provenance rule). If a deal genuinely couldn't be read: `[Deal] — unread, check manually`.

### 5. Gmail signals (last 7 days)
Catch async movement that never reaches Circleback:
```
newer_than:7d (from:client-domains…)                              # decisions, blockers, asks between meetings
newer_than:7d (proposal OR agreement OR onboarding OR invoice)    # deal/contract status
newer_than:7d (hiring OR contractor OR interview OR offer)        # team pipeline
```
Email is more recent than meeting notes — where they conflict, email wins for facts, but the CRM still wins for deal stage (§4).

### 6. AR + MRR (Stripe) — exact verified method
**AR — pull open invoices:** `stripe_api_read` operation **`GetInvoices`** with `{"status":"open"}` (paginate; the list returns `has_more`). Read **directly off each invoice object**: `customer_name`, `amount_remaining`, `due_date`, `collection_method`, `number`.
- Keep only `amount_remaining > 0`. **Overdue** = `due_date` in the past.
- `due_date` null + `collection_method` = `charge_automatically` → **auto-charge not clearing** (ops fix: needs payment method), report separately from `send_invoice` chases.
- Flag any client about to be scrutinized on spend who also owes — they pay first.
- **NEVER call `stripe_api_execute` (it does not exist)** — that exact bug made past briefs falsely report "Stripe not connected." If `GetInvoices` ever errors, rediscover via `stripe_api_search "list invoices"` then `stripe_api_read`. If Stripe is genuinely unreachable, emit **`AR UNAVAILABLE — verify Stripe MCP on the Mac Mini`**, never "AR clean."

**MRR (compute from Stripe — do NOT use the vault/P&L estimate; it runs ~$10K high and stale):**
- Discover the subscriptions op via `stripe_api_search "list subscriptions"` → `stripe_api_read`. Sum active/trialing subs, annual ÷ 12.
- **Also count recurring `send_invoice` subscriptions** that sit in `past_due`/non-active (goop, Capriotti's, etc. bill net-30 — a naive `status=active` query MISSES ~$15K). Include clearly-recurring service fees even when delinquent; note the delinquent portion.
- Note CAD subs (BKDS group) — state whether counted nominally or converted.
- Report **Total MRR + gap to $100K**, with the subscription / recurring-invoice split and past-due amount. (Reference only, Jun 2026: ~$64K subs + ~$15.5K recurring = ~$79.5K, ~$20.5K to goal — verify, don't reprint.)

### 7. Churn scoring
Score every active client 0/1/2 on five dimensions — **Pay** (late/disputed billing), **Eng** (responsiveness, attendance, POC churn), **Perf** (sales/conversion/rating trend), **Ops** (platform/menu/campaign blockers), **Rel** (lead changes, tension). Total /10 → 🔴 High (6+), 🟡 Monitor (3–5), Healthy (0–2). Compare to last week's prep (fetch the prior archive page) and note score changes + why. Surface only clients scoring 3+.

---

## Part 2 — Output Format

Section order is fixed. **Length budgets are hard caps.** Enforce the **one-mention rule**: each client/deal lives in exactly ONE section; reference it elsewhere by name only ("see §1"), never re-describe its metrics.

Open with one italic source line: dates pulled, sources used, standup excluded, departed excluded from credit, and **any source that ran in fallback / was unavailable** (provenance).

**Output hygiene (copy-paste-ready):**
- **One representation per dataset** — never the same data as both a table and a list.
- **No auto-link bait** — Notion auto-links bare domains/emails into ugly live links; reword ("your e-sign queue", "vendor/no-reply contacts") or drop. Keep only intentional `[label](url)` links to real Notion/Circleback pages.
- **Title = one icon** — the archive page already has 📋; don't prefix another.
- **Cross-ref, don't repeat.**

### 1. Top Priorities This Week (triaged)
Start from **Maxx's actual open tasks** — `python3 tools/notion_db_read.py tasks`, then keep rows where `Owner` includes Maxx and `Status` ∈ {Not started, In progress, Blocked, On Hold}, sorted by `Due date`. Triage: overdue, due this week, high-leverage, or **should be reassigned** to a GM/Ops lead. Then layer §2–§7 + vault top-of-mind + the coming week's calendar to catch anything not yet ticketed.
- Commit to the **5 highest-leverage things only Maxx can move** (closes, escalations, churn saves, key decisions, content he must record — not GM execution). One line each: the move, the one number that justifies it, the deadline. Link the actual Notion task where one exists; mark `(not ticketed)` if not.
- **Balance rule (enforce every week):** the 5 must not be all defense. Include **≥1 offense** (net-new revenue: a live prospect call / open proposal to push) and **≥1 build** (Spice Agent / product / systems that remove Maxx). Verify deal stage off the CRM (§4) before calling something offense — a **Won** deal is booked revenue, not a close.
- If the tasks read ran in fallback, say "§1 candidates from signal, not the tracker."

**Decisions waiting on you** — ≤6 items, one line each; calls only Maxx can make. Don't repeat a priority above.

**AR / cash flag** — from §6. One line per unpaid invoice (or the `AR UNAVAILABLE` flag).

### 2. Sales Pipeline Review
From §4. Grouped by stage, bullets (no tables). Skip empty stages. One italic line noting it's driven off the live CRM `Deal stage` field (or fallback mode).
```text
**Meeting Booked**
- **[Deal]** ([owner], [N loc], $[value]) — [next step + date]. [⏳ if stale]

**Pitched / Proposal Shared / Agreement Sent**
- **[Deal]** ([owner]) — [context]. Next: [action]. [⏳ if stale]

**Recently Won → onboarding**
- [Deal list] — billing confirmed via Stripe/P&L. [verify flags if any]

**Chase this week:** [stale + high-value deals, named].
```
Keep CRM cleanup / data-quality notes OUT of the doc (those go to Maxx in chat — §4 step 5).

### 3. Content Pipeline Review
Read the content DB: `python3 tools/notion_db_read.py content`. Output: (a) what's scheduled to publish this week (`Status` = Scheduled/Approved, `Publish Date` in the week) with links, (b) up to 3 *new* post-worthy topics from recent client work (fresh ideas or `Pillar` = Source Material), one line each with a timely angle. ~8 lines.

### 4. Team Highlights — last week
One line per **active** member: the single best thing they shipped, with a metric. Include EVERY active teammate (someone being transitioned out is still active — neutral line; only the *departed* are omitted). Cross-check the roster so no one is silently dropped. End with one "client performance wins" line for results not tied to one person.

### 5. Onboarding Updates
New-client onboarding only, **sourced from §3 (the onboarding DB read), not meeting notes.** Lead with the real category totals: 🚨 Blockers / 🔴 Overdue / ⚠️ At Risk / ✅ On Track. One line per active onboarding: the gating task, its category, the owner to tag, the next concrete step. Recently-won-but-not-yet-onboarding = a single roll-up line.

### 6. Client Churn Risk
**One scored bullet per client — no separate table:** `🔴/🟡 **Client (score)** — issue + owner + this-week move`. 🔴 High (6+) first, then 🟡 Monitor (3–5); only 3+ shown. If also a §1 priority, write `see §1`. Note score changes vs last week. End with `Lost:` if any.

### Standup Summary — copy/paste (formatted, NOT code blocks)
The one intentional consolidation (its job is to be pasted into the standup doc). Render as **real formatted content** — proper sub-headings + bullet/numbered lists — NOT inside code fences. Use the standup's exact section names as `###` sub-headings, in order:
- **MRR / Goal** → one bold line: the **Stripe-computed** MRR (§6) + RAG dot + gap to $100K. Never the vault estimate.
- **`### Pipeline Updates`** → bullets: **Recently Won** / **Proposal Shared** / **Meeting Booked** / **Pitched** / **Chase**.
- **`### 🏆 Big Wins This Week (All)`** → numbered list, top 5, `win — owner`.
- **`### Onboarding Updates`** → counts + the one client needing attention.
- **Churn Risk** (bold sub-label) → **Red** / **Watch** / portfolio health / Lost.

Names-and-numbers, not sentences. Skip any block that maps to nothing rather than inventing a target.

---

## Part 3 — Output, staging, notify (Mac Mini)

1. Build the brief as markdown.
2. **Save a workspace copy:** `$HOME/Desktop/Cowork/Clients/_Internal/Weekly-Prep/Weekly-Prep-[YYYY-MM-DD].md` (`mkdir -p` the dir first; works as `maxx` on the laptop or `spicy` on the Mac Mini).
3. **Write to the Command Center "Weekly Prep Archive"** (data source `collection://47524728-ae68-4019-a793-0a1032495061`). Title: `📋 Weekly Prep | [Mon date] - [Fri date], [Year]` — exactly one 📋. If a page exists for this week, update it; else create under the archive. Use **real newlines, never literal `\n`**. (Legacy fallback only if the Archive is unreachable: "Maxx - Scratchpad" `1d0d3ff0-18e7-805d-8802-fd9baee89737`.)
4. **STAGE ONLY** — do not post to Slack or the standup. Surface the Notion link to Maxx.
5. **iMessage notify** (Mac Mini, no connector needed) — one line: the single most important thing + the Notion link:
   ```bash
   osascript -e 'tell application "Messages" to send "📋 Weekly Prep ready: [1-line headline]. Review: [Notion URL]" to buddy "maxx@spicedigital.co" of (service 1 whose service type is iMessage)'
   ```
   If the send fails (Messages not signed in), note it and continue — don't block the brief.

---

## Part 4 — Standup Sync (run Monday morning, separate step)

Trigger: "push prep to standup", "fill the standup", "Monday standup sync", or the Monday schedule. **Run AFTER the standup instance spawns (~9am Mon) — never Sunday.** Source = the latest Weekly Prep page in the archive (`collection://47524728-ae68-4019-a793-0a1032495061`). Target = this week's standup instance.

The standup doc "🌶️ Spice | Weekly Standup" is a row in **DB: Team Meetings** (`collection://1ced3ff0-18e7-8088-820b-000b9f3c0729`), auto-spawned each Monday from a template (`1ced3ff018e780f1a66ce1e554093ff3` — reference only, NEVER write to it).

1. **Find the target:** the row with `Category = Standup` and `Date` = this week's Monday (or `notion-search "Spice Weekly Standup"`, newest). Confirm the Date is the current week. **If no instance exists yet, STOP** — the template hasn't spawned; don't create one.
2. **Fill only-if-empty:** for each section, write only if it's still placeholder/empty. If a human already filled it, **skip and report the skip** — never clobber teammate input.
3. **Map from the prep page:**
   - `## Pipeline Updates` ← prep §2 (stages + chase). Omit the internal CRM-cleanup note.
   - `## 🏆 Big Wins This Week (All)` ← prep §4, numbered with attribution.
   - `## Onboarding Updates` (+ `Churn Risk` sub-bullets) ← prep §5 + §6 Red/Yellow one-liners.
   - Exec Summary toggle → **2026 Company Goals** table → `MRR to 100k` row → **Status cell** = the Stripe-computed MRR + RAG dot (e.g. `~$79.5K — $20.5K to goal 🟡`).
4. **NEVER touch:** the inline linked DB view in Exec Summary; any per-person toggle (Accomplishments / Top Priorities / Something Fun); the Announcements callout.
5. **Report** which sections were filled, which were skipped, and the standup page link.

---

## Anti-patterns (the failures this skill exists to prevent)
- **Stale/baseline data presented as current, or hedge language** ("verified subset", "per the [date] baseline") → violates the provenance rule. Read it live or flag it unread.
- **Calling `stripe_api_execute`** (doesn't exist) → false "Stripe not connected." Use `stripe_api_read` + `GetInvoices`.
- **Reading DBs via MCP query/search instead of the reader** → blocked (plan gate) or lossy (dropped rows). Always use `tools/notion_db_read.py`; fallback only on exit 3/5, and say so.
- **False "clean"** (AR/churn/onboarding) when the read actually failed → must be `UNAVAILABLE`, never "clean".
- **Pipeline stages inferred from calls/emails** → wrong stages. CRM `Deal stage` is ground truth.
- **Onboarding hand-derived from meetings** → soft, wrong counts. Pull §5 from the onboarding DB.
- **Sourcing from the standup** → circular. Client meetings, sales calls, 1:1s, biweeklies, Notion, Gmail, Stripe only.
- **Crediting departed teammates** → exclude them.

## Self-check before finishing
- Every section labeled live / fallback / unavailable — and zero banned hedge phrases?
- Any stale or baseline number presented as current? (must be no)
- AR: a real Stripe read, or an explicit `AR UNAVAILABLE`? Never a false "clean"?
- Pipeline stages from the reader/CRM, not inferred from calls?
- §1 anchored to Maxx-only leverage (≥1 offense, ≥1 build), with reassignments called out?
- Anyone departed credited? (must be no)
- Anything sourced from the standup meeting itself? (must be no)
- Do the standup blocks paste cleanly into the exec-summary structure?

---

## Token setup (one-time — the Mac Mini likely has this already)
The reader uses the Mac Mini's existing `NOTION_TOKEN` (an `ntn_...` internal-integration token, per MAC-MINI-SETUP.md). It only needs that the integration is **shared with each DB the reader hits**. If a read returns exit 5 with a 404, that DB isn't shared yet:
1. Open the DB → `•••` → **Connections** → add the integration. Do this for: **Sales Pipeline**, **Team Task Tracker**, **Content Calendar**, **DB: Spice Client Onboarding**.
2. If `NOTION_TOKEN` is somehow unset, export it (token from notion.so/my-integrations) or drop it at `~/.config/spice/notion-token` (`chmod 600`).
Until a DB is shared, the skill auto-falls back to search-enumerate (lossy) and labels that section accordingly.
