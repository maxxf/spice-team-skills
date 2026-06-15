# Spice Brain: Delivery Marketplace Playbook

> Synthesized learnings from Spice Digital's delivery marketplace service. Everything we know, battle-tested across goop Kitchen (13 locations), Capriotti's (140+), Everytable (38), Brooklyn Dumpling Shop, and the rest of the portfolio.
>
> **Last updated: June 2026** (prior: February 2026)
>
> **Scope:** delivery **marketplaces** only — Uber Eats, DoorDash, Grubhub. Meta/paid social is a separate service line and isn't tracked in the marketplace campaign plan. (When Meta intersects marketplace performance — see incrementality work — it shows up in attribution decomposition, not as a marketplace channel.)

---

## 0. The Governing Law: The Spend Maturity Curve

The unifying frame under everything below — the 3% north star, the cannibalization audit, the incrementality work, and every per-location spend decision a GM makes. State it as a law:

**3P marketing spend is acquisition spend wearing a conversion costume.** The ROI of a marketing dollar is a function of *where the location sits on its awareness curve*, not of how well the location performs. The same dollar does opposite things at the two ends:

- **Mature location** — you already own the demand. Spend largely buys orders you'd have gotten anyway, so it **cannibalizes**; pulling it back *lifts* net payout. Harvest end of the curve.
- **New / dark / scaling location** — spend is the only thing acquiring new eaters. Pulling it **bleeds** — you switch off the engine. Acquisition end of the curve.

**The proof points (cross-client — this is a law, not one client's quirk):**

| Location state | What happened | What it proves |
|---|---|---|
| Mature (Ahipoki) | Pulled $65–70K of 3P spend over 4 months → sales stayed flat | Spend was cannibalizing; demand was already owned |
| Mature (Counter Service) | Held spend flat, *reallocated* it → +23% sales | On a mature base, mix beats volume |
| Struggling accounts | Cut spend → net payout up to +11% | Cannibalization, quantified in payout |
| Dark (Capriotti's) | Went dark on Uber Eats → −$480K/quarter + 23% drop in new-eater acquisition | The other end: spend *was* the acquisition engine |

**Implications that cascade through the rest of this playbook:**

- **ROAS is not a performance grade — it's a position on the curve.** A high ROAS at a mature store is harvesting demand you already own; a low ROAS at a new store is the cost of buying eaters who don't exist yet. Never rank stores on raw ROAS.
- **Incrementality tests (§4) are how you *locate* a store on the curve** — a stepped pullback tells you whether spend is incremental (acquisition end) or cannibalizing (harvest end). That's the measurement, ROAS is not.
- **The Cardinal Rule (§1) is the off-curve gate** — a broken store isn't anywhere on the curve yet; fix foundations before it earns a position.
- **The location tier framework is this curve made operational** (`references/tier-framework.md`): maturity (capacity + awareness) sets the goal, the goal sets the spend band. Top = harvest (0–3%), Mid = transitional (4–8%), Low/New = acquisition (8–20%), Red = off-curve.
- **Net payout is the north star at the harvest end; new-eater acquisition is the north star at the acquisition end.** Same business, different objective function by curve position — which is why "goal" (payout vs growth) is set per location, not per client.
- **Segment the ads to read (and cap) the curve.** Every store except brand-new ones runs ads split by audience (New / Existing / Lapsed), not one blended campaign — a blended line can't tell acquisition from cannibalization. Per-segment ROAS/CPO is the cheap, always-on read of curve position (the stepped pullback is the expensive confirmation); per-segment budget caps are how you enforce it — cap the existing-customer spend on a mature store, give the new-customer segment headroom on a scaling one. New stores run blended until they have a base, then segment at the 60-day re-tier.

---

## 1. The Cardinal Rule: Fix Foundations Before Spending

Every failed marketplace engagement we've seen traces back to the same mistake: throwing ad dollars at a broken storefront. The hierarchy is non-negotiable.

**Before any marketing spend, these thresholds must be met:**

- Ratings above 4.5 (if not, fix quality/packaging/accuracy issues)
- Error rate below 2% (if not, work with kitchen on order accuracy)
- Uptime above 95% (if not, address staffing/hours/tablet issues)
- Menu photos on 90%+ of items (if not, schedule a photo shoot)
- Menu priced correctly for delivery with 15-20% markup over dine-in

A 4.3-star store with 3% inaccuracy will waste ad dollars every time. We've watched it happen. The algorithm punishes poor ops metrics harder than it rewards ad spend.

---

## 2. Platform Intelligence

### DoorDash
- Dominates Bay Area and suburban markets
- Algorithm rewards: high ratings (4.5+), low error rates, consistent uptime, menu completeness
- DashPass visibility is critical. Most orders come from subscribers
- Promotions most effective on weekday lunch (highest competition) and late night (lowest)
- Ad types: Sponsored Listings (CPC), Promotions (discount-funded)
- Sponsored Listings typically run 8x+ ROAS when fundamentals are clean
- Start at $0.50-$1.00 CPC, test 3 ad groups, measure 7-day ROAS
- Tablet disconnection issues directly cause lost orders. Silver Lake lost ~20 estimated orders from a single outage dropping uptime to 91.4%
- **Friday-depth tweak (added June 2026):** deeper promo on Friday only, standard depth other days, takes share at peak auction without bleeding margin all week. Drove goop Pasadena to best-of-year sales week. Pair with ratings flyer to compound the volume-spike review flywheel.

### Uber Eats
- Leads in major metros: LA, NYC, Chicago
- Algorithm rewards: acceptance rate, preparation time accuracy, photo coverage
- Uber One members drive disproportionate volume. Optimize for subscriber discovery
- Better ad platform than DoorDash. More targeting options, better ROAS tracking, audience segmentation for new customer acquisition
- Photo quality matters more on UE than DD. Invest in professional hero image
- Prep time accuracy directly impacts algorithm ranking. Work with kitchen to set realistic times, not aspirational ones
- Restaurant Ads (auto-bidding) for launch, manual bidding after 14 days of data
- Geo-targeted ads show promise for location-specific acquisition

### Grubhub
- Declining market share but still relevant in legacy markets (NYC, Chicago)
- Lower commission rates can mean better unit economics
- Less sophisticated ad platform
- Worth maintaining presence but rarely the primary growth lever
- When to invest: NYC/Chicago markets, corporate/catering volume, competitor gap to exploit, or significantly lower commission rates
- AOV tends to be more sensitive to pricing on GH. Test bundle offers to lift AOV at underperforming locations
- Modifier mapping errors are the most common source of GH-specific error rate spikes

---

## 3. The Attribution Problem (Critical Learning)

This is the single most important thing we've learned. It took forensic data work on goop Kitchen to uncover, and it changes how we evaluate every dollar of marketplace spend.

### The Flaw
Uber Eats' merchant dashboard conflates two different things:
1. Orders attributed to paid ads (actual ad-driven orders)
2. Orders that had an active promotion applied (promo-attributed orders)

When promos only run at 1-2 stores but ad spend runs across all 12, the dashboard counts orders with promos as "marketing orders" while orders from ad spend at the other 10 stores get bucketed as "organic."

### The Numbers
- Weeks 43, 45, 46 (2025): 70-83% of ad spend was generating orders incorrectly classified as organic
- Week 44: all stores had promos running, so 100% was properly attributed
- The ROAS didn't change week to week. The measurement did. Wild swings from 0.9x to 2.2x were purely a measurement artifact

### The Fix
Always pull data from Uber Eats Ads Manager (which tracks actual ad-attributed orders) separately from merchant-funded offer tracking. These are different systems measuring different things. Build reporting that separates:
- True Ad ROAS by store (from Ads Manager)
- True Promo ROAS separately (from merchant portal)
- A blended view that actually captures the full picture

### The Implication
Blended cost-per-order metrics can mask unprofitable new customer acquisition patterns. Always decompose into: new customer acquisition cost (not blended CPO), organic vs. paid order split, repeat rate by acquisition channel, and revenue per customer over 90 days.

---

## 4. Incrementality Testing Framework

Developed for goop Kitchen's "Unicorn" locations (Beverly Hills, Costa Mesa, Venice, SoMa). This is our methodology for answering the question every restaurant should ask: "If we stopped spending, would the orders still come?"

### Design: Staggered Stepdown
Not a simple on/off test. Too risky for locations doing $100K+/week.

**Phase 1 (Light Pullback, -25%):** Reduce total marketplace ad spend by 25%. Keep all campaign types active, lower daily caps.

**Phase 2 (Moderate Pullback, -50%):** Cut spend in half. Eliminate lowest-ROAS campaign types first (usually broad Uber promos). Keep DoorDash sponsored listings running.

**Phase 3 (Aggressive Pullback, -75%):** Retain only always-on DoorDash sponsored listings and new customer offers. Kill broad promos, frequency campaigns, existing customer retargeting.

### Sequencing Logic
Stagger location entry so you always have comparison points. BH and Costa Mesa go first (most stable). SoMa enters last (ops issues would confound results). Venice watches BH results before moving.

### Key Learnings So Far
- SoMa went from $15K to $2.2K/week in Uber spend. Sales barely moved. That's the incrementality signal we're looking for
- A 16% blended reduction across all 4 locations was the accidental Phase 1 after Rodrigo moved to dinner-only ads ($1,500/store/week, $3 min bid) before the formal plan kicked in
- Using prior weeks as baseline works when the pre-test data is clean (no other major ops/menu/hours changes)

### What to Measure
Track weekly by location: total orders, GMV, net payout, organic order share, paid order share, platform-reported ROAS, true incremental ROAS, and the delta between the two. Net payout is the north star for goop. Revenue that doesn't improve net payout is noise.

---

## 5. Multi-Location Delivery Radius Strategy

Developed from goop Kitchen's LA network analysis (7 locations). This applies to any multi-location client.

### The Overlap Problem
Larchmont sits in a 4-way collision zone. Its 8km (~5 mile) default Uber Eats radius overlaps significantly with Beverly Hills, Silver Lake, Studio City, and Pico Robertson. Only 20-30% of Larchmont's radius is net-new addressable territory (a narrow corridor east toward Koreatown, Hancock Park, DTLA fringe).

### Strategic Implications
- Ads served in overlap zones reach customers who may already order from another location. Effective CPA for truly incremental customers could be 2-3x what dashboards report
- If you pull back spend on one location, the overlap-zone location may absorb those orders, or they may just evaporate. This is the most valuable experiment to run
- Use the cleanest location (Pasadena, with near-zero overlap) as the benchmark for what a new launch "should" generate per unique household, then discount expectations by overlap factor

### Tactical Recommendations
- Negotiate custom delivery polygons with platform reps. Ethan (UE) confirmed these are "situationally supported for exclusive partnerships." With 7+ locations, there's leverage
- Reframe the new location's target market around its unique territory, not the contested zones
- Set up location-vs-location order volume tracking from day one to quantify self-cannibalization
- Incorporate overlap as a variable in incrementality testing

---

## 6. New Client Launch Playbook (First 30 Days)

### DoorDash
Days 1-3: Audit (rating, error rate, uptime, menu completeness, photo coverage, pricing vs. competitors)
Days 4-14: Fix foundation. Priority order: errors > uptime > photos > pricing > menu structure
Days 7-21: Optimize menu (restructure categories, add modifiers, optimize descriptions, 90%+ photo coverage)
Days 14-21: Launch promotions (start low-risk: free delivery for new customers, % off first order)
Days 21-30: Activate Sponsored Listings ($0.50-$1.00 CPC, 3 ad groups, measure 7-day ROAS)

### Uber Eats
Days 1-3: Audit (rating, acceptance rate, prep time accuracy, menu quality score)
Days 4-14: Fix foundation (prep time calibration, acceptance rate optimization, menu accuracy)
Days 7-21: Optimize menu (hero image, category structure, upsell items, combo deals)
Days 14-30: Launch Restaurant Ads (auto-bidding first, manual bidding after 14 days)

### Grubhub
Default to maintenance mode unless NYC/Chicago market or specific strategic reason to invest. Keep menu current, monitor ratings, respond to reviews, minimal ad spend.

---

## 7. Ongoing Optimization Cadence

**Daily:** Check marketplace alerts, cancellations, negative reviews
**Weekly:** Pull performance snapshot, adjust bids, refresh promotions
**Biweekly:** Competitive pricing check, menu seasonal updates
**Monthly:** Full performance review, incrementality check, strategy adjustment
**Quarterly:** QBR prep, trend analysis, budget reallocation

---

## 8. Promotion Strategy Matrix

| Goal | Tactic | Target Segment | Expected Impact | When to Use |
|------|--------|----------------|----------------|-------------|
| New customer acquisition | $X off first order | **New** | High volume, lower quality | Launch phase, slow periods |
| Reactivation | Free delivery for returning | **Lapsed** | Medium volume, good retention | After 30+ days dormant |
| AOV increase | Spend $X get $Y off (AOV-calibrated) | **Existing** or **All** | Lower volume, higher margin | Established accounts |
| Subscriber retention | Exclusive offer / loyalty | **DashPass** (DD) / Uber One (UE) | High repeat rate | High-subscriber markets |
| Visibility boost | Featured placement bid | **All** | Brand awareness | Competitive markets |

**Customer Segment is a first-class planning dimension** (added June 2026). Every offer specifies its target segment from {New, Existing, Lapsed, DashPass, All}. Tracked in the Campaign Planning DB's `Customer Segment` field; rolled up on the campaign-plan dashboard as a By-Segment performance table. Stops the blanket-promo subsidy of buyers who'd convert anyway.

**Calibrate Spend X Save Y to AOV.** Spend threshold should sit within 10-15% above the location's AOV. If it's 30%+ above, you only catch over-orderers and miss the threshold-buyer mechanic. Goop SJ: aggressive (lower threshold) tier drove conversion 25% → 33% where conservative tier had stalled.

### Platform Co-Marketing Offers (How to Evaluate)
Learned from declining Uber Eats' March Madness campaign for goop:
- Always check if the campaign window conflicts with any active testing
- "All eater" broad promos at 40%+ savings are the exact channel proven to be non-incremental for established locations
- Platform lift claims (+20% sales) measure during vs. before, not incremental vs. counterfactual. Same attribution gap
- Exception: "Deals Hub only" tier for newer locations still building awareness, if promo economics pencil out (model cost per redemption, expected new customer %, breakeven)
- Frame declines diplomatically: "being strategic about promotional cadence this quarter"

---

## 9. Client Health Signals

| Signal | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Rating | >4.5 | 4.2-4.5 | <4.2 |
| Error rate | <2% | 2-5% | >5% |
| Uptime | >95% | 90-95% | <90% |
| MoM revenue trend | Growing | Flat | Declining 2+ months |
| Client responsiveness | Same-day | 2-3 days | Ghost mode |

---

## 10. Reporting & Metrics That Matter

### Weekly KPI Snapshot (Per Location, Per Platform)
Orders, GMV, net payout, AOV, error rate, avg prep time, uptime, rating. Always show WoW delta.

### What to Always Decompose
- New customer acquisition cost (not blended CPO)
- Organic vs. paid order split
- Repeat rate by acquisition channel
- Revenue per customer over 90 days
- Net payout % (the metric that actually matters to restaurant operators)

### Reporting Cadence to Client
- EOW Slack/email snapshot with 3-5 bullets: what's up, what's down, what's next
- Monthly deep dive with insights and action items
- Quarterly QBR deck with strategic recommendations

### Quality Gates
- No campaign goes live without GM review
- No client communication without proofread
- No spend increase >20% without data justification
- No new platform feature adoption without testing on 1 client first

---

## 11. Pricing Model

- Monthly retainer, capped at $5K/location group for marketplace management
- Loop analytics always charged separately: $60/location/month on top of base retainer
- Performance-based pricing for paid acquisition services
- Lower retainer, higher margin for advisory-only engagements

---

## 12. Operational Lessons (Hard-Won)

1. **Modifier mapping errors are the #1 source of preventable error rate spikes on Grubhub.** Always audit modifier groups after menu changes.

2. **Tablet disconnection = lost revenue.** A single Silver Lake outage cost ~20 orders. Escalate immediately and open platform support tickets same-day.

3. **Prep time accuracy is an algorithm input, not just an ops metric.** Overpromising prep times tanks ranking. Work with kitchens to set realistic times.

4. **DashPass and Uber One subscribers drive disproportionate volume.** Menu optimization for subscriber discovery is as important as ad spend.

5. **Blended CPO across a multi-location portfolio hides location-level problems.** Always look at per-location, per-platform metrics.

6. **Net payout is the north star.** Not GMV, not order count. What the restaurant actually takes home after platform fees, commissions, and marketing costs.

7. **When evaluating platform co-marketing offers, ask: is this incremental or am I subsidizing orders that would have happened anyway?** The answer is usually the latter for established locations.

8. **Menu pricing for delivery should be 15-20% above dine-in to account for commission.** Clients resist this but it's mathematically necessary for healthy unit economics.

9. **Photo quality has a measurably larger impact on Uber Eats than DoorDash.** Prioritize UE hero images and item photography.

10. **The best incrementality signal comes from SoMa-style natural experiments.** When spend drops dramatically and sales barely move, you have your answer. Document these moments obsessively.

11. **Make blocked items visible to the client, with day counts.** (Added June 2026.) Surface "Blocked-on-client" status with days-in-queue on the campaign plan. Hidden blockers stay blocked; visible blockers move. The goop BOGA sat 11 days unseen — once the new plan exposed the count, client approved within 48 hours. Every client plan now shows this.
