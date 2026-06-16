# Output Template

The complete section-by-section template. Copy structure verbatim; fill in client-specific data.

## Page metadata block

```
> **For:** [Primary client decision-maker] + [CFO/finance contact] + the [client] team
> **From:** [Spice Service Lead name] (Spice)
> **Period covered:** [SOW start date] through W[n] of [year] ([Mon-Sun date range])
```

## TL;DR (always at top)

6 bullets, each one line, leading with the strongest number. Always include:

- **Same-store YoY** (if engagement ≥12 months): + sales / + payout / +/- ad spend
- **Platform cannibalization story** (if applicable): UE or DD ad spend cut + sales/payout growth
- **Portfolio scale** (if expansion): N → M stores, $X → $Y total sales
- **Marketing efficiency**: TMI/Sales improved A% → B%, ROAS Xx → Yx
- **Struggling locations growing** (if applicable): per-location % growth
- **Leading indicators validated** (if menu CVR + ratings tracked): pre → post change
- **Communication gap owned** (if §5 applies): structural fix shipping this week

Close with a single one-liner ask: "60-90 days of runway at [location]. Approve [parked campaign]. Approve [test]."

## High Level Metrics table

Always 3 columns × 4 rows. The lenses adapt per client.

| Metric | Lens 1: YoY (same-store ex-closing) | Lens 2: Intra-year (portfolio, W1 → W_n) | Lens 3: Struggling locations |
| :-- | :-: | :-: | :-: |
| **Total Sales** | $A → $B (+X%) | $C → $D/wk (+Y%) | Loc1 +%, Loc2 +% vs baseline |
| **Net Payout** (the cash story) | $A → $B (+$delta, +X%) | $C → $D/wk (+$delta/wk, +Y% → +$annualized) | Loc1 +%, Loc2 +% vs baseline (~$annualized) |
| **Marketing Spend** | $A → $B (% absolute, A% → B% of sales) | $C → $D/wk (-Y%, A% → B% of sales) | Loc1 A% → B%, Loc2 A% → B% of sales |
| **ROAS** | Xx → Yx blended sales/$mkt | Xx → Yx marketing ROAS (+Z%) | Loc1 Xx → Yx, Loc2 Xx → Yx |

## §1 YoY Same-Store

Intro: "N stores active in both [prior year] W1-W[n] and [current year] W1-W[n], excluding [closing/winding-down location]."

Per-store table:

| Store | Tier | Sales [prior] → [current] | Sales YoY | **Payout YoY** (the cash growth) |
| :-- | :-: | :-: | :-: | :-: |
| Store1 | TIER | $A → $B | +X% | **+Y%** ($A → $B) |
| ... | ... | ... | ... | ... |
| **N-store total** | | **$A → $B** | **+X%** | **+Y%** ($A → $B = **+$delta**) |

Closing/winding-down callout (one line): "[Location]: $A → $B (-X%) as it wound down."

### Optional sub-sections (include only when relevant)

**Platform Cannibalization Fix**: only if one platform shows sales growth on ad spend reduction. Same 4-bullet pattern: Ad Spend cut, Sales grew, Payout grew, TMI net.

**[Outlier Store] update**: only if any same-store grew sales <10% or shrank. Re-frame with payout if profitability still improved.

**Marketing mix shift**: explain UE/DD reallocation if it happened. Most important: was total spend up or down, and was % of sales improving?

## §2 Intra-Year Trajectory

Intro: "W1 ([first full week date]) vs W[n] ([most recent week]), portfolio level."

**Charts** (use QuickChart, not Mermaid):

1. Weekly Total Marketing Spend ($K): line chart, red
2. Marketing ROAS: line chart, teal

**Bullets:**

- Total weekly sales: $A → $B (+X%)
- Total marketing spend: $A → $B (Y%), broken into ad spend Y% and offer spend Y%
- ROAS: Xx → Yx (+Z%)
- Net payout: $A/wk → $B/wk (+X%)
- Inflection point: W[n] ([date]): what happened that week

Closing line: "Annualized at W[n] run-rate: **+$X payout** on **$Y less** total marketing spend vs early-engagement baseline."

## §3 Struggling Locations Progress

Intro: Reframe if locations are NEW (opened in last 6 months) vs legacy struggling. "[Loc1] + [Loc2] opened [date] (no prior-year baseline). Classified [TIER] for early performance below the $[X]/day target. The work is accelerating new-store maturity, not turning around legacy stores."

**Lever 1: Menu CVR** (if tracked)
- QuickChart bar: SJ Before / SJ After / Pas Before / Pas After
- Per-location % point lift + relative funnel gain
- Honest note if any concern (e.g., "Robert flagged the menu changes as hard for GEMs to maintain when items 86")

**Lever 2: Ratings Velocity** (if program is running)
- QuickChart bar: Before / After per location
- W_recent snapshot: organic share % per platform per location

**Sales Trajectory:**
- QuickChart dual-line: location 1 + location 2 weekly sales
- Per-location table: Jan baseline, W_n current, % change

**Per-location metrics table:**

| Metric | Loc1 Jan | Loc1 W_n | Loc2 Jan | Loc2 W_n |
| :-- | :-: | :-: | :-: | :-: |
| Weekly sales | $A | **$B** (+X%) | $A | **$B** (+X%) |
| **Weekly net payout** | $A | **$B** (+X%, +$delta/wk) | $A | **$B** (+X%) |
| Mkt Spend % | A% | B% | A% | B% |
| ROAS | Ax | Bx | Ax | Bx |
| Menu CVR (if tracked) | A% | **B%** | A% | **B%** |

**The ask:** "60-90 more days of runway. Leading indicators have moved meaningfully. Sales are starting to follow."

## §4 Portfolio Context (only if expansion happened)

Intro: "[N] new locations opened. Total business +X%."

Table: stores, total sales, contribution split (same-store vs new-store growth points).

Callout: "Standout: [Location] opened [date], now the #N location in the portfolio at $X/wk on Y% marketing spend."

## §5 Competitive Context (skip if no competitive data)

Where the client sits relative to category benchmarks and nearest competitors.

**Sources to pull from:**
- Most recent storefront audit of the client (if one exists in their Notion space)
- Storefront audits of named competitors in the same category and geos
- Public marketplace data: hero images, menu structure, pricing, promo cadence visible on merchant landing pages
- Internal Spice benchmarks: anonymized aggregates across the client's category (fast-casual, healthy bowls, pizza, etc.)

**Section structure:**

Short intro framing the competitive set. "We benchmarked [client] against [3-5 named competitors] across the same delivery markets."

Then 3-4 sub-areas:

1. **Storefront positioning**: hero image grade, menu structure clarity, promo cadence vs competitors. Qualitative table (you / competitor 1 / competitor 2 / category median).
2. **Pricing position**: AOV and price-per-item vs competitors. Premium / parity / discount? Honest read.
3. **Marketing intensity**: how aggressive is competitor ad spend / promo activity at the same locations. Sourced from observed marketplace state, not platform analytics.
4. **Where we have edge / where we lag**: 2-3 specific calls each way. Don't shy from honest lag callouts.

**Closing callout:** "What this means strategically: [1-2 sentences on the implication for the forward plan]."

Skip this entire section if:
- No storefront audit exists for the client
- The client has no clear competitive set in their delivery markets
- The audit data is older than 4 months and would mislead

## §6 Honest Reflection (only if applicable)

Quote block (Notion callout, gray bg, 💬 icon): the verbatim Slack/email quote from the Spice lead.

Three sub-sections with emoji headers:

- **⚡ The pattern**: bullets showing the work has been fast (specific examples with dates)
- **🕳️ The gap**: bullets showing where visibility didn't keep up
- **🎯 Where we owe better**: the structural fixes

### Three structural fixes table

| Fix | When |
| :-- | :-: |
| [Specific commitment 1] | This week |
| [Specific commitment 2] | First [date] |
| [Specific commitment 3] | W_n update |

Close: "If we miss [commitment], that's a failure. Call it out."

## §6 Forward Plan (next 90 days)

**Group priorities** (3-5 bullets):
- Hold [winning playbook]
- Launch [pending launch]
- Hold [ops gate] until [metric clears threshold]

**Struggling-locations KPIs** table:

| Bet | Target | Cadence |
| :-- | :-: | :-: |
| Menu CVR | A%+ for N weeks | Weekly |
| Ratings velocity | A+/wk for N weeks | Weekly |
| [Location] weekly gross | $X for N weeks | Weekly |

Tripwire line: "If [leading indicator] reverses 3+ weeks, we send a re-eval memo immediately."

**Asks for [client]** (numbered list):
1. **[Specific runway ask]**
2. **[Specific approval ask]** (parked X days)
3. **[Specific test ask]**

## §7 Questions We Expect

Short Q&A bullets in the client's voice:

- **[Anticipated question]?** [One-paragraph honest answer.]

Common questions to anticipate:
- "Are [struggling locations] turnarounds or new stores?"
- "Spice attribution?"
- "Why is [struggling tier] mkt spend at X%?"
- "[Most recent ops issue]?"
- "Why did this review take [X months]?"

## Source of Truth section (always at bottom)

```
## Source of Truth (reconciled [date] to canonical Weekly Reporting Skill methodology)

Methodology per [Delivery Marketplaces | Weekly Reporting Skill](url):
- **Total Sales** = food subtotal EXCLUDING tax
- **Net Sales** = Total Sales − Discounts
- **Net Payout** = Net Sales − Commissions − Ad Spend − Other Adjustments
- **Net Payout %** = Net Payout ÷ Total Sales × 100

[Current period] numbers come directly from canonical 2.0 tabs.
[Prior period] numbers come from raw CSVs with the same formula applied.

| Doc section | Source | Reconciled? |
| :-- | :-- | :-: |
| Lens 1 / §1 | Raw CSVs (with canonical formula applied) | n/a (2.0 tabs don't span prior year) |
| Lens 2 / §2 | Weekly Platform Overview 2.0 | ✅ |
| Lens 3 / §3 | By Location 2.0 + Ops - Focus Locations | ✅ |
| §4 | By Location 2.0 | ✅ |
```

## Sources (always at bottom)

Links to:
- Data Appendix (companion page if created)
- Campaign Plan
- Most recent W_n weekly update
- Weekly metrics workbook
- Any client-specific diagnostic pages
- Raw YoY data files
