---
name: store-ops-leaderboard
description: >
  Monthly store ops leaderboard for any multi-unit delivery marketplace client.
  Loads platform exports (UE order history + ratings, DD financial transactions + operations
  quality, GH operations review), computes per-store ratings velocity, fulfillment, average
  delivery time, applies absolute-threshold Status (Healthy/Watch/Broken/Inactive), and emits
  a ranked leaderboard with Inactive stores in a separate section. Triggers on "update
  leaderboard", "leaderboard for [client]", "monthly leaderboard", "store ops leaderboard",
  "refresh leaderboard", or when the user provides platform exports for a client and mentions
  the leaderboard.
version: 1.0.0
supersedes: leaderboard-update (Everytable-only, deprecated 2026-05-19)
---

# Store Ops Leaderboard — Monthly Update

Update a client's monthly store ops leaderboard from platform exports. Status (absolute thresholds) drives action. Rank is for ordering only. Inactive stores pulled out of the ranked list. Calibration of velocity + delivery-time thresholds happens during pilot before generalizing to a new client.

---

## Prerequisites

**Per-client config:** `clients/<slug>.json` (mirror of the `client-diagnostics` skill pattern). Holds:
- `client_slug`, `client_display_name`
- `workbook_path` or `gsheet_id` (Sheet or xlsx location, per-client)
- `target_velocity_per_week` (default 10; calibrate per portfolio)
- `active_platforms` (UE / DD / GH)
- `closed_stores` (explicit roster of confirmed closures; skips Inactive auto-detection for these stores so they're always categorized correctly)

**Workbook structure** (consistent across clients):
- Tabs: Instructions, Leaderboard, Previous Month, Data Input, Stores
- The Leaderboard tab is 100% formula-driven. Touch only Data Input, Previous Month, and the period label.

Drop new client workbooks from a template. Pre-pilot phase, copy from the closest existing pilot Sheet (goop Kitchen or Fresh Kitchen) and adapt the Stores tab + branding.

**Reference implementation:** `references/update_leaderboard_everytable_reference.py` is the legacy Everytable-only Python script. Use as adaptation reference when generalizing per-client. Hardcoded paths and exclusions need to be replaced with config-driven values.

---

## Phase 1: Collect Required Files

Ask the user for the reporting period (week or date range), then collect these exports:

### Uber Eats (2 required)
- [ ] **Order History CSV** — from UE Manager > Orders > Export. Contains order-level rows with store ID, order date, order status (delivered/canceled/failed/unfulfilled).
  - Spanish headers: `Fecha del pedido`, `ID de tienda externa`, `Tienda`, `Estado del pedido`
- [ ] **Restaurant Ratings CSV** — from UE Manager > Ratings > Export. Contains per-order ratings.
  - Spanish headers: `Fecha del pedido`, `ID de tienda externa`, `Valor de la valoracion`
  - Count rows where `Valor de la valoracion` = "5" as positive ratings.

### DoorDash (3 required)
- [ ] **Financial Transactions CSV** — from DD Merchant Portal > Financials > Export. One row per order.
  - Spanish headers: `Tipo de transaccion` (filter to "Order"), `Hora local del sello de tiempo`, `Nombre de la tienda`
  - This is the source for DD total order counts.
- [ ] **Cancelled Orders CSV** — from DD Merchant Portal > Operations Quality > Cancelled Orders > Export.
  - English headers: `Order Placed Date`, `Store Name`
- [ ] **Missing/Incorrect Orders CSV** — from DD Merchant Portal > Operations Quality > Missing/Incorrect > Export.
  - English headers: `Order Delivered Date`, `Store Name`, `DD Order ID`
  - Deduplicate by DD Order ID (multiple items per order create multiple rows).

### DoorDash Ratings (optional but recommended)
- [ ] **Customer Reviews CSV** — from DD Merchant Portal > Customer Reviews > Export.
  - Contains "Loved" counts. Without this, DD ratings = 0 in the leaderboard.

### Grubhub (1 required)
- [ ] **Operations Review CSV** — from GH for Business > Analytics > Operations Review > Export.
  - Headers: `store_number`, `total_orders`, `total_canceled_orders`, `adjusted_orders`, `ratings_5_stars`
  - This is aggregate data (not order-level). Covers the full export date range.

---

## Phase 2: Validate & Parse

1. Identify the reporting period from the user (e.g., "Week of Apr 14-20" or "Q1 2026 Jan-Mar").
2. Define date filters: `PERIOD_START` and `PERIOD_END`.
3. For each uploaded file, confirm it exists and read headers to validate format.
4. Build the store ID map from UE data: extract `ID de tienda externa` (e.g., CA001) and clean store name by stripping "Everytable (" prefix and trailing ")".

### Exclusions
- **CA062** (Anaheim) — confirmed closed. Always exclude.
- **CA048** (Whittier) — exclude if < 5 orders in the period.
- Check with user if any new stores should be excluded.

---

## Phase 3: Process Data

Run the update script. The script does:

1. **Rotate**: Copy current Data Input rows into Previous Week (overwrite).
2. **Clear**: Wipe Data Input rows (keep header).
3. **Load**: For each store, write one row per platform with data:
   - Column A: Store Name (clean, no "Everytable" prefix)
   - Column B: Platform ("Uber Eats", "DoorDash", or "Grubhub")
   - Column C: Total Orders (in period)
   - Column D: Positive Ratings (5-star for UE/GH, "Loved" for DD)
   - Column E: Cancellations
   - Column F: Errors (missing/incorrect orders)
4. **Update period label**: Set Leaderboard B3 to the period string.
5. **Save**.

### Key Processing Rules

**Uber Eats:**
- Count ALL orders (including canceled) in total orders.
- `canceled` status = cancellation. `failed` or `unfulfilled` = error.
- Positive ratings = rows in ratings CSV where `Valor de la valoracion` = "5".

**DoorDash:**
- Total orders from Financial Transactions where `Tipo de transaccion` = "Order".
- Extract store ID from store name: split on " - ", take first token (e.g., "CA001").
- Deduplicate error orders by `DD Order ID`.
- "Loved" ratings from Customer Reviews export (if provided).

**Grubhub:**
- Already aggregate. Use values directly: `total_orders`, `total_canceled_orders`, `adjusted_orders` (errors), `ratings_5_stars`.
- Add GH-only stores to the store map using `city` as fallback name.

---

## Phase 4: Recalc & Verify

1. Run LibreOffice recalc: `python mnt/.claude/skills/xlsx/scripts/recalc.py <path> 60`
2. Verify: 0 formula errors, ~500 formulas, 35 stores with data.
3. Spot-check top 3 and bottom 3 stores for reasonable scores.
4. Confirm WoW arrows show movement (not all "▲" unless it's the first week).
5. Report Status distribution (the only distribution that matters; rank-thirds Tier is deprecated):
   - 🟢 Healthy / 🟡 Watch / 🔴 Broken / 🚫 Inactive counts
   - Call out any 🚫 Inactive stores explicitly with their volume drop signal

---

## CRITICAL: Design rules (codified 2026-05-19)

### Rule 1: Status is the only health signal. Rank is for ordering only.

**Rank** (1 to N) shows leaderboard position by composite score. Information only.

**Status** (🟢 Healthy / 🟡 Watch / 🔴 Broken / 🚫 Inactive) is the actionable health signal, derived from absolute thresholds.

The rank-thirds Tier column (Top33 / Mid34 / Bot33 emoji) is **REMOVED** from the leaderboard. It produced false-alarm reds for healthy stores in high-performing portfolios (Fresh Kitchen pilot showed 3 "🔴 Triage" stores at 99% fulfillment, all actually Healthy). Stores can be Rank N/N AND Status 🟢 Healthy. Don't show conflicting signals.

### Rule 2: Inactive stores are pulled OUT of the ranked list

Detect closure or pause before scoring:
- Current period orders < 20% of prior period AND current orders < 500 → 🚫 Inactive
- OR current period orders below absolute floor (< 300 / month) → 🚫 Inactive

Inactive stores get a separate section below the ranked leaderboard. They don't occupy rank slots. Action: GM confirms with client whether closed, paused, or genuine collapse needing investigation.

Example: goop Kitchen Beverly Hills in April had 224 orders vs 7,677 in March (2.9% of prior). Was incorrectly ranked #2 with Watch status. Should have been pulled to Inactive section, no rank, action "confirm store status."

### Rule 3: Ratings input is VELOCITY, not rate

**Old (deprecated):** Pos Rtg % = positive ratings / total ratings received. A store with 1 positive of 1 received looked perfect (100%) despite tiny sample.

**New:** Velocity = total positive ratings / weeks in period.

```
Positive Velocity = (UE 5★ + DD Loved + GH 4★/5★) / weeks_in_period
```

Velocity rewards active ratings acquisition (the ratings flyer program). Penalizes stores that aren't gathering reviews. Volume-adjusted measure of customer satisfaction.

Velocity status thresholds (calibrate against your portfolio; these are starting values):

| Status | Positive Ratings / Week |
|---|---|
| 🟢 Healthy | ≥ 5 |
| 🟡 Watch | 2 to 5 |
| 🔴 Broken | < 2 |

### Rule 4: UE ratings must be included

UE 5★ ratings live in **UE Manager → Ratings & Reviews → 90d export OR screenshot**. They are NOT in the standard Order History export. The runbook (`ops-data-collection-process.md`) now asks for this. The Data Input section MUST include a `UE 5★` column per store. The score formula adds it to the numerator alongside DD Loved and GH stars.

DD+GH only was a stale workaround from before the UE Ratings export was reliably available. Triple-platform now.

### Rule 5: Average delivery time tracked, threshold TBD

Add `Avg Delivery (min)` column to Leaderboard. Data Input pulls per-platform avg delivery time:
- UE: Performance → Operations → Time to door
- DD: Operations Quality → Avg delivery time
- GH: Operations Review export → avg_delivery_time column

Status thresholds (DRAFT, calibrate during multi-client pilot):

| Status | Avg Delivery |
|---|---|
| 🟢 Healthy | ≤ 35 min |
| 🟡 Watch | 35 to 45 min |
| 🔴 Broken | > 45 min |

For first month: include the data, don't include in status calculation. Observe distribution across pilot clients. Lock thresholds before slot 3 productization.

### Composite score formula (standardized, replaces both Fresh Kitchen + goop versions)

```
Composite Score = (Fulfillment Wt × Fulfillment %) 
                + (Velocity Wt × normalized_velocity)

where:
  Fulfillment % = (Orders − Cancellations − Errors) / Orders [all platforms combined]
  Velocity = (UE 5★ + DD Loved + GH 4★/5★) / weeks_in_period
  normalized_velocity = MIN(Velocity / TARGET_VELOCITY, 1.0) × 100
  TARGET_VELOCITY = 10 (positives/week — calibrate per portfolio)
  Default weights: 50% Fulfillment, 50% Velocity
```

### Full Status calculation (all rules combined)

```
=IFS(
  OR(Orders_current/Orders_prior < 0.20, Orders_current < 300), "🚫 Inactive",
  OR(Fulfillment_pct < 0.90, Cancellation_pct > 0.05, Error_pct > 0.05, Velocity < 2), "🔴 Broken",
  OR(Fulfillment_pct < 0.97, Cancellation_pct > 0.02, Error_pct > 0.02, Velocity < 5), "🟡 Watch",
  TRUE, "🟢 Healthy"
)
```

Status = worst flag across all tracked metrics. Inactive supersedes everything (don't rank, don't score, separate section).

### Status thresholds reference

| Metric | 🟢 Healthy | 🟡 Watch | 🔴 Broken |
|---|---|---|---|
| Fulfillment % | ≥ 97% | 90-97% | < 90% |
| Cancellation % | < 2% | 2-5% | > 5% |
| Error rate % | < 2% | 2-5% | > 5% |
| Rating (where exposed) | ≥ 4.5 | 4.2-4.5 | < 4.2 |
| Positive velocity (per week) | ≥ 5 | 2-5 | < 2 |
| Avg Delivery (min) — TBD | ≤ 35 | 35-45 | > 45 |

Aligned with `client-diagnostics/references/diagnostic-framework.md` lines 79-92.

### Legend at top of Sheet

Replace the old tier-thirds explainer with:

> "Rank shows leaderboard position (sorted by composite score). Status shows absolute health (🟢 Healthy / 🟡 Watch / 🔴 Broken / 🚫 Inactive) using fixed thresholds independent of rank. Use Status, not Rank, to decide whether to scale or fix. Inactive stores are listed below the ranked leaderboard and require client confirmation of operational status."

### Pilot validation before generalizing

Before this skill gets productized for all clients (slot 3 of umbrella plan), Santi runs the updated logic against 4 clients with different shapes:
1. **Fresh Kitchen** (11 stores, FL, stable, single-cuisine)
2. **goop Kitchen** (16 stores, multi-state, has 1 Inactive + 1 NEW launch)
3. **Pret** (~16 stores, urban-dense, tests delivery time variance)
4. **Everytable** (35+ stores, largest portfolio, tests scale)

Goal: status distribution reads sensibly across all 4. Inactive detection catches actual closures, no false positives. Velocity thresholds map to portfolio reality. Delivery time data captured to calibrate thresholds for slot 3.

### Rule 6: Canonical column layout (codified 2026-05-20)

**Every client's leaderboard MUST use this column order.** Skills describe rules; layout must be enforced for cross-client comparability. Pilot showed goop and Everytable Sheets with different shapes because each was built independently. From v1.0 forward, all client Sheets follow this canonical layout:

| # | Column | Source | Notes |
|---|---|---|---|
| 1 | Rank | computed | Sort by Score desc; Inactive stores not ranked |
| 2 | Δ Rank | vs prior period | ▲ N / ▼ N / — |
| 3 | Status | computed (Rule 1) | Drives action; appears early for scannability |
| 4 | Store | from Stores tab | |
| 5 | ID | from Stores tab | Optional, only if client uses store codes (CA001, etc) |
| 6 | Platforms | from config `active_platforms` | UE / DD / GH or subset |
| 7 | Score | computed (Rule 6 formula) | Composite |
| 8 | Δ Score | vs prior period | ▲ X.X / ▼ X.X / — |
| 9 | Fulfillment % | computed | Orders − Cancels − Errors / Orders |
| 10 | Cancel % | computed | Cancels / Orders |
| 11 | Error % | computed | Errors / Orders |
| 12 | Velocity / wk | computed (Rule 3) | (UE 5★ + DD Loved + GH 4+5★) / weeks |
| 13 | Δ Velocity | vs prior period | ▲ X.X / ▼ X.X / — |
| 14 | Avg Del (min) | from ops exports | Capture-only first month |
| 15 | Orders | aggregate this period | All platforms combined |
| 16 | Orders prior | aggregate prior period | For Inactive detection |
| 17 | MoM Δ | this − prior | Raw count |
| 18-N | UE 5★, DD Loved, GH 4+5★ | per-platform positive rating counts | Optional detail, hide by default unless GM expanding view |

Below the ranked table, two separate sections (with headers and visual divider):
- **🚫 INACTIVE — Confirm operational status with client.** Stores caught by Rule 2. Show only: Store, ID, Status, Current Orders, Prior Orders, MoM Δ, action ("confirm closure/pause with GM").
- **🆕 NEW LAUNCH — Pre-steady-state. Score shown for reference only.** Stores marked new (per config `new_stores` roster). Show all standard columns but mark Score as informational.

Delta arrows use ▲ / ▼ glyphs (not raw + / -) for visual scannability.

### Per-client calibration (slot 3 lesson, captured 2026-05-20)

**Target velocity is NOT universal. Each client's `target_velocity_per_week` in `clients/<slug>.json` must be calibrated against portfolio volume.**

Evidence from pilot:
- goop Kitchen (~5,000-13,000 orders/store/month): velocity 30-80+/wk per store. Target of 10/wk easy to clear; 30/wk would be more meaningful threshold.
- Everytable (~100-300 orders/store/month): velocity 0.2-4.2/wk per store. Target of 10/wk impossible to clear. Realistic target ~3-5/wk.

Calibration heuristic: set `target_velocity_per_week` at the 60th percentile of the client's current portfolio distribution, so ~40% of stores need to lift to hit Healthy. Re-calibrate annually or when portfolio composition changes materially.

Status threshold bands shift proportionally:
- 🟢 Healthy: ≥ target
- 🟡 Watch: 20-100% of target
- 🔴 Broken: < 20% of target

OR (simpler, recommended): keep absolute bands (5 / 2-5 / <2) and accept that low-volume portfolios will skew Watch/Broken until volume grows. Maxx's call on which is right.

### Rule 7: Optional per-client extension columns (codified 2026-05-20)

**Default behavior:** every client gets exactly the canonical column layout from Rule 6. Nothing more, nothing less. Cross-client comparability stays intact.

**Override:** if a client requests additional data points (specific KPIs they want to see in their leaderboard), append them after the canonical columns via the per-client config. Don't insert into the middle; don't remove canonical columns.

Per-client config pattern (`clients/<slug>.json`):

```json
{
  "client_slug": "everytable",
  "client_display_name": "Everytable",
  "target_velocity_per_week": 4,
  "active_platforms": ["UE", "DD", "GH"],
  "closed_stores": ["CA062"],
  "new_stores": [],
  "additional_columns": [
    {
      "name": "Market Segment",
      "source": "stores_tab.market_segment",
      "position": "after_canonical",
      "format": "text"
    },
    {
      "name": "Opening Date",
      "source": "stores_tab.opened_at",
      "position": "after_canonical",
      "format": "date"
    },
    {
      "name": "Avg Ticket",
      "source": "computed: gross_sales / orders",
      "position": "after_canonical",
      "format": "currency"
    }
  ]
}
```

**Rules for additional_columns:**
1. Position is always `after_canonical` (after column N from Rule 6). No insertion in the middle.
2. Format is one of: `text`, `number`, `currency`, `pct`, `date`, `status_emoji`.
3. Source is either a static lookup (from Stores tab) or a computed expression on the existing data.
4. Additional columns are INFORMATIONAL ONLY. They don't feed Status calculation, don't affect Score, don't change ranking. The action signal stays from the canonical metrics.
5. Document the addition in the client's Notion portal so the team knows why this client has the extra column. Avoid silent customization that drifts over time.

**When to push back on a client request:**
- They want to remove a canonical column. Don't. The whole point of v1.0 is shared schema.
- They want to change a Status threshold to make their stores look better. Don't. Status is honest, not flattering.
- They want a column that's actually a separate report (e.g., full campaign analytics). Don't bloat the leaderboard. Suggest a sibling Sheet or section.

**When to say yes:**
- Genuinely useful operational context that helps the GM at-a-glance (Market Segment, Store Age, Franchise/Corporate flag)
- A client-specific KPI they track for their own reporting that should match the leaderboard period
- A flag that the GM uses for prioritization (Priority Tier, Geo Cluster)

If a client requests something niche, default to "yes if it's just a column, no if it would change scoring or status." Per-client config keeps the customization explicit and auditable.

---

## Phase 5: Report

Present a summary to the user:

```
Leaderboard Updated: [Period]
Stores: [count] | Data Rows: [count] (UE + DD + GH)
Formulas: [count] | Errors: [count]

Top 5 by rank:
1. [Store] — Score [X], Fulfillment [Y%], Velocity [Z/wk], Avg Delivery [M min], Status: [Healthy|Watch|Broken]
...

Bottom 3 by rank:
N-2. [Store] — Score [X], Fulfillment [Y%], Velocity [Z/wk], Status: [Healthy|Watch|Broken]
N-1. [Store] — ...
N.   [Store] — ...

🚫 INACTIVE (pulled from ranked list):
- [Store] — Apr orders [X] vs Mar [Y] ([Z%] of prior). Action: confirm closure / pause with client.

Status Distribution: 🟢 Healthy [n] | 🟡 Watch [n] | 🔴 Broken [n] | 🚫 Inactive [n]

Velocity benchmark: target [TARGET_VELOCITY]/wk per store. Portfolio avg: [X/wk].
Avg Delivery range across portfolio: [min] to [max] min. (Status threshold TBD — first month captures data for calibration.)

Data Gaps:
- [any missing exports or known issues]
```

---

## Reference: Update Script Template

Below is the Python script pattern for the weekly update. Adapt paths to match uploaded files.

```python
"""
Weekly Everytable Store Leaderboard Update
Usage: Adapt file paths, date range, then run.
"""
import csv
from datetime import datetime
from collections import defaultdict
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Border, Side

PERIOD_START = datetime(2026, 4, 14)  # ← UPDATE EACH WEEK
PERIOD_END = datetime(2026, 4, 20)    # ← UPDATE EACH WEEK
PERIOD_LABEL = "Week of Apr 14-20, 2026"  # ← UPDATE EACH WEEK

# ← UPDATE FILE PATHS EACH WEEK
UE_ORDERS = "path/to/ue_order_history.csv"
UE_RATINGS = "path/to/ue_ratings.csv"
DD_FIN = "path/to/dd_financial_transactions.csv"
DD_CANCELS = "path/to/dd_cancelled_orders.csv"
DD_ERRORS = "path/to/dd_missing_incorrect.csv"
DD_REVIEWS = None  # path/to/dd_customer_reviews.csv if available
GH_OPS = "path/to/gh_operations_review.csv"

WORKBOOK = "mnt/Everytable/Everytable_Store_Leaderboard.xlsx"
EXCLUDE = {'CA062'}  # Anaheim closed

LIGHT_GRAY = "F5F5F5"
dat_font = Font(name="Arial", size=10)
thin_b = Border(
    left=Side(style='thin', color='CCCCCC'), right=Side(style='thin', color='CCCCCC'),
    top=Side(style='thin', color='CCCCCC'), bottom=Side(style='thin', color='CCCCCC'))

def parse_date(d):
    return datetime.strptime(d.strip().split(' ')[0], '%Y-%m-%d')

def in_period(d):
    return PERIOD_START <= d <= PERIOD_END

def dd_store_id(name):
    return name.split(' - ')[0].strip() if ' - ' in name else name.split(' ')[0]

# [... same processing logic as load_all_platforms.py ...]
# 1. Build store ID map from UE
# 2. Process UE orders + ratings
# 3. Process DD financial + cancels + errors (+ reviews if available)
# 4. Process GH operations review
# 5. Rotate Data Input → Previous Week
# 6. Clear Data Input, load new data
# 7. Update period label
# 8. Save
```

---

## Notes

- The Leaderboard tab formulas are self-updating. Never edit Leaderboard cells directly.
- Store names must match EXACTLY between Stores tab, Data Input, and Previous Week.
- If a store is added or removed, update the Stores tab too.
- The composite score weights (Rating 50%, Fulfillment 50%) are in cells E3 and H3 on the Leaderboard tab. Adjustable without code changes.
- DD "Loved" ratings are the biggest data gap. Push to get the Customer Reviews export from Merchant Portal.
