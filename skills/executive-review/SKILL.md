---
name: executive-review
description: "Generate a CFO-ready engagement-to-date executive review for any Spice delivery marketplace client. Produces a three-lens metrics headline (YoY same-store, intra-year trajectory, struggling locations), per-store breakdown, struggling location progress, portfolio context, competitive context, optional honest reflection, forward plan with asks, and anticipated Q&A. Output is a Notion page in the client's Documents Hub plus a Slack-ready summary. Optionally kicks off a data collection sprint by creating Team Task Tracker tickets assigned to the client's ops analyst (Supporting Team field). Trigger on 'exec review for [client]', 'executive review', 'CFO review', '6-month review', 'performance review for [client]', 'strategic review', 'engagement review', '90-day ROI report', 'quarterly business review', client steering committee prep, board updates, or any request to package strategic-level review of client engagement performance, even if the user doesn't say 'exec review' explicitly. Also trigger when the user asks to 'assign data collection for exec review' or 'spin up the analyst tickets for [client] review'."
---

# Executive Review: Spice Delivery Marketplace Skill

This skill produces a strategic-level review of a Spice client engagement, suitable for sharing with the client's CFO, head of operations, or board. It uses canonical Weekly Reporting Skill methodology so the numbers reconcile to the client's live tracker tabs.

## What this produces

Two artifacts, in two different stores:

1. **Raw data appendix** in a Google Drive folder under `/Clients/[Client]/Exec Reviews/[YYYY-MM]/`. Holds every CSV, MD scratch note, and screenshot the ops analyst produced. CSVs live as Google Sheets so charts, pivots, and QUERY are first-class.
2. **The final Notion page** in the client's Documents Hub, which synthesizes the raw appendix into the client-facing narrative. Page links the GDrive folder as "Data appendix."

Why split: Notion swallows CSVs as opaque attachments. Sheets are first-class in GDrive and sit next to the client's live Data Dashboard. Doc Hub is where Hannah/Jamie expect to find polished reports, and it carries discussion threads. Raw data and final narrative serve different readers.

The Notion page is structured as follows (full template in `references/output-template.md`):

1. **TL;DR**: 6 punchy bullets + a one-line "ask" footer
2. **High Level Metrics**: 3-lens × 4-metric table (Total Sales, Net Payout, Marketing Spend, ROAS across YoY same-store, Intra-year portfolio, Struggling locations)
3. **§1 YoY Same-Store**: per-store breakdown table with payout YoY column, plus cannibalization story if applicable, per-location callouts for anomalies
4. **§2 Intra-Year Trajectory**: portfolio-level W1 → W_current with charts (Weekly TMI, Marketing ROAS), bullets on the inflection
5. **§3 Struggling Locations Progress**: focus locations only, with menu CVR (if tracked), ratings velocity (if program exists), sales trajectory chart, weekly payout deltas
6. **§4 Portfolio Context**: new-store contribution if portfolio expanded; tier breakdown if helpful
7. **§5 Competitive Context**: where the client sits vs category benchmarks and nearest competitors. Pulls from storefront audits and public marketplace data. Skip if no competitive data available.
8. **§6 Honest Reflection**: only if there's a communication gap or trust moment worth surfacing; quote + structured bullets
9. **§7 Forward Plan + Asks**: next 90 days, KPI commitments, specific asks for the client
10. **§8 Questions We Expect**: anticipatory Q&A in client's voice

Plus a **Slack-ready short summary** (3-5 sentences) the GM can paste into the client channel when sharing the doc.

## When to use

Use this skill whenever the Spice GM, Service Lead, or Maxx asks to produce a strategic review of client engagement. Common triggers:

- "Build an exec review for [client]"
- "I need a CFO-ready doc for [client]" 
- "What's the case for our work with [client]?"
- "Steering committee prep for [client]"
- "Show me a 6-month review for [client]"
- "We have a quarterly business review with [client] coming up"
- "Run exec review for [client] and assign data collection to the ops analyst" (triggers Phase 0 delegation first)

Don't use this skill for:
- Weekly tracker updates (use `weekly-reporting` skill)
- Campaign-level briefs (use `campaign-planner` or `campaign-ops`)
- Single-week pulse reports (use `weekly-reporting` skill)
- Sales follow-ups or proposals (use `post-sale-proposal`)

## The workflow

### Phase 0: Data collection delegation (optional but standard)

Trigger this phase whenever:
- The user explicitly asks to "assign data collection tasks" or "spin up tickets for the ops analyst"
- The exec review is being kicked off with a multi-day lead time (analyst can prep raw data while Maxx is mid-week)
- The synthesis lives more than 24 hours away and parallelizing data pull saves wall-clock

Skip this phase if Maxx is doing the synthesis himself in real time and already has the CSVs in hand.

**Step 0.1 — Identify the ops analyst.** Pull the client page in Notion (Clients DB: `collection://1c8d3ff0-18e7-80e9-8381-000b4448cb87`) and read the `Supporting Team` people field. Resolve user ID → person via `notion-get-users`. As of May 2026 the rotation is Santiago, Dulari, and Manish; the client's Supporting Team field is the source of truth.

**Step 0.2 — Provision the GDrive folder.** Create `/Clients/[Client]/Exec Reviews/[YYYY-MM]/` in Google Drive (or note the path for the analyst to create). All raw outputs (CSVs, MD notes, screenshots) land here. Each output file must be named per the ticket spec so the synthesis step can grab them programmatically.

**Step 0.3 — Create Team Task Tracker tickets.** One ticket per data input the skill needs.

**Scoping rule — read this twice.** These tickets are raw data extraction. The analyst pulls numbers, screenshots, and verbatim quotes into structured CSVs and dumps them in the GDrive appendix folder. The analyst does NOT interpret, summarize, characterize tone, flag "concerning patterns," write "key learnings," or draw conclusions. Maxx (or whoever runs the synthesis) reads the raw outputs and writes the narrative. Every ticket Description should lead with `SCOPE: raw data extraction only. Maxx synthesizes.` and every Additional Notes field should restate it. Interpretive language in a ticket Description biases the analyst into editorializing, which (a) wastes their time on judgment calls outside their scope and (b) contaminates the source material the synthesizer is supposed to read fresh.

Banned ticket phrases: "key learnings," "trust temperature," "flag concerning," "surface where X is the only Y," "summarize results," "what worked," "highlight," "analyze." Use instead: "extract," "pull into the CSV," "verbatim," "no commentary," "leave the cell blank if X."

Use the Team Task Tracker data source: `collection://1c8d3ff0-18e7-80f0-a36b-000b6befe5b1`. Template fields per ticket:

```json
{
  "Request Title": "[Exec Review] [CLIENT] — [DELIVERABLE]",
  "Client Name": "[Client]",
  "Client": "[client page URL]",
  "Status": "Not started",
  "Priority": "High",
  "Task type": "Analysis",
  "Service Team": "Marketplace",
  "Source": "Agent",
  "Urgency Level": "Urgent - same or next business day",
  "Platforms": "[\"Uber Eats\", \"DoorDash\"]",
  "Support Category": "Data/Reporting",
  "date:Due date:start": "[tomorrow's date]",
  "date:Due date:is_datetime": 0,
  "Description": "[exact deliverable spec + GDrive output path + file name]",
  "Additional Notes": "[which exec review section this feeds]"
}
```

Then assign the analyst via `notion-update-page` setting the unnamed person property `""` to `"[\"<user_id>\"]"`.

**Standard ticket set (adapt per client situation):**

1. **Engagement-to-date trajectory (W1 → W_current)** — portfolio + per-location canonical metrics. Feeds §2.
2. **Per-location weekly performance** — every active store, weekly granularity. Feeds §3, §4.
3. **Menu CVR funnel for focus/struggling locations** — UE Manager funnel data. Feeds §3 CVR lever.
4. **Ratings velocity + review program status** — every location, both platforms, baseline vs current. Feeds §3, §5.
5. **Campaign performance recap** — every campaign run during the review window with TMI/incremental orders/ROAS. Feeds §2 inflection bullets + §7 forward plan.
6. **Competitive context per market** — top 3 nearest competitors per market, hero/promo/rating/review count. Feeds §5.
7. **Recent client comms sentiment (last 6 weeks)** — Circleback + Slack + WhatsApp signal. Determines whether §6 Honest Reflection runs.

**The YoY ticket is non-optional.** YoY same-store is the lift story: same stores, prior-year same calendar weeks, with vs without Spice. Engagement length does not determine whether YoY runs. Store operating history does. If the stores existed last year, the YoY lens runs. The shorter the engagement, the more important YoY becomes because it's the cleanest counterfactual.

The 8th ticket: prior-year same-window raw CSVs from UE/DD for every store with ≥12 months operating history. UE order history + DD financial transactions for the matching N-week window one year back. Apply canonical Net Payout formula to both years.

**Step 0.4 — Notify the analyst.** Post in `#support-ops` Slack channel with @-mention of the analyst, all ticket links, the GDrive folder path, and a one-line context sentence ("Maxx is building the [Client] engagement-to-date exec review for [POC] — engagement is [<12mo / ≥12mo] so [intra-year / YoY] is the headline lens.").

**Step 0.5 — Confirm the tickets stuck.** Re-fetch one of the tickets to verify the assignee field landed and the due date is set correctly. Notion's person field uses a JSON array string; if the assignment shows blank, retry.

After Phase 0, work pauses until the analyst's outputs land in the GDrive folder. The user can re-trigger the skill with "synthesize the exec review for [client]" once raw data is ready, jumping straight to Phase 1.

### Phase 1: Gather context (do not skip)

Before computing any numbers, gather these inputs. Most can be pulled programmatically; some require asking the user.

**Required:**

1. **Client name** (must match Notion Client Wiki)
2. **Review period**: default is "engagement-to-date" (SOW start → most recent W_n). Can be quarterly, annual, or custom.
3. **Engagement start date** (from Client Wiki SOW Start Date property)
4. **Tier framework**: pull from Client Wiki "Service Details" (UNICORN/GREEN/YELLOW/RED, or client-specific variant)
5. **Focus locations**: pull from Client Wiki (typically the bottom-performing tier the GM is actively working on)
6. **Closed/winding-down locations**: to exclude from same-store comp (ask GM if unsure)
7. **Workbook URL**: the client's weekly metrics tracker
8. **GDrive raw appendix folder** (if Phase 0 ran): grab the folder URL so it can be linked from the final Notion page as "Data appendix"

**Optional but valuable:**

- Recent Circleback meeting notes (last 4-6 weeks)
- Recent Slack messages from client channel (`#ext-[client]-spice` and `#int-[client]`)
- Campaign Plan Q2 / current Q
- Most recent W_n weekly update Notion page
- Raw platform CSVs for YoY analysis (UE/DD/GH for current period + prior year equivalent), if engagement is ≥12 months

### Phase 2: Compute the three lenses

Use the canonical methodology defined in `references/methodology.md` (mirrors the Delivery Marketplaces | Weekly Reporting Skill doc):

- **Total Sales** = food subtotal EXCLUDING tax
- **Net Sales** = Total Sales − Discounts
- **Net Payout** = Net Sales − Commissions − Ad Spend − Other Adjustments
- **Net Payout %** = Net Payout ÷ Total Sales × 100
- **TMI** = Ad Spend + Discounts (offers)
- **Marketing ROAS** = Marketing-driven sales ÷ TMI

**Lens 1 (YoY same-store):** Run on every store with ≥12 months operating history (NOT every engagement with ≥12 months Spice tenure — those are different rules). Compare same N-week window current year vs prior year. Exclude any store that wasn't active across both windows. Sum totals; compute per-store deltas; flag any store down YoY. For shorter engagements this lens is the headline because it isolates Spice's intervention from the store's pre-Spice baseline.

**Lens 2 (Intra-year portfolio):** Pull canonical Weekly Platform Overview 2.0. Compare W1 of current year (first full week) vs most recent W_n. Show: Total Sales, Net Payout, TMI, Mkt/Sales %, ROAS.

**Lens 3 (Struggling locations):** For each focus location, compute Jan baseline → most recent W_n trajectory. Pull menu CVR if tracked (from Ops - Focus Locations tab). Pull ratings velocity if program is running.

Scripts to use:
- `scripts/compute_yoy.py`: applies canonical formula to raw CSVs for prior year
- `scripts/compute_intra_year.py`: pulls intra-year trajectory from canonical tab CSVs
- `scripts/compute_struggling.py`: focus locations sales + CVR + ratings

### Phase 3: Decompose the story

Run `scripts/decompose_growth.py` against same-store YoY data. This surfaces:

- **Platform-level attribution**: how much UE vs DD drove growth
- **Spend pattern**: ad spend vs offer spend YoY shift
- **Cannibalization signal**: if a platform shows sales growth ON ad spend reduction, that's the cannibalization fix story
- **Margin pressure flag**: if payout % dropped while sales grew, surface honestly

Run `scripts/cvr_to_dollars.py` if struggling locations have menu CVR data. Quantifies the CVR lift in annualized $ terms.

### Phase 4: Decide which sections to include

Not every client needs every section. Use this logic:

- **§1 YoY Same-Store**: include if stores have ≥12 months operating history. Engagement length is irrelevant. Skip only if all stores opened during the engagement (rare).
- **§3 Struggling Locations**: include only if client has a focus tier with active interventions
- **§4 Portfolio Context**: include only if new stores opened during the comparison period
- **§5 Honest Reflection**: include only if there's a real communication gap or trust moment from recent meetings/Slack. Don't fabricate. If unsure, ask the user.
- **§6 Forward Plan**: always include; pull from current Campaign Plan

### Phase 5: Draft and visualize

Use the output template (`references/output-template.md`) as the structural skeleton.

**Charts MUST use QuickChart, not Mermaid.** Mermaid xychart-beta lines render too faintly in Notion. Use the URL builders in `scripts/build_chart_urls.py` which apply consistent styling:

- Line charts: red `#E63946` for spend / "down is good" metrics, teal `#2A9D8F` for ROAS / "up is good"
- Bar charts: gray `#94A3B8` for "before" baseline, teal `#2A9D8F` for "after" / improved state
- 4px borderWidth, 6px point radius, 18pt title, 14pt labels
- Always include explicit axis ranges (don't auto-scale)

**Voice rules** (see `references/voice-guide.md`):
- Direct, no fluff
- No em-dashes (use period, comma, or restructure)
- Lowercase casual when paraphrasing Maxx; title case for headings
- "skip 'great question' / 'it's not about X, it's about Y'" patterns
- Banned phrases: "here's the kicker", em-dashes, watery hedging

### Phase 6: Publish + handoff

1. Create the Notion page in the client's Documents Hub
2. Move any prior versions to deprecated (rename with `[DEPRECATED v_n]` prefix)
3. Generate the Slack-ready summary using `references/slack-template.md`
4. Surface the doc link + summary to the user
5. Always include a **Source of Truth banner** at the bottom citing the Weekly Reporting Skill methodology doc
6. **Link the GDrive raw appendix folder** at the top of the Notion page under a "📁 Data Appendix" callout so the CFO can drill down if they want the source CSVs

## Storage convention (raw vs synthesized)

This skill writes to two stores. Don't mix them.

**Google Drive — raw appendix.** Path: `/Clients/[Client]/Exec Reviews/[YYYY-MM]/`. Holds:
- Raw CSVs the analyst produced (uploaded as Google Sheets so QUERY and pivots work natively)
- MD scratch notes from the analyst's competitive scan and comms sentiment pull
- Screenshots from UE Manager / DD Merchant Portal as supporting evidence
- Source platform CSV exports (UE order history, DD financial transactions) if used for YoY

File naming inside the folder follows the ticket spec exactly: `FK_Trajectory_W1_to_Wcurrent.csv`, `FK_PerLocation_Engagement_to_Date.csv`, `FK_RED_CVR_Funnel.csv`, `FK_Ratings_Velocity.csv`, `FK_Campaign_Recap_Mar_to_May.md`, `FK_Competitive_Context_by_Market.md`, `FK_Comms_Sentiment_Last_6_Weeks.md`. Predictable file names mean the synthesis step can grab them without asking Maxx where things are.

**Notion Documents Hub — synthesized deliverable.** The exec review page itself, with the narrative, charts (embedded as QuickChart PNGs), and Slack-ready summary block. Page top-of-doc carries a `📁 Data Appendix` callout linking the GDrive folder. Bottom-of-doc carries the Source of Truth banner citing the Weekly Reporting Skill methodology.

**What goes where, decision tree:**
- Is it a CSV, raw export, or table the CFO might want to slice? → GDrive
- Is it the polished narrative, chart, table that goes in front of the CFO? → Doc Hub
- Is it a screenshot used as evidence? → GDrive (then embed in Doc Hub if it's load-bearing)
- Is it the Slack-ready summary? → Doc Hub as a callout block, copy-pasteable

**Permissions.** GDrive folder defaults to Spice-internal until Maxx flips it to client-shared if Hannah asks. Doc Hub page follows the client's existing share settings (Fresh Kitchen: Spice + Hannah + Jamie + Matt).

## Adaptation per client situation

### Client with <12 months engagement (YoY still runs)
- §1 YoY same-store is still the headline. Stores have prior-year history even when Spice doesn't.
- Frame YoY as "lift vs prior-year same-stores baseline" so Hannah/the CFO sees the counterfactual cleanly.
- Pair YoY with §2 intra-year to show "here's the lift, here's the trajectory inside our window driving it."
- Pull the YoY raw-CSV ticket in Phase 0 regardless of engagement length.

### Client with new stores (<12 months operating history)
- Exclude those stores from the §1 YoY same-store calc (apples-to-apples)
- Surface them separately in §4 Portfolio Context as new-store contribution

### Client with no struggling locations / focus tier
- Skip §3
- Lens 3 column in High Level Metrics shows portfolio-best or strategic-priority location instead
- Skip the CVR funnel ticket in Phase 0

### Client with no menu CVR tracking
- §3 still possible but skip the CVR lever subsection
- Use sales trajectory + ops metrics as the leading indicators

### Client without recent communication friction
- Skip §5 (Honest Reflection)
- Move §6 (Forward Plan) up to be §5
- Don't fabricate a gap that doesn't exist
- The comms sentiment ticket still runs in Phase 0, since the analyst's sweep is what tells us whether friction exists

### Multi-tier portfolio (e.g., HealthNut, Capriotti's)
- Show tier breakdown table in §4
- Lens 3 surfaces the tier doing worst, not a single store
- Phase 0 per-location ticket expands to per-tier rollups

## Reference files

- `references/methodology.md` .  Canonical metric definitions (mirrors Weekly Reporting Skill)
- `references/output-template.md` .  Section-by-section template with examples
- `references/visual-standards.md` .  QuickChart specs, color palette, chart type decisions
- `references/voice-guide.md` .  Spice / Maxx voice rules
- `references/slack-template.md` .  Pattern for the paste-ready Slack summary
- `references/data-collection-tickets.md` .  Standard 7-ticket template (TODO: extract from this SKILL.md)

## Scripts

- `scripts/compute_yoy.py` .  Apply canonical formula to raw CSVs for prior-year baseline
- `scripts/compute_intra_year.py` .  Extract intra-year trajectory from canonical 2.0 tab CSVs
- `scripts/compute_struggling.py` .  Focus locations sales + CVR + ratings velocity
- `scripts/decompose_growth.py` .  Same-store growth attribution by platform + spend pattern
- `scripts/cvr_to_dollars.py` .  Quantify CVR lift as annualized $ at current menu view volume
- `scripts/build_chart_urls.py` .  QuickChart URL builders with consistent styling

## Common failure modes and how to avoid them

**Over-claiming Spice attribution.** When same-store grows YoY, some of that is brand momentum / market trends / repeat customer flywheel. Be honest. Use the per-platform spend pattern as the cleanest attribution signal (e.g., "UE +47% on -53% ad spend can't be brand momentum alone, requires cannibalization diagnosis").

**Mixing raw-CSV totals with canonical 2.0 tab totals.** The raw per-order sum (UE "Total payout" field, DD "Net total" field) runs ~3% higher than canonical Net Payout because it includes line items the canonical formula excludes (capital payments, certain other_payments). Always apply the canonical formula to BOTH years of raw CSVs for clean apples-to-apples.

**Faint Mermaid charts.** Mermaid xychart-beta renders 1px lines that disappear in Notion. Always use QuickChart with 4px borderWidth.

**Methodology silently changing across the doc.** If §2 uses canonical 2.0 directly but §1 uses raw per-order, the per-platform breakdown won't reconcile. Document the methodology at the bottom in the Source of Truth banner.

**Fabricating a "communication gap" for §5.** Only include the honest reflection if there's a real, recent moment (last 2-4 weeks) where the client questioned the value or surfaced friction. Don't invent one to make the doc feel "humble."

**Skipping the per-store payout YoY column.** Payout growth is the right metric for non-RED stores (per Maxx). Sales YoY alone misses the margin story. Always include payout YoY in the same-store table.

**Putting raw CSVs in Notion.** They become opaque attachments and Hannah can't slice them. Always route raw outputs to the GDrive appendix folder. Notion gets the narrative + embedded chart PNGs.

**Phase 0 tickets without a GDrive folder.** If the folder doesn't exist when the analyst starts, they dump outputs in scattered Slack threads and the synthesis step can't find anything. Provision the folder first, put the path in every ticket's Description, then create tickets.

## Sources of methodology + voice

- [Delivery Marketplaces | Weekly Reporting Skill](https://www.notion.so/spice-digital/Delivery-Marketplaces-Weekly-Reporting-Skill-30cd3ff018e781028137de464c4894d8): canonical metric definitions
- [goop kitchen × Spice | 6-Month Review v5](https://www.notion.so/36bd3ff018e7812981efeffaaebcf2e0): the prototype this skill encodes

*Built May 28, 2026 by Maxx + Claude. Phase 0 (data collection delegation) + GDrive/Notion split added May 28, 2026 after the Fresh Kitchen kickoff revealed the parallelization gap.*
