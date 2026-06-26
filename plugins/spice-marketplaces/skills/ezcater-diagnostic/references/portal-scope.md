# ezCater Partner Portal — Scope Map (from live exploration, Jun 26 2026)

Explored Tiff's Treats' live account (`success+tiffstreats@spicedigital.co`,
`partnerportal.ezcater.com`). This documents what the portal actually exposes and what's
controllable — the ground truth for scoping the managed service. **Several findings correct
assumptions in the v0.1 diagnostic** (flagged ⚠️ below).

## Two portals, not one

| Surface | URL | What it holds |
|---|---|---|
| **Partner Portal** | `partnerportal.ezcater.com` | Analytics, ops metrics, reliability/badge, sales performance, reviews, menus, financials |
| **ezManage** (separate) | `catering.ezcater.io` / `ezmanage` | The **paid levers** — Preferred Partner bids, ezRewards, Promotions. The portal's "Marketing / Engage customers" nav is inert; these are managed on ezManage. |

⚠️ **Service-access implication:** managing ezCater needs logins to **both** surfaces, not just
the partner portal. The export SOP and onboarding access checklist must cover ezManage too.

## Partner Portal sections (all per-store, 175 stores for Tiff's)

- **`/operational-metrics`** — per-store ops table + per-store detail with pause status & recommendations
- **`/reliability_rockstar`** — badge funnel with exact goals (below)
- **`/performance` (`/performance-metrics`)** — sales funnel, conversion, customer mix, CSV export
- **`/reviews`** — customer reviews (monitor only — ⚠️ no reply control seen; unlike DD/UE)
- **`/menus`** — per-store menu editing (items, photos, packaging, pricing) ✅ controllable
- **`/payments`** — financials / payout history
- **`/orders`** — order management

## ⚠️ Correction 1 — TWO threshold systems (the store-detail page proves it)

The per-store operational detail shows metrics split into two groups:

**Accountability standards** (breaching these → store **PAUSED**, can't accept any orders):
| Metric | Pause standard |
|---|---|
| Rejected orders | ≤ 5% |
| Canceled orders | ≤ 3% |
| On-time delivery | ≥ 95% |
| Ready for Dispatch | ≥ 95% |

**Quality goals** (don't gate marketplace access, but matter for badge/visibility):
| Metric | Goal |
|---|---|
| Order accuracy | ≥ 99% |
| Star rating | ≥ 4.8 |
| Delivery tracking | ≥ 75% (badge) / 100% (quality view) |
| On-time acceptance | 100% |

The v0.1 diagnostic collapsed these into one band set (rejection 0.5/2, etc.). It must
distinguish **pause-risk** (loose, revenue-gating) from **badge-miss** (strict, visibility).

## ⚠️ Correction 2 — PAUSE status is a first-class, P0 lever

A store can be **Paused** (zero marketplace orders) or **At Risk**. Tiff's: **21 stores
paused or at risk**. Example: **H4 Westchase** is paused *purely* for 11.1% cancellations
despite 0% rejection, 100% on-time, 100% accuracy, 5★. To unpause, the partner must complete
ezCater's **"Cancellations course."** This is the single most urgent finding type — a paused
store earns nothing — and the v0.1 diagnostic doesn't model it. Need a `status` column +
`store_paused` P0 finding with the remediation-course action.

## ⚠️ Correction 3 — Badge requires Delivery Tracking ≥75% (the real Tiff's blocker)

Confirmed badge goals (resolves the audit's "criteria unconfirmed" P0):
order volume ≥6 · rejected ≤0.5% · canceled 0% · accuracy ≥99% · on-time ≥98.5% ·
**delivery tracking ≥75%**.

Tiff's **self-delivers → 0% delivery tracking → fails the badge** even when every other metric
passes. That's why the 16 "metrics-pass" stores aren't badged — it's **not an enrollment gap**.
The fix is operational: provide delivery status updates (driver app / ezDispatch). The
diagnostic's badge logic must add the delivery-tracking gate, and `badge_gap` should name
delivery-tracking as the blocker for self-delivery clients.

## ⚠️ Correction 4 — Catering DOES have a conversion funnel

The Sales Performance page exposes a real funnel + benchmark (so "no menu funnel" was wrong):
- **Search Views** (35,674) → **Menu Views** (2,471) → **Orders** (238) → **Sales** ($46,544)
- **Conversion rate** 9.6%, **benchmarked vs local peers** (~10%)
- **Organic vs Sponsored Listings** split
- **Customer mix:** New / Existing / Lapsed (163 / 36 / 27) → re-order/loyalty signal IS available
- ezCater's own named levers: optimize menu, **update menu photos**, add a promotion, **raise ezRewards rate**

Implication: the diagnostic can add **Search→Menu CTR** (traffic), **Menu→Order conversion**
(vs peer benchmark), and a **customer-mix / re-order** dimension — richer than packaging alone.

## Controllable vs read-only (service scope)

| Lever | Where | Controllable? |
|---|---|---|
| Menu items, photos, packaging, pricing | Portal `/menus` | ✅ yes |
| Sponsored Listings campaign | Portal `/performance` → Create campaign | ✅ yes |
| Preferred Partner bid % | ezManage | ✅ yes (separate login) |
| ezRewards rate | ezManage | ✅ yes (separate login) |
| Promotions / promo codes | ezManage | ✅ yes (separate login) |
| Pause recovery (course completion) | Portal (per store) | ✅ partner action |
| Reviews | Portal `/reviews` | 👀 monitor only (no reply seen) |
| Ops metrics, sales, financials | Portal | 👀 read (drive the diagnostic) |

## Net: what the managed service actually is

1. **Reliability/pause management** — keep stores off the pause/at-risk list (cancellations,
   rejections, on-time, ready-for-dispatch), run pause-recovery courses. *Revenue-critical.*
2. **Badge pursuit** — close the gap to the 6 badge goals; for self-delivery clients the lever
   is delivery tracking.
3. **Visibility/paid levers** (ezManage) — Preferred Partner bids, ezRewards, Sponsored
   Listings, Promotions.
4. **Menu/conversion** — photos, packaging, pricing to lift the Menu-View→Order rate vs peers.
5. **Reporting** — sales funnel, customer mix, monthly recap.
