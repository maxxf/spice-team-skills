---
name: campaign-briefing
description: >
  Weekly delivery-marketplace campaign briefing for ANY Spice client, run TUESDAY (platform data
  settles Tue, not Mon). Two modes: (A) Spend-Pacing Flash — a one-screen client pulse answering
  "how are we pacing / can we spend more", pulled live from the ad portals; and (B) Full Weekly
  Refresh — updates the client's campaign sheet + weekly report. Pulls budget utilization by
  campaign & location (Uber "Budget pacing" column; DoorDash is CPO-capped), the ads-vs-offers mix
  by platform, budget-pacing outliers, bid-strategy diagnostics, and coverage + succession. Can also
  render a branded, Slack-shareable visual flash card via /deploy. Trigger
  on "weekly refresh for [client]", "[client] flash report", "[client] spend pacing", "how is
  [client] pacing", "budget utilization for [client]", "build [client] weekly report", or any request
  to brief a client's campaign performance for a week. Works for every marketplace client; for
  client-specific config (paths, report templates, store list, spend cap) read that client's block.
team: marketplace
version: 1.0.0
---

# Campaign Briefing (Tuesday) — all clients

Client-agnostic. Resolve `{client}` first, load their config block (below), then run one of two modes:

- **Mode A — Spend-Pacing Flash.** One-screen Slack pulse: "how are we pacing and can we spend
  more?" No report duplication. Default for a mid-week / async client request.
- **Mode B — Full Weekly Refresh.** The client's campaign sheet refreshed + weekly report built.

Owner varies by client (analyst pulls → account lead commentary → Maxx QA + client send).

## Why Tuesday, not Monday
Platform data (Uber Eats, DoorDash) keeps settling — transactions, offer attribution, ad spend —
through Monday. Tuesday is the first stable read of the closed week (Mon–Sun). Anything sent to a
client goes out Tuesday.

## The four questions every briefing answers
1. **Pacing vs the client's marketing-spend cap** — portfolio %, by platform, by tier; dollar headroom.
2. **Room to spend more efficiently** — capped-but-earning campaigns (raise) vs underspending (headroom).
3. **Coverage** — any location with no active campaign/offer; any campaign ending ≤14 days (succession).
4. **Adjustments** — a specific raise / cut / reallocate / launch / hold list, each tied to a campaign.

---

## Phase 1 — Resolve client + inputs
- Load the client's config block: working folder, campaign sheet, report template, store list, spend
  cap %, tier structure, house report format, Slack channels.
- Raw pulls → `{client working folder}/flash-report-data/`, dated by week. Never overwrite a prior
  week (audit trail).

## Phase 2 — Pull platform data

### Uber Eats — Ads Manager (`advertiser.uber.com/campaigns/manage`)
- **Account:** Spice manages ~15 clients under one advertiser login (`success@spicedigital.co`).
  CONFIRM the account selector reads the correct `{client}` before trusting any number — it loads a
  different client first by default.
- **Budget utilization = the "Budget pacing" column** (spend as % of budget per campaign & location).
  This is the utilization metric clients ask for.
- Per campaign capture: Status, Location, Budget/wk, Budget pacing %, ROAS, Ad spend, Sales, **End
  Date**, co-funding %, New / Lapsed / Existing split, and **bid strategy** (Maximize ROAS vs manual
  Target CPC — see 3c).
- "Locations with campaigns (N of [store count])" above the table = fast coverage check.
- Recommendations panel flags capped winners ("raise budget $X→$Y, +$Z/wk") — corroboration only.
- Offers tab (`/campaigns/manage/offers`): status, spend/redeemed, ROAS, end date per location.

### DoorDash — Merchant Portal
- **DoorDash caps on cost-per-order (CPO), not a weekly budget.** "No cap on average weekly budget"
  ≠ uncapped — the control is the CPO ceiling / target ROAS. Do NOT report a weekly-budget
  utilization % for DD. Report spend / sales / ROAS per campaign and the CPO where visible.
- "Spend more on DD" = raise the CPO ceiling + expand coverage (Sponsored Listings often run at few stores).

### Grubhub
- Lower priority (typically small portfolio share). Pull only if the week's decisions touch it.

### Known blocker — the pull is fragile
Automated pulls have hit an "Accept Uber Advertising Terms" wall and CDP/portal timeouts. The team
has account access — accept the terms once, manually, to clear the wall. Screenshots time out
intermittently; reading the page DOM is more reliable than screenshotting.

## Phase 3 — Analysis

### 3a. Budget-pacing outliers (active campaigns only)
- **Capped winners** — pacing >90% AND ROAS above the client's target → raise budget.
- **Underutilized** — pacing <60% → headroom, BUT check why: often audience-size-limited (a small
  Lapsed pool can't absorb more spend), not a budget lever.
- **Inefficient high-spend** — pacing >80% AND ROAS below target → fix or reallocate.
- **Status flag each active campaign:** 🟢 Performing (above target, no concern) · 🟡 Watch
  (trending down / borderline) · 🔴 Below target (below ROAS target 2+ weeks) · 🧪 Test (active
  experiment w/ hypothesis + decide-by date).

### 3a-bis. Direction (WoW) — not just the snapshot
Pacing/spend/ROAS as a point tells you little; the direction drives the call. Pull last week's
numbers (tracker/sheet or a prior portal pull) and, per location & per campaign, mark whether
**spend, budget pacing, and ROAS are rising, flat, or falling.** Read the combinations:
- pacing ↑ to ~100% + ROAS holding → scale (raise budget)
- spend ↑ + ROAS ↓ → getting inefficient (investigate before feeding more)
- pacing ↓ → losing steam / audience fatigue
Surface a short **"Movers"** list (biggest WoW risers and fallers in spend and ROAS) in every briefing.

### 3a-ter. Decline Alerts (fire automatically)
Flag any of: **location WoW sales < −10%** · **campaign ROAS below target 2 consecutive weeks** ·
**active test failing its hypothesis.** These are the must-surface items, above the general commentary.

### 3b. Ads vs Offers mix
- Split marketing spend into Ads (UE + DD Sponsored Listings) vs Offers (UE Offers + DD Promotions),
  by platform and blended; each as share of spend + ROAS.
- The split is **platform-specific, not global**: on UE ads ≈ offers ROAS; on DD offers usually beat
  ads. And within each, **Lapsed audiences beat New-to-Brand.** Frame aggression by audience +
  platform, not by the ads/offers label.

### 3c. Bid-strategy diagnostic
Utilization is driven by bid strategy, not audience:
- **Maximize ROAS** = the efficient auto strategy. (goop example: the same new-to-brand audience
  returns ~1171% on Maximize ROAS vs ~230% on manual Target CPC.)
- **Manual Target CPC** ($2–3/click) causes full-pacing-but-low-ROAS campaigns — it buys clicks to a
  price ceiling regardless of conversion. Flag and convert off it.
- Size budget to audience; give new campaigns 2–3 weeks before judging pacing.
- **Name hygiene:** audit campaign name vs configured audience — stale names (e.g. "New" vs
  "New-to-Brand" both mapping to the new-to-brand audience) cause bad reads.

### 3d. Coverage + succession
- **Enumerate ALL storefronts from the store list first** (UE Manager + DD store list), THEN diff
  against active campaigns. A location with zero campaigns never appears in the campaign table, so
  reading campaigns alone will silently miss dark locations. The coverage read is only complete when
  every storefront in the store list is accounted for.
- Coverage matrix per storefront: active UE ad? active offer? active DD? Flag any dark platform, and
  explicitly list any storefront that could not be verified (don't imply full coverage).
- Succession: any active campaign ending ≤14 days → name the planned successor.

## Phase 4 — Build the artifact

### Mode A — Spend-Pacing Flash
Structure the output as a 3-part spine — **what's happening → what we're changing → what we're
watching** — bookended by an at-a-glance line and a bottom line. Keep depth inline (each move
carries its own number) rather than in separate Raise/Cut/Headroom blocks — that's what makes it
digestible without losing the receipts.

```
📊 {client} — W[XX] Spend-Pacing Flash · [Tue date]

At a glance: marketing X.X% of sales vs {cap}% target · ~$XXK/wk headroom · blended Xx.
[one line framing the real question — usually "not whether we can spend more, but where it pays"]

WHAT'S HAPPENING
• Pacing: X.X% (UE X.X · DD X.X · GH X.X), direction WoW
• Ads vs offers: XX/XX — where return actually lives (platform + Lapsed vs New-to-Brand)
• Momentum: ⬆️ risers · ⬇️ fallers

WHAT WE'RE CHANGING THIS WEEK   (numbered moves, each with its why)
1. … 2. … 3. …
The receipts: compact table — Campaign | Paced% | ROAS | Move this week — covering every
campaign being touched (raises + tests + retargets). This is the depth layer readers want.

WHAT WE'RE WATCHING
• resets, payout flags, unverified coverage

Bottom line: [the one-sentence strategic call — usually reallocation before net-new spend]
```
Neutral, data-first; account lead adds interpretive "why" lines. No report duplication — that's the
point of a flash. Scale the receipts table to what changed; if nothing's moving, say so.

**Slack rendering (important):** Slack does NOT render Markdown pipe tables — put the receipts in a
``` code block ``` so columns stay aligned. Use `*single-asterisk*` bold (not `**`), bold lines
instead of `#` headers, and `•`/`-` bullets. Note the code block side-scrolls on mobile; if the
audience is mobile-first, use one bulleted line per campaign instead of the code-block table.
**Never use italics** (no `_text_`, no `*text*` as emphasis) in any output — house style. Use bold
or plain text for emphasis everywhere.

#### Visual flash card (recommended for client shares)
Alongside the text flash, render a branded one-card visual and share it as a link — Slack renders it
cleanly where Markdown tables don't. Design lane: frontend-design / dataviz, NOT content voice.
- Layout (single card, one screen, flat): header (`{client}` · W[XX] · date) → KPI row (marketing %
  vs cap · $ headroom · blended ROAS · WoW efficiency) → two columns (What's happening / Changing
  this week) → receipts table color-coded by move (green = raise · amber = test · blue = retarget) →
  Watching strip → bottom line. No italics.
- Deliver via `/deploy` → a hosted link that unfurls in Slack, works on mobile, and can be gated for
  client-facing channels. Post the link alongside the text flash for readers who don't click through.
- Scale the receipts rows to what changed; keep it to one card.

### Mode B — Full Weekly Refresh
Run the client's campaign-sheet update and weekly-report build per their config block / template.
- **Report spine (4 pillars, locked order):** Payout $ trend · Spend % trend · Struggling locations ·
  Campaigns + launches. (Clients may add bespoke pillars in their config block.)
- **By-Location rollup:** # active campaigns, total spend/sales, blended ROAS, top performer /
  underperformer per location.
- Every closed campaign gets Archive Learnings before it leaves Active (Hypothesis / Outcome /
  Decided-to-Continue) — experiment discipline.
- **Validation before client share:** net sales tie-out, commission % in expected range, net payout %
  in range. Catch any anomaly before it reaches the client.

## Phase 5 — Experiment discipline
- Any live test (bid-strategy switch, audience change, offer depth) is logged with a **hypothesis**
  and a **decide-by date** (usually next Tuesday's read): continue / modify / kill.
- Do not close a campaign without documented Learnings.

## Phase 6 — Handoff
Post in the client's internal channel: data loaded, artifact link, handoff to the account lead for
commentary, Maxx QAs after. Update the client's weekly-metrics sheet.

---

## Per-client config (add a block per client)
Each client needs: working folder · campaign sheet path · weekly-report template · store list +
count (UE / DD) · marketing-spend cap % · tier structure · house report format · Slack channels ·
any co-funding deals.

### goop kitchen (example block)
- Folder `/Users/maxx/Documents/Claude/Projects/goop kitchen/`; Campaign Sheet v3.
- Notion master template `notion.so/373d3ff018e781dabe7fc0a8710af031` (duplicate only, never edit).
- Stores: 28 UE / 20 DD. Cap: 10%. Tiers: Top / Mid / Low / New (+ Red-tier SJ & Pasadena).
- Report Highlights pillars (locked order): Payout $ trend / Spend % trend / Struggling locations /
  Campaigns + launches. Channels: `#int-goop-kitchen`, `#ext-goopkitchen-spice`.
- Reference: Weekly Platform Overview 2.0 `docs.google.com/spreadsheets/d/18we-M-qVdug4LRZiolfScL3emVPE0AuL4Zb9Zqn_A3A`.

## Do NOT
- Run before Tuesday · edit a client's report master · report another client's numbers as this
  client's · report a fake DD budget-utilization % · close a campaign without Learnings · fabricate
  retrospective hypotheses.
