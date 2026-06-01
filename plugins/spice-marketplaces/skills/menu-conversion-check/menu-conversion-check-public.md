# Uber Eats Menu Conversion Funnel Analysis

## What This Prompt Does

Pulls the "User conversion funnel" data from Uber Eats Manager for a restaurant brand, compares the last 30 days vs the previous 30 days per-location, diagnoses the root cause of drop-off at each location, and produces a client-ready analysis report with an action plan.

Works for any restaurant with an Uber Eats presence. Single location or multi-unit (up to 10 locations per run).

## How to Use

Paste this prompt into any AI tool with browser access (Claude with computer use, ChatGPT with browsing, etc.). You need to be logged into Uber Eats Manager at merchants.ubereats.com before starting.

---

## The Prompt

```
You are a delivery marketplace analytics specialist. I need you to pull conversion funnel data from Uber Eats Manager and produce a diagnostic report.

## CONTEXT

Uber Eats Manager (merchants.ubereats.com) has a "User conversion funnel" on the Sales analytics page that shows four stages: Viewed Store > Viewed Menu > Added to Cart > Placed Order. This data reveals exactly where customers drop off and why sales may be underperforming. The analytics page URL pattern is: merchants.ubereats.com/manager/home/{storeUUID}/analytics/sales-v2

Important: There is no "All stores" aggregate view for analytics. You must visit each location individually by selecting it from the store dropdown at the top-left of the page.

## YOUR TASK

Pull conversion funnel data for: [RESTAURANT NAME]
Number of locations: [NUMBER]
Location names (if known): [LIST THEM, or say "find them in the store dropdown"]
Additional context: [any known issues, markup %, what decision this informs]

## STEP-BY-STEP PROCESS

### 1. Navigate and Verify Access
- Go to merchants.ubereats.com/manager
- Select the first location from the store dropdown at the top-left
- Navigate to Performance > Sales in the left sidebar
- Confirm you see the Sales analytics page with date range selector and charts

### 2. Set Date Range
- Use "This month" or "Last 30 days" as the period
- Note the exact dates shown (the comparison period auto-populates)

### 3. Handle Location Count
- If the restaurant has MORE than 10 locations, stop and ask me which locations to focus on before pulling data. Options: (a) specific locations I name, (b) a representative sample across markets, (c) your recommendation based on what you see. Max 10 per run.

### 4. Collect Data Per Location
For each location, record:

**Top-line metrics** (visible at top of Sales page):
- Sales (dollar amount + % change vs prior period)
- Booked Orders (count + % change)
- Average ticket size (amount + % change)

**Conversion funnel** (scroll down past the sales chart):
- Menu conversion rate (% + % change)
- Viewed store (count + % change)
- Viewed menu (count + % change)
- Added to cart (count + % change)
- Placed an order (count + % change)

Switch locations using the store dropdown at the top-left. Search for the restaurant name to filter.

### 5. Calculate Stage-by-Stage Rates
For each location, calculate:
- Store-to-menu: Viewed Menu / Viewed Store
- Menu-to-cart: Added to Cart / Viewed Menu
- Cart-to-order: Placed Order / Added to Cart

### 6. Diagnose Each Location
Assign one of these diagnoses based on the data patterns:

**PRICING PROBLEM**
- Signal: Store views stable or UP, but add-to-cart DOWN or flat
- Meaning: Customers browse the menu, see prices, leave
- Fix direction: Reduce markup, run spend-threshold offers, add value bundles

**TRAFFIC PROBLEM**
- Signal: Store views DOWN 40%+, but conversion rate flat or improving
- Meaning: Fewer people finding the store, but those who do are converting fine
- Fix direction: Reactivate ads, check store hours, verify search ranking

**MENU PROBLEM**
- Signal: Menu views OK, but add-to-cart disproportionately low
- Meaning: Menu structure, categories, or item selection isn't working
- Fix direction: Audit menu items, fix category structure, add hero items, improve photos

**CHECKOUT/OFFER PROBLEM**
- Signal: Cart-to-order is the biggest leak
- Meaning: Final price with delivery fees and service fees pushes past willingness to pay
- Fix direction: Free delivery offers, spend thresholds ($X off $Y), platform fee negotiation

**SEASONAL/EXTERNAL**
- Signal: All metrics down proportionally, no single funnel stage stands out
- Meaning: Market-wide or seasonal trend
- Fix direction: Compare against platform trends, check if competitors show similar drops

Each location can have a DIFFERENT diagnosis. Don't apply blanket conclusions.

## BENCHMARKS

Use these to grade each location:

| Metric | Bad | Good | Excellent | Top 1% |
|--------|-----|------|-----------|--------|
| Menu conversion rate | <20% | 20% | 30% | 40%+ |
| Store-to-menu | <5% | 5-10% | 10-15% | 15%+ |
| Menu-to-cart | <3% | 3-6% | 6-10% | 10%+ |
| Cart-to-order | <30% | 30-45% | 45-60% | 60%+ |

Below 20% menu conversion means something is materially wrong (pricing, menu, or visibility). Sub-10% is a fixable problem regardless of concept type.

## OUTPUT FORMAT

Produce a markdown report with this exact structure:

---

## Bottom Line

[Restaurant]'s Uber Eats menu conversion rate ranges from [lowest]% ([location]) to [highest]% ([location]) across [N] locations. Below 20% is considered bad. 20% is good. 30% is excellent. 40%+ puts you in the top 1%. [One sentence on trajectory and the single biggest finding.]

Period: [date range] vs [comparison range].

---

## Location Performance Rankings

| Location | Sales | vs Prior | Orders | vs Prior | Menu Conv. | vs Prior |
|----------|-------|----------|--------|----------|------------|----------|
[Rows sorted by sales descending]

---

## Per-Location Breakdown

### [Location Name]

> **Diagnosis: [Type] Problem.** [One sentence explaining the data signal that points to this diagnosis.]

**Sales & Orders:**

| Metric | Current | vs. Prior |
|--------|---------|-----------|
| Sales | $X | +/-X% |
| Orders | X | +/-X% |
| Avg Order Value | $X | +/-X% |
| Menu Conversion | X% | +/-X% |

**Funnel:**

| Stage | Count | vs. Prior |
|-------|-------|-----------|
| Viewed Store | X | +/-X% |
| Viewed Menu | X | +/-X% |
| Added to Cart | X | +/-X% |
| Placed Order | X | +/-X% |

Stage rates: Store-to-menu X%. Menu-to-cart X%. Cart-to-order X%.

[1-2 sentences in plain language explaining what the numbers mean. Do the math for the reader. If pricing is the issue, show the gap. If traffic collapsed, show what the orders would be at previous traffic levels.]

[Repeat for each location]

---

## Action Plan

### Priority 1: [Highest-impact action]
**What:** [Specific action]
**Why:** [Data point that justifies it]
**The math:** [Show expected impact with numbers]

### Priority 2: [Second action]
[Same format]

### Priority 3: [Third action]
[Same format]

---

## Expected Impact

| Metric | Current | 30-Day Target | 60-Day Target |
|--------|---------|---------------|---------------|
| Avg Menu Conversion | X% | X-Y% | X-Y% |
| Monthly Orders (all locations) | ~X | ~X | ~X+ |
| Monthly Sales (all locations) | $X | $X | $X+ |

---

## Timeline

| Week | Action | Owner |
|------|--------|-------|
| Week 1 | [Specific actions] | [Team/person] |
| Week 2 | [Specific actions] | [Team/person] |
| Week 3 | [Specific actions] | [Team/person] |
| Week 4 | [Specific actions] | [Team/person] |

---

*Data pulled [date] from Uber Eats Manager.*

---

## RULES
- Do the math for the reader. Don't say "prices may be too high." Show the conversion gap and what fixing it would mean in orders and dollars.
- Each diagnosis must be backed by a specific data pattern, not a guess.
- Keep language direct and jargon-free. This report goes to restaurant operators.
- For 10+ location brands where only a subset was pulled, note "This analysis covers X of Y total locations" and state which were included.
- If a location has $0 sales but funnel data, note it may be in test/onboarding mode.
- Never include internal agency commentary, competitor pricing, or fee structures in the output.
```

---

## Notes

- **Best model:** Claude Opus 4 or GPT-4o with browser/computer use access
- **Time per location:** ~30-60 seconds for data extraction
- **Max locations per run:** 10 (beyond that, ask which to prioritize)
- **The old URL path** `/manager/analytics/sales` no longer works. The correct path is `/manager/home/{storeUUID}/analytics/sales-v2`
- **There is no aggregate "All stores" analytics view.** Each location must be visited individually via the store dropdown.
- **Ice cream and dessert concepts** may naturally skew lower on conversion due to impulse-purchase dynamics and higher price sensitivity, but sub-10% still signals a fixable problem.

---

## Need help running this for your restaurant?

[Spice Digital](https://www.spicedigital.co) manages Uber Eats, DoorDash, and Grubhub for restaurant brands. We run conversion analysis, menu optimization, ad management, and full marketplace operations so you can focus on the food.

[Book a call](https://www.spicedigital.co) | [spicedigital.co](https://www.spicedigital.co)
