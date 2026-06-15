---
name: weekly-prep
description: Sunday evening weekly prep for Maxx, plus a Monday "push to standup" sync. Trigger when asked to "prep for the week", "weekly prep", "Sunday prep", "get ready for Monday", "push prep to standup", "fill the standup", or "Monday standup sync". Pulls calendar, recent meeting notes from ALL clients, the live sales pipeline (read per-deal from the CRM), sales emails, AR, and churn signals into a tight, triaged operating brief plus a short paste-ready standup block; then (Part 4, run Monday) auto-fills the team standup doc's Pipeline / Big Wins / Onboarding+Churn sections and the MRR goal cell.
---

# Weekly Prep

Generate Maxx's Sunday operating brief by pulling from Circleback (meetings/calendar), Notion (Sales Pipeline + client pages + Task Tracker), Gmail, and Stripe, then synthesizing into a triaged, action-first brief.

**This is an operating brief, not a status report.** Every line should either tell Maxx what to do or give him the one fact he needs to decide. If a line does neither, cut it.

---

## Part 1 — Data Sourcing

### 1. Calendar (coming week)
```
SearchCalendarEvents: startDate=[Monday], endDate=[+7 days], pageIndex=0
```
Feeds Top Priorities and surfaces sales calls, client meetings, conflicts. No standalone calendar table in the output.

### 2. Meeting notes (last 7 days)
```
SearchMeetings: startDate=[7 days ago], endDate=[today], pageIndex=0
```
`ReadMeetings` for every client meeting. Extract: wins (with metrics, attributed to the account owner), open action items (what's due, who owns), churn signals, onboarding progress.

Cover ALL clients, not just ones Maxx attends — goop, Capriotti's, Dayglow/AWAN, Everytable, Teleferic, MBFS, Counter Service, Menya Ultra, Temaki, Gertie, Fresh Kitchen, Westville, retention clients (HealthNut, AhiPoki, MBF), plus anyone in onboarding. Also pull the Retention Biweekly.

**CRITICAL — exclude the Spice Team Weekly Standup from all sourcing.** The prep feeds INTO the standup doc; sourcing from it creates circular duplication. If a data point appears only in the standup and in no client meeting/sales call/1:1/biweekly, it cannot be used.

### 3. Onboarding status — delegate to the `onboarding-status-check` skill (do NOT hand-derive from meetings)
Onboarding status for §5 is sourced from the **onboarding-status-check** skill, never re-derived from meeting notes (that's what made the section soft). Run only its **read + categorization** logic:
- Query the Client Onboarding Tasks DB (`collection://239d3ff0-18e7-8041-84d2-000b393bcc69`) for incomplete tasks (Status ≠ Done/N/A, has a Client assigned); fetch each task's Due Date (or compute it from SOW Start Date + Days After Start).
- Categorize each: 🚨 **Blocker** (5+ days late) / 🔴 **Overdue** (3–4 days) / ⚠️ **At Risk** (due today/tomorrow or 1–2 days past) / ✅ **On Track** (later). Run its stale-task check too (3+ days late still "Not Started").
- **READ-ONLY here:** do NOT trigger that skill's write side-effects during weekly-prep — no form/credential migration, no marking tasks Done, no Slack posts. Weekly-prep only consumes the status.
- That skill runs Tue/Thu 9am on the Mac Mini and posts a rollup to **#new-client-onboarding** (`C08D4EM5UCX`). Use the latest post as a cross-check, but prefer a fresh read since Sunday is several days out from Thursday.

### 3b. Active-client context (Notion)
For active (non-onboarding) clients, look for meeting-note pages from the last 7 days and team-logged decisions/blockers. Cross-reference with meeting notes — Notion may lag reality.

### 4. Sales Pipeline — read it correctly (this is the section that breaks; follow exactly)

Pipeline DB: data source `collection://1c0d3ff0-18e7-805b-ba76-000b04cc35c4`.

**Why this matters:** `notion-fetch` on the database — or on any of its views, even with `?v=` — returns **only the schema, never rows**. This MCP has **no `query_data_sources` tool**. `notion-search` over the data source returns an unranked, unfiltered grab-bag with **no Deal stage / Deal value / Last contact** fields and includes dead/test rows. None of these alone gives you the pipeline. You MUST read each deal's properties from its own page. Do not skip this — guessing stages from calls/emails is the exact bug that produced wrong stages before.

**Procedure:**
1. **Enumerate** candidate deals: `notion-search` with `data_source_url=collection://1c0d3ff0-18e7-805b-ba76-000b04cc35c4`, `page_size=25`, `max_highlight_length=0`. Returns page IDs, titles, last-edited dates.
2. **Drop junk** by title/age: skip anything matching `[DUPE]`, `[DELETE]`, `TEST`, or last-edited >90 days ago — unless a call/email from this week references it.
3. **Fetch each remaining deal page** (`notion-fetch` by ID, in parallel) and read the REAL fields: `Deal stage`, `Deal value`, `Locations`, `Last contact date`, `Account owner`, `Notes`.
4. **Ground truth = the CRM `Deal stage` field. Never infer stage from Circleback or Gmail.** Use calls/emails only to ADD next-step context (what was said, what's owed, what's blocking). If an email implies a different stage than the CRM shows, do NOT report the email's version — report the CRM stage and append a one-line `⚠️ CRM says X; [date] email suggests Y — update CRM`.
5. **Active pipeline** = `Deal stage` ∈ {New Lead, Reached Out, Qualified, Meeting Booked, Pitched, Proposal Shared, Agreement Sent}.
   - **Won** → list under "Recently Won → onboarding"; cross-check Stripe/P&L that billing started. A "Won" with no recent contact and no billing → flag `verify`.
   - **Lost / Not a Fit** → one line only if it moved this week.
   - **Ice Box** → omit unless reactivated this week.
6. **Stale flag:** days since `Last contact date`. Any active deal >14 days gets `⏳ N days quiet` and goes on the chase list.
7. **Data hygiene:** if junk rows or stage-quality problems exist (junk/dupe/test rows; "Won" rows with no value/Stripe IDs that read as un-closed), surface them in the **chat summary to Maxx — NOT in the Notion doc.** The brief stays operational; CRM cleanup is housekeeping. Never include junk rows in the pipeline list. (Per-deal `verify` tags on a specific deal are fine in-doc; the broad cleanup roll-up is not.)

**Banned language:** never write "verified subset," "confirm in CRM," "runs clean on the live job," or any hedge. If a deal genuinely couldn't be read, name it: `[Deal] — unread, check manually`. Nothing vaguer.

### 5. Gmail signals (last 7 days)
Catch async movement that never reaches Circleback. Three searches:
```
newer_than:7d (from:client-domains…)        # async decisions, blockers, asks between meetings
newer_than:7d (proposal OR agreement OR onboarding OR invoice)   # deal/contract status
newer_than:7d (hiring OR contractor OR interview OR offer OR onboard)  # team pipeline
```
Email is more recent than meeting notes — where they conflict, email wins for facts, but the CRM still wins for deal stage (see §4).

### 6. AR + MRR (Stripe)
**AR:** pull unpaid/overdue invoices. For each: client, amount, invoice ID, due date, why (failed auto-charge vs send-invoice unpaid), who to chase. Flag any client you're about to scrutinize on spend who also owes money — they pay first.

**MRR (compute it — do NOT use the vault/P&L estimate; that runs ~$10K high and stale):** the goal-tracking number must come from Stripe.
- Sum **active subscriptions** (status active/trialing), normalizing annual ÷ 12. Paginate fully — don't trust a truncated page.
- **Also count recurring `send_invoice` subscriptions** — goop, Capriotti's, etc. bill net-30 and sit in `past_due`/non-`active` status, so a naive `status=active` query MISSES them (~$15K). Query all statuses and include clearly-recurring service fees. These count toward MRR even when delinquent (MRR = contracted recurring), but note the delinquent portion.
- ~7 CAD subscriptions (BKDS group) add minor FX noise — state whether you counted CAD nominally or converted.
- Report **Total MRR + gap to the $100K goal**, with the subscription / recurring-invoice split and the past-due amount. (Reference figures, Jun 2026: ~$64K subs + ~$15.5K recurring invoices = ~$79.5K; ~$20.5K from goal.)

### 7. Churn scoring
Score every active client 0/1/2 on five dimensions — **Pay** (late/disputed billing), **Eng** (responsiveness, attendance, POC churn), **Perf** (sales/conversion/rating trend), **Ops** (platform/menu/campaign blockers), **Rel** (lead changes, tension). Total /10 → High (6+), Monitor (3–5), Healthy (0–2). Compare to last week's prep (fetch the prior page) and note score changes + why. Only surface clients scoring 3+; the rest are "Healthy."

---

## Part 2 — Output Format

Section order below is fixed. **Length budgets are hard caps.** Enforce the **one-mention rule**: each client/deal lives in exactly ONE section; reference it elsewhere by name only ("see §1"), never re-describe its metrics.

Open with one italic source line: dates pulled, sources used, standup excluded, departed teammates excluded from credit.

**Output hygiene (clean, copy-paste-ready — no exceptions):**
- **One representation per dataset.** Never ship the same data as both a table and a list (the old churn table + bullets was the offender). Pick one.
- **No auto-link bait.** Notion auto-links bare domains/emails (`Agree.com`, `gong.io`, `x@gmail.com`) into ugly live links. Reword to avoid them ("your e-sign queue", "vendor/no-reply contacts") or drop them. Keep only intentional `[label](url)` links to real Notion/Circleback pages.
- **Title = one icon.** The archive page already has a 📋 icon — do NOT prefix the title text with another 📋.
- **Paste blocks** use a plain-text code fence (```` ```text ````), never a language-tagged one.
- **Cross-ref, don't repeat.** If a client is both a §1 priority and a §6 churn case, §6 says "see §1" — metrics live in one place.

### 1. Top Priorities This Week (triaged)
Max **5**, ranked by leverage. Each ≤3 sentences: the move, the one number that justifies it, the deadline. Link the source meeting.

**Decisions waiting on you** — sub-list, ≤6 items, **one line each**. These are calls only Maxx can make. Do not re-describe anything already in a priority above; if it's both, keep it in priorities and drop it here.

**AR / cash flag** — from §6. One line per unpaid invoice.

### 2. Sales Pipeline Review
From §4. Grouped by stage, bullets (no tables). Skip empty stages. One italic line noting it's driven off the live CRM Deal stage field.
```
**Meeting Booked**
- **[Deal]** ([owner], [N loc], $[value]) — [next step + date]. [⏳ if stale]

**Pitched / Proposal Shared / Agreement Sent**
- **[Deal]** ([owner]) — [context]. Next: [action]. [⏳ if stale]

**Recently Won → onboarding**
- [Deal list] — billing confirmed via Stripe/P&L. [verify flags if any]

**Chase this week:** [stale + high-value deals, named].
```
**No hiring here** — that's the team section. Keep CRM cleanup / data-quality notes OUT of the doc — those go to Maxx in the chat summary (Part 1 §4 step 7).

### 3. Content Pipeline Review
Latest content mine + anything scheduled + up to 3 post-worthy topics, one line each. Note timely angles (events, platform news). Keep to ~8 lines.

### 4. Team Highlights — last week
One line per active member: the single best thing they shipped, with a metric. **Include EVERY active teammate** — someone being transitioned out (e.g. under performance management) is still active and gets a neutral line; only the *departed* are omitted. Cross-check the roster so no one is silently dropped. End with one "client performance wins" line for results not tied to a single person. ~1 line each, no paragraphs.

*Roster check (as of Jun 2026 — verify, don't trust blindly): active — Rodrigo, Daniel, Ana, David Pliego, Manish, Harol, Santiago Lopez, Santiago Beltrán, Dilli, Omar, Diline. Departed (no credit) — Cesar, Rui, Tomas.*

### 5. Onboarding Updates
New-client onboarding only, **sourced from the onboarding-status-check read in §3 — not from meeting notes.** Lead with the real category totals from that DB: 🚨 Blockers / 🔴 Overdue / ⚠️ At Risk / ✅ On Track. One line per active onboarding: the gating task, its category, the owner to tag, and the next concrete step. Recently-won-but-not-yet-onboarding clients are a single roll-up line. Meeting notes only ADD color (e.g. a verbal "storefronts are built") — the task DB is the source of truth for status.

### 6. Client Churn Risk
**One scored bullet per client — no separate scoring table** (fold the score in): `🔴/🟡 **Client (score)** — issue + owner + this-week move`. 🔴 High (6+) first, then 🟡 Monitor (3–5); only 3+ shown. If the client is also a §1 priority, write `see §1` instead of repeating its metrics. Note score changes vs last week. End with `Lost:` if any.

### Standup Summary — copy/paste (formatted, NOT code blocks)
The ONE intentional consolidation — the body's one-mention rule doesn't apply here (its whole job is to be pasted into the standup doc). **Render it as real formatted content — proper sub-headings and bullet/numbered lists, exactly as it should look in the standup doc — NOT inside code fences.** Maxx copies a section's formatted content and drops it under the matching standup heading; no reformatting. Use the standup's exact section names as `###` sub-headings, in this order:
- **MRR / Goal** (the Exec Summary "MRR to 100k" cell) → a single bold line: the **Stripe-computed** MRR (§6) + RAG dot + gap to $100K. Never the vault estimate.
- **`### Pipeline Updates`** → bullets: **Recently Won** / **Proposal Shared** / **Meeting Booked** / **Pitched** / **Chase**.
- **`### 🏆 Big Wins This Week (All)`** → a numbered list (`1.` …), top 5, `win — owner`.
- **`### Onboarding Updates`** → bullet(s): counts + the one client needing attention.
- **Churn Risk** (bold sub-label under Onboarding) → bullets: **Red** / **Watch** / portfolio health / Lost.

Names-and-numbers, not sentences. Skip any section that maps to nothing rather than inventing a target (there is no team-level "Top Priorities" block — that's per-person in the standup). When the Part 4 sync runs it writes these same blocks directly and this manual summary becomes unnecessary.

---

## Part 3 — Output to Notion

Write the brief to the **Weekly Prep Archive** (the page already lives under Diline's Command Center). Title: `📋 Weekly Prep | [Mon date] - [Fri date], [Year]` — exactly one 📋, no double prefix.

```
notion-search: "Weekly Prep [date]"
```
If a page exists for this week, update it; otherwise create one under the archive data source.

**Formatting:** when using `replace_content`/`new_str`, use real newline characters — never literal `\n`, which renders as text in Notion.

Return the Notion page link in the final response.

---

## Part 4 — Standup Sync (run Monday morning, separate step)

Trigger: "push prep to standup", "fill the standup", "Monday standup sync", or a Monday-morning schedule. **Run AFTER the standup instance has spawned (~9am Mon) — never Sunday.** Source = the latest Weekly Prep page in the archive (`collection://47524728-ae68-4019-a793-0a1032495061`). Target = this week's standup instance.

The standup doc "🌶️ Spice | Weekly Standup" is a row in **DB: Team Meetings** (`collection://1ced3ff0-18e7-8088-820b-000b9f3c0729`), auto-spawned each Monday from a database template (template `1ced3ff018e780f1a66ce1e554093ff3` — reference only, NEVER write to it).

**Procedure:**
1. **Find the target.** Search DB: Team Meetings for the row with `Category = Standup` and `Date` = this week's Monday (or `notion-search "Spice Weekly Standup"`, newest). Confirm Date is the current week. **If no instance exists for this week yet, STOP** — the template hasn't spawned; do not create one manually.
2. **Fetch the instance.** For each target section below, **only write if it's still empty** (placeholder/empty blocks only). If a human already filled it, skip it and report the skip — never clobber teammate input.
3. **Fill (map from the prep page):**
   - `## Pipeline Updates` ← prep §2, condensed: stages + chase list. **Omit** the internal CRM-cleanup / data-quality note — that's for Maxx, not the team doc.
   - `## 🏆 Big Wins This Week (All)` ← prep §4 wins, numbered with team-member attribution.
   - `## Onboarding Updates` (+ its `Churn Risk` / `Churn Cases` sub-bullets) ← prep §5 + §6 Red/Yellow one-liners.
   - Exec Summary toggle → **2026 Company Goals** table → `MRR to 100k` row → **Status cell** = the Stripe-computed MRR figure + RAG dot from the prep standup block (e.g. `~$79.5K — $20.5K to goal 🟡`).
4. **NEVER touch:** the inline linked DB view in Exec Summary; any per-person toggle (Accomplishments / Top Priorities / **Something Fun**); the Announcements callout. These are human/live.
5. **Return:** which sections were filled, which were skipped (already had content), and the standup page link.

---

## Anti-patterns (the failures this skill exists to prevent)
- **Pipeline read from schema/search instead of per-deal pages** → wrong stages, miscategorized deals, hedge language. Always do §4 in full.
- **Onboarding status hand-derived from meetings** → soft, wrong counts. Always pull §5 from the onboarding-status-check DB read (§3).
- **Duplication** → the old "Standup Exec-Summary Blocks" re-listed every section. One-mention rule + the tight standup block kill this.
- **Status-report bloat** → if a line doesn't drive an action or a decision, cut it.
- **Sourcing from the standup** → circular. Client meetings, sales calls, 1:1s, biweeklies, Notion, Gmail, Stripe only.
- **Crediting departed teammates** → exclude them.
- Maxx adds his own "Something Fun"; the standup doc auto-duplicates Monday 9am.
