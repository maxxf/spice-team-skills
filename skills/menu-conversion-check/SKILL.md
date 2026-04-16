---
name: menu-conversion-check
description: >
  Pull menu conversion funnel data from Uber Eats Manager for any client, compare last 30 days
  vs previous 30 days at both the group level and per-location, diagnose what's causing drop-off
  at each location, and produce a client-ready Notion analysis page with action plan. Use this
  skill whenever the user mentions "menu conversion", "conversion check", "check conversions for
  [client]", "funnel data", "cart drop-off", "conversion rate on Uber Eats", "UE conversion
  analysis", "why aren't they converting", "check [client] conversion funnel", or any request to
  analyze customer drop-off behavior in delivery platform analytics. Also trigger when the user
  asks about "price markup impact", "are prices too high on Uber Eats", or "should we reduce
  markup" for a specific client, since conversion funnel data is the evidence needed to answer
  those questions.
---

> **Spicy Nugget handoff:** This is operational work. Delegate to Spicy. Post to #spice-ai-ops: "@Spicy Nugget check menu conversion for [client]"

# Menu Conversion Check

Pull Uber Eats conversion funnel data for a client at group and per-location level, diagnose the root cause of drop-off at each location, and produce a client-facing Notion page with the analysis and action plan.

## Why This Skill Exists

The Uber Eats Manager portal shows a "User conversion funnel" on the Sales analytics page: Viewed Store > Viewed Menu > Added to Cart > Placed Order. This data is gold for diagnosing why a client's sales are underperforming. But extracting it per-location is tedious because UE Manager requires you to filter on each individual location in a multi-store account. This skill standardizes that process and turns raw funnel numbers into a diagnosed, client-ready deliverable.

## Prerequisites

- **Chrome browser access** (Claude in Chrome MCP tools)
- **Uber Eats Manager login** for the client's account (via merchants.ubereats.com)
- **Notion MCP** for creating the output page
- Client must have an active Uber Eats presence

## Inputs Needed

Before starting, confirm with the user:

1. **Client name** (as it appears in UE Manager)
2. **Number of locations** (so you know how many to filter through)
3. **Location names** (to search for in the store dropdown)
4. **Any context** the user can provide: current markup %, known issues, what decision this data informs

If the user doesn't provide location count, check UE Manager after login and report back.

## Workflow

### Step 1: Navigate to UE Manager Sales Analytics

1. Go to `https://merchants.ubereats.com/manager`
2. If not already logged in, ask the user to log in (do NOT enter credentials)
3. Select a specific store first (the analytics page does NOT load at the "All stores" level)
4. Navigate to Performance > Sales in the left sidebar, which loads the URL pattern: `https://merchants.ubereats.com/manager/home/{storeUUID}/analytics/sales-v2`
5. **IMPORTANT:** The old URL path `/manager/analytics/sales` no longer works. The correct path is `/manager/home/{storeUUID}/analytics/sales-v2`. You must be in a single-store context to access analytics.

### Step 2: Set Date Range

1. Click the date range selector
2. Set to "Last 30 days" for the current period
3. Note the exact date range shown (e.g., "Feb 25 - Mar 26, 2026")
4. You'll use "Previous period" comparison to get the vs-prior data

### Step 3: Select Client Stores and Handle 10+ Location Cap

UE Manager shows stores from multiple clients (Spice manages 400+ stores). The store selector is a single-store context picker at the top left of the page.

**How the store selector works:**
1. Click the store name/dropdown at the top-left of the page (shows current store name)
2. A dropdown appears with a search box and a list of all stores
3. Type the client name to filter
4. Click a specific store to switch to it (this reloads the analytics page for that store)
5. There is NO multi-select or "All stores" view for analytics. Each store must be visited individually.

**10+ Location Rule:**
If the client has more than 10 locations, do NOT attempt to pull all of them. Instead:

1. Count the total locations visible in the search results
2. Tell the user: "This client has [N] locations. I can pull detailed data for up to 10. Which locations should I prioritize? Options: (a) Top/bottom performers by sales, (b) specific locations you name, (c) a representative sample across markets."
3. Wait for the user's selection before proceeding
4. In the Notion output, note that the analysis covers X of Y total locations and state which ones were included

This cap exists because pulling per-location data is sequential (one store at a time) and each takes 30-60 seconds. Beyond 10 locations the context window and time cost make it impractical.

### Step 4: Per-Location Data Collection

For each location (up to 10):

1. Click the store dropdown at the top left
2. Search for the client name
3. Click the specific location
4. Wait for the Sales analytics page to load (URL will change to `/manager/home/{storeUUID}/analytics/sales-v2`)
5. **Read the top-line metrics:**
   - Sales (dollar amount + % change vs previous period)
   - Orders (count + % change)
   - Average Order Value (amount + % change)
6. **Scroll down to "User conversion funnel"** section (below the sales chart). Record:
   - Menu conversion rate (% + % change)
   - Viewed store (count + % change)
   - Viewed menu (count + % change)
   - Added to cart (count + % change)
   - Placed order (count + % change)
7. Scroll back up and switch to the next location via the store dropdown

**Speed tips:**
- After capturing one location, use the store dropdown search to quickly switch. Don't navigate away from the analytics page.
- The URL contains the store UUID. You can navigate directly: `https://merchants.ubereats.com/manager/home/{storeUUID}/analytics/sales-v2`
- Keep a running tally in a structured format as you go (see Data Recording Format below)

**Note on group-level data:** UE Manager does not provide an aggregate "all locations" analytics view. Group-level totals must be calculated by summing per-location data. Add up sales, orders, and funnel counts across all pulled locations to derive group metrics. For menu conversion rate, use total placed orders / total viewed store as the group rate.

### Step 5: Calculate Derived Metrics

For each location and the group, calculate:

| Metric | Formula |
|--------|---------|
| Store-to-menu conversion | Viewed Menu / Viewed Store |
| Menu-to-cart conversion | Added to Cart / Viewed Menu |
| Cart-to-order conversion | Placed Order / Added to Cart |
| Store-to-order conversion | Placed Order / Viewed Store |

These stage-by-stage rates reveal WHERE in the funnel customers drop off.

### Step 6: Diagnose Each Location

This is the analytical core. For each location, determine which of these archetypes fits:

**Pricing Problem** (most common)
- Signal: Store views stable or UP, but add-to-cart DOWN significantly
- Translation: People find the store, browse the menu, see prices, and leave
- Fix: Reduce markup, run spend-threshold offers, add value bundles

**Traffic/Distribution Problem**
- Signal: Store views DOWN dramatically (40%+), but conversion rate flat or improving
- Translation: The few people who find the store are converting fine. Nobody's finding it.
- Fix: Reactivate ads, check search ranking, verify hours/availability

**Menu Problem**
- Signal: Menu views reasonable, but add-to-cart disproportionately low OR wrong items showing
- Translation: The menu doesn't match what customers expect from this brand
- Fix: Audit the actual menu items, fix category structure, add missing hero items

**Offer/Promo Problem**
- Signal: Cart-to-order drop is the biggest leak (people add items but don't complete)
- Translation: The final price with fees pushes past the customer's willingness to pay
- Fix: Free delivery offers, spend thresholds ($X off $Y), reduce delivery fee via platform negotiation

**Seasonal/External**
- Signal: All metrics down proportionally, no specific funnel stage stands out
- Translation: Likely seasonal, weather, or market-wide trend
- Fix: Compare against platform-wide trends, check if competitors show similar patterns

Each location can (and often does) have a different root cause. Resist the temptation to apply a blanket diagnosis.

### Step 7: Build the Client-Facing Notion Page

Search Notion for the client's workspace page, find the Document Hub database, and create a new page.

**Page structure (follow this template):**

```
## Bottom Line
[2-3 sentence summary: conversion rate range across locations, benchmark
comparison, trajectory, and the single biggest finding]

---

## Location Performance Rankings
[Table: Location | Sales | vs Prior | Orders | vs Prior | Menu Conv. | vs Prior]
[Sorted by sales descending. Max 10 rows.]

---

## Per-Location Breakdown

### [Location Name]
[Callout block with color-coded diagnosis: red=pricing, yellow=traffic, orange=menu]
[Metrics table]
[Funnel table]
[1-2 sentences explaining what the numbers mean in plain language]

[Repeat for each location]

---

## Action Plan

### Step 1: [Highest-impact action]
What, why, and the math showing expected impact

### Step 2: [Second action]
...

### Step 3: [Fix fundamentals]
...

---

## Expected Impact
[Table: Current vs 30-day target vs 60-day target for conversion rate, orders, sales]

---

## Timeline
[Table: Week 1-4 with specific actions and owners]

---

*Data pulled [date] from Uber Eats Manager. Prepared by Spice Digital.*
```

**Notion formatting rules:**
- Use `<callout>` blocks with colored backgrounds for diagnoses (red_bg, yellow_bg, orange_bg)
- Use `<table>` with `header-row="true"` for all data tables
- Bold the diagnosis label in each callout
- Keep prose direct and jargon-free. This goes to the client.
- Do the math for the reader. Don't say "prices are too high." Show the delivered price calculation.
- Include the benchmark context: Below 20% is bad. 20% is good. 30% is excellent. 40%+ is top 1%.
- For 10+ location clients, the rankings table should show only the locations that were pulled, with a note about total location count

**Notion page properties:**
- Title: `[Client] Menu Conversion Analysis - [Month Year]`
- Category: "Strategy doc"
- Client: link to the client's page in the Clients database
- Icon: chart emoji

### Step 8: Share with User

After creating the Notion page, share the link. Summarize the key findings in conversation:
- The headline diagnosis for each location
- The recommended first action
- Any questions or decisions that need the user's input before proceeding

## Data Recording Format

Use this structure while collecting data to stay organized:

```
CLIENT: [name]
PERIOD: [date range] vs [comparison date range]

GROUP:
  sales: $X (Y%)
  orders: X (Y%)
  aov: $X (Y%)
  menu_conversion: X% (Y%)
  funnel:
    viewed_store: X (Y%)
    viewed_menu: X (Y%)
    added_to_cart: X (Y%)
    placed_order: X (Y%)

LOCATION: [name]
  sales: $X (Y%)
  orders: X (Y%)
  aov: $X (Y%)
  menu_conversion: X% (Y%)
  funnel:
    viewed_store: X (Y%)
    viewed_menu: X (Y%)
    added_to_cart: X (Y%)
    placed_order: X (Y%)
```

## Benchmarks Reference

| Metric | Bad | Good | Excellent | Top 1% |
|--------|-----|------|-----------|--------|
| Menu conversion rate | <20% | 20% | 30% | 40%+ |
| Store-to-menu | <5% | 5-10% | 10-15% | 15%+ |
| Menu-to-cart | <3% | 3-6% | 6-10% | 10%+ |
| Cart-to-order | <30% | 30-45% | 45-60% | 60%+ |

Menu conversion rate benchmarks are from Uber Eats platform standards. Below 20% means something is materially wrong (pricing, menu, visibility). Ice cream and dessert concepts can skew lower due to impulse-purchase dynamics and higher price sensitivity, but sub-10% still signals a fixable problem.

## Edge Cases

- **Client has 1 location:** Skip the "Location Performance Rankings" table. The per-location section IS the entire analysis. Focus on funnel stage diagnosis.
- **Client has 10+ locations:** Enforced by the 10-location cap in Step 3. Ask the user which locations to focus on. In the Notion output, state "This analysis covers [X] of [Y] total locations" and list which ones were included. The per-location breakdown section should show a maximum of 10 locations.
- **Client has 2-3 locations:** No group summary needed since you can see everything in the per-location sections. Still include the rankings table at the top for a quick comparison.
- **No funnel data showing:** The User conversion funnel may not appear if the date range is too short or the store has very low traffic. Try expanding the date range to 60 days or switching the date picker to "This month."
- **UE Manager shows $0 sales but has funnel data:** The store may be in a test/onboarding state. Note this in the report.
- **Multiple brands under one account:** Filter carefully. Some clients (like AWAN/Dayglow) have sister brands in the same UE Manager account. Make sure you're only pulling the target brand's locations.
- **Date range defaults to "This month":** UE Manager typically defaults to "This month" with a comparison to the same period in the prior month. This is fine for the analysis. If the user wants a specific date range, use the date picker to adjust.

## What NOT to Include in Client-Facing Output

- Raw Spice internal commentary or Slack references
- Specific payout percentages or commission details
- Competitor pricing data (save for internal analysis)
- Spice's fee structure or margin calculations
- Internal team member names (use "Spice Team" as owner)
