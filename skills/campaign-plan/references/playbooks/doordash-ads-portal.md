# DoorDash Ads Portal — verified reference

_First documented 2026-07-27 from direct observation on a 20-store enterprise DD account (goop Kitchen), plus that client's W29 campaign pull. Everything here was observed directly or is arithmetically derivable from observed data._

**Scope rule for this file:** the rules are client-agnostic; client names appear only as receipts for a specific observation. No account IDs, no client-specific dollar figures except where a number is the proof of a general mechanic (e.g. the order-rate identity in §6). Running client numbers live in the client record, not here.

**Confidence key used throughout:** ✅ observed directly · ⚠️ observed once, needs a second account to confirm it generalises · ❓ hypothesis, do not report as fact

---

## 1. Where things are now

✅ Marketing moved from `mxportal.doordash.com` to **`ads.doordash.com/portal/business/<business_id>/`**. Financials and Operations Quality stayed on the merchant portal. Both are needed for a full pull.

✅ Four tabs, with these exact route slugs:

| Tab | Route |
|---|---|
| Performance | `/performance` |
| Customer insights | `/customer/insights` |
| Campaigns | `/campaigns` |
| Reports | `/reports` |

✅ Note the Customer insights slug is `/customer/insights`, **not** `/customer-insights`. The hyphenated form returns "Page not found," which reads like a permissions problem and isn't.

## 2. What the portal now exposes that it didn't before

### Customer insights — three modules ✅

1. **Customer breakdown.** Total / new / lapsed / existing customers, with a toggle between **Customers from ads** and **Overall customers**. Daily time series with campaign-change annotation markers on the x-axis.
2. **Customer purchase trends.** Twelve-month recency decay across four buckets: `<45d`, `45–90d`, `90d–6mo`, `6mo–1y`, plus a total active-customer count. This is the lapsed-pool sizing tool.
3. **Customer long-term value over 90 days.** Average customer value, average ticket, average order rate. Has a **New customers** tab and a **Lapsed customers** tab.

⚠️ There is **no Existing-customer tab** in the LTV module. We have measured 90-day value for New and Lapsed cohorts only. Any claim about existing-customer value is modelled, not measured.

### Performance tab ✅

- **Ads summary** and **Promotions summary** as separate cards, each with its own sales / orders / spend / ROAS
- Total sales decomposed into **Organic / Ads / Promo / Ads+Promo**
- **Performance by daypart**, six dayparts (early morning, breakfast, lunch, afternoon, dinner, late night), trendline or heat map
- **Average category share** — your share of sales in your top dish categories against competitors in your submarkets, with YoY comparison
- A line reporting "Your DoorDash marketing credit boosted your sales by `N`x"

### Reports tab ✅

- Report type: **Campaign performance**
- **View by:** `Day, Store` or `Day, Ad group`
- Reports are named freely by whoever creates them and persist in a flat list

## 3. Data freshness and timezone gotchas ✅

These are stated on the page and are easy to miss. They matter when reconciling.

| Surface | Freshness | Timezone basis |
|---|---|---|
| Customer breakdown | Daily, **two-day delay** | — |
| Customer purchase trends | Daily, trailing 12 months | — |
| Customer long-term value | Daily | — |
| Ads summary | Own timestamp | — |
| Promotions summary | **Different timestamp from Ads summary** | — |
| Average category share | — | **UTC** |
| Performance by daypart | — | **Local** |

✅ Ads summary and Promotions summary do **not** update in lockstep. On 2026-07-27 they were stamped ~21 hours apart. Never sum them for a period without checking both timestamps.

✅ Category share is UTC while daypart is local time, on the same page. Do not cross-reference them for the same window without adjusting.

## 4. Known defects (as of 2026-07-27)

✅ **The portal degrades badly on large multi-location accounts.** On a 20-store business the Campaigns tab timed out on every attempt (six attempts, two browser tabs, 45s script timeouts). After a handful of interactions the **Performance tab and the `/portal` root also stopped responding**, so this is not one broken tab — the whole SPA becomes unusable within a session.

**Working practice that follows:**
- Capture what you need **early in the session**, in as few interactions as possible. Screenshot or transcribe on first load.
- Prefer **Reports exports** over live browsing for anything campaign-level.
- Don't retry a wedged page more than twice. Open a fresh tab, or come back later.

✅ **The "Overall customers" toggle inside the long-term-value module hangs the page.** Reproduced twice. Use the "Customers from ads" view on that module and note the gap.

## 5. Budget mechanics ✅

Verified on goop via campaign detail pages, treat as the DoorDash pattern until a counter-example appears:

- **Offer campaigns:** "No cap on average weekly budget"
- **Sponsored Listings:** "Avg weekly budget $0" with **Bid strategy = Automatic**

Consequences:
- **Budget utilisation / pacing % is not computable on DoorDash.** There is no ceiling to pace against. Never put a DD budget-pacing figure in a report.
- "Limited by budget" never applies. Spend is demand- and bid-driven.
- **The lever to increase spend on a winner is the cost-per-order ceiling**, not a budget increase.

✅ DoorDash still does not expose Impressions / Clicks / CTR for Sponsored Listings. Mark `n/a`; it is not missing data.

## 6. The metrics this unlocks

All of these are now computable from portal-published numbers on any DD client. Carry them in every report.

| Metric | Formula | Confidence |
|---|---|---|
| **Blended ROAS** | (ads sales + promo sales) ÷ (ads spend + promo spend) | ✅ |
| **CAC (low)** | ads spend ÷ ad-attributed new customers | ✅ |
| **CAC (high)** | total marketing spend ÷ ad-attributed new customers | ✅ |
| **LTV90 (new)** | portal-published | ✅ measured |
| **LTV90 (lapsed)** | portal-published | ✅ measured |
| **LTV:CAC** | LTV90 ÷ CAC, reported as a range | ✅ |
| **Payback in orders** | CAC ÷ ad-driven new-customer ticket | ✅ |
| **Lapsed pool** | active customers × share in the 45d–1y buckets | ✅ |
| **Recapture rate** | ad-attributed lapsed customers ÷ lapsed pool | ✅ |
| **Ticket gap** | ad-driven new-customer ticket − storefront average ticket | ✅ |

### The order-rate identity ✅

The portal's **average order rate** for a cohort is the 90-day value multiple, by definition:

```
LTV90 = average ticket × average order rate
```

Checked on goop: `$41.49 × 2.17 = $90.03` against a published LTV90 of `$90.22`. Matches to rounding.

This matters because it means the multiple is not a modelling choice. It is arithmetic on published numbers.

## 7. What follows for reporting — and what doesn't

### Established ✅

**Report blended ROAS as the headline.** The two summary cards each describe half the spend and each overstates the whole. A client can open the same portal and compute blended themselves.

**In-window ROAS understates New-audience campaigns by the measured order-rate multiple.** New customers reorder inside the 90-day window; the portal publishes how often. A New-audience campaign's 90-day value is its in-window ROAS times the cohort order rate. This is arithmetic, not an assumption. **Never cut a New-audience campaign on in-window ROAS alone without applying the multiple.**

**Lead client conversations with LTV:CAC and payback.** ROAS stays as a channel-efficiency metric.

**Never use the portal's store count as a coverage denominator.** It includes storefronts the client has shut down (virtual brands, closed locations). Count against the client's own canonical location list. Getting this wrong overstates a coverage gap, which is a bad way to open a client conversation.

### NOT established ❓

**Existing-customer campaigns are probably overstated by in-window ROAS — but this is unproven.** The reasoning is that they reach customers who were already ordering, so a share of attributed sales is not incremental. Two things block it from being fact:

1. The LTV module has no Existing cohort, so there is no measured multiple for them.
2. No incrementality test has been run on any Spice client to size the non-incremental share.

Until a holdout runs, treat this as a hypothesis. **Do not tell a client their existing-customer spend is waste.** The defensible version of the ask is "let's run a two-week pullback at one location to size the incremental share," which is Meta-Rule 7 and §4 of the main playbook, applied.

**The playbook's "retention delivers 14x better ROAS than acquisition" is unverified.** It may be partly the same measurement artifact. The same holdout settles both.

## 8. First-pull checklist for a new DD client

Do this in one session, early, before the portal degrades:

1. **Reports** → Campaign performance, `Day, Store`, trailing 90d. Name it `{client}-dd-daystore-{start}-{end}`. Check the existing report list first — reports accumulate and nobody names them.
2. **Customer insights** → screenshot all three modules. Toggle ads vs overall on the breakdown. Capture New and Lapsed tabs on the LTV module.
3. **Performance** → Ads and Promotions summaries (note both timestamps), the Organic/Ads/Promo split, daypart, category share.
4. **Coverage** → count locations with an active campaign against the client's canonical location list, not the portal's store count.
5. Compute the §6 metric set. Add the row to the cross-client benchmark table.

## 9. Open questions

Log answers here as they land. An answer that changes a recommendation should be promoted into §7 Established.

| # | Question | How it gets answered |
|---|---|---|
| 1 | What share of existing-customer campaign sales is incremental? | 20% spend pullback, one location, 14 days, matched control |
| 2 | Does the "retention 14x" rule survive an incrementality test? | Same test |
| 3 | Is a ~31% 45-day-active rate normal, or is goop an outlier? | Cross-client benchmark table (`dd-customer-benchmark-template.csv`) |
| 4 | Do ad-driven customers systematically order smaller baskets, or was that one client? | Cross-client benchmark, ticket-gap column |
| 5 | Did DoorDash migrate or deprecate multi-store campaigns during the July rebuild? | Account rep |
| 6 | Does the marketing-credit "boosted sales by 1.00x" line ever show a real multiple? | Watch across clients; ask rep about credit consumption |
