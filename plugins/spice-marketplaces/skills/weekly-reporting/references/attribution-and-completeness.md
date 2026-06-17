# Attribution & completeness — methodology (ALL clients)

## 1. Marketing-Driven Sales = per-order, NEVER campaign exports
Marketing-Driven Sales — and everything derived from it (tier/location MDS, Marketing ROAS, Mkt-Driven %, the **Campaign Performance Dashboard** for every client) — is computed from the **canonical per-order attribution** (metric #8): for each Completed order, flag **offer-driven** (transaction-CSV discount columns < 0) OR **ad-driven** (Tier-2 cross-ref), sum net sales, and **dedupe** (one order counted once even if both applied).

**Do NOT build the dashboard's tier/location MDS from platform campaign exports** (UE/DD Ads Manager). They (a) use platform attribution windows that don't match per-order, (b) double-count across overlapping campaigns, and (c) are frequently incomplete — a missing offer/promo export silently drops whole stores.

**Reconciliation rule (enforce):** sum of tier (and location) Marketing-Driven Sales **must equal** the headline per-order MDS (±$2). If it doesn't, the breakdown is built off the wrong (campaign-export) source — fix it.
> goop W24 evidence: tier sum **$291,959** vs headline **$430,869** = **$139K gap**, 🦄 Unicorn tier **$0** — caused by missing offer exports for 9 of 15 stores.

## 2. New-Customer CAC
- **Denominator** — new customers from the complete offer/transaction source, NOT the gappy campaign exports.
- **Numerator** — **acquisition spend only** (first-order + new-customer-targeted offers/ads), NOT total marketing spend. Dividing total spend (which includes loyalty/lapsed/existing) by new customers overstates CAC by charging retention against acquisition. If total spend is kept for simplicity, label it **"blended cost / new customer,"** not CAC.
> goop W24: $95,130 ÷ 884 new = $108, vs ~$55 the prior week — the 884 was halved by the missing offer data, and the numerator is over-broad.

## 3. Completeness gate — run BEFORE any publish / in-place write
Incomplete extractions must never silently publish. Extends `validate_report.py` (which already gates formula integrity); the new piece validates against an **expected manifest**, not just the data that happened to extract.
1. **Coverage** — every expected location × platform (from client registry / store map) present with data. Expected-but-$0 / no-rows → CRITICAL (halt), unless registry marks it inactive.
2. **Offer-export completeness** — a store with offer-driven sales last week but $0 offer attribution this week → flag "offer export likely incomplete" (DD Promotion / UE Offers export missing or partial).
3. **WoW guardrails** — any of {Total Orders, New Customers, Marketing-Driven Sales, Mkt-Driven %} moving beyond ±25% (±10pts for a %) WoW → hard flag requiring reviewer sign-off before publish.
4. **Reconciliation** — tier/location MDS sum == headline MDS (±$2); location sales sum == platform totals == overall. **Per-store Marketing-Driven Sales must be ≤ that store's Total Sales** — a value >100% means the attribution is double-counting (see UE full-overlap dedup in `column-mappings.md`).
5b. **Trend method-consistency** — never splice weeks computed with different attribution methods into one trend line. If the current week uses a corrected method vs prior weeks, either recompute the prior weeks the same way or **remove the trend** — don't show a line that spikes on a methodology change.
5. **Output gating** — any CRITICAL failure → mark output **"DRAFT — INCOMPLETE, do not publish,"** block the in-place write, fall back to flagged paste.

This is what would have caught W24: coverage (9 stores missing offers, SoMa missing entirely), WoW (new customers −46%, Mkt-Driven % −15pts), and reconciliation (the $139K tier gap).

## 4. Dashboards: formula-driven, never hand-typed (the structural anti-fake-data guard)
The Campaign Performance Dashboard must compute from a **settled-inputs block** (per-location atomics the weekly run writes — Total Sales, Mkt-Driven, Ad Spend, Offer Cost, Orders) via **in-sheet formulas** (SUM/SUMIF). Never hand-type aggregates. Specifically:
- **WoW deltas** compute from the prior week's stored values — never placeholder them. If a prior value is missing (new store), show `new`, not a guessed number.
- **Trend** series must be method-consistent — if the current week uses a different attribution method than prior weeks, label it, don't silently splice.
- Tier/location/platform breakdowns are SUMIF rollups off the inputs block, so they **reconcile to the headline by construction**.
This is what makes "no fabricated values" enforceable rather than a manual check.
