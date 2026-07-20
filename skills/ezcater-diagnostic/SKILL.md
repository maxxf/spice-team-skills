---
name: ezcater-diagnostic
description: >
  Runs a 90-day catering diagnostic for an ezCater client and produces a tiered
  action plan. Use when the user says "ezCater diagnostic for [client]",
  "diagnose [client]'s catering", "run a catering audit", "ezCater action plan
  for [client]", "how is [client] doing on ezCater", or asks to assess a
  restaurant's catering-marketplace health. Catering analog of client-diagnostics:
  collects the four ezCater browser exports, builds one unified CSV, runs the
  deterministic scorer, and returns a tiered action plan + (optionally) a Notion page.
version: 0.2.0
---

# ezCater Catering Diagnostic

Catering analog of the delivery `client-diagnostics` skill. Same shape — one
sentence in, four exports dropped in a folder, one action plan out — but built
for ezCater's catering marketplace: **3 sub-buckets (Ops · Visibility · Packaging)**,
a **monthly** cadence, a single platform, and the **Reliability Rockstar badge** funnel.

Read `references/ezcater-diagnostic-framework.md` for the full methodology before
interpreting output. This is the **marketing/visibility layer** service (no corporate-
account sales motion in v1).

## Triggers

- "ezCater diagnostic for [client]" / "diagnose [client]'s catering"
- "run a catering audit for [client]"
- "ezCater action plan for [client]"
- "how is [client] doing on ezCater"
- User drops ezCater partner-portal exports and asks for analysis

## Data access (no API — browser automation, TWO surfaces)

ezCater has no partner API. Data is pulled by browsing the client's account. **There are two
surfaces** (confirmed by live exploration, see `references/portal-scope.md`):
- **`partnerportal.ezcater.com`** — ops metrics, reliability/badge, sales performance, reviews,
  menus, financials (the diagnostic's read inputs).
- **ezManage (`catering.ezcater.io`)** — the paid levers: Preferred Partner bids, ezRewards,
  Promotions. The portal's "Marketing" nav is inert; these live here.

Managing a client needs logins to **both**. The four exports and where to get them are in
**`references/ezcater-export-sop.md`**; the full scope map is in `references/portal-scope.md`.

## The flow

### Step 1 — Resolve the client
Check `clients/` for `<slug>.json` (e.g. "Tiff's Treats" → `clients/tiffs-treats.json`).
If missing, copy `clients/_template.json`, fill `client_slug` + `client_display_name`.

### Step 2 — Collect the four exports
Post the data-collection checklist from `references/ezcater-export-sop.md`. The four:
1. **Operational Metrics** (`/operational-metrics`) — per-store on-time, rejection, accuracy, cancellation
2. **Performance / Reliability** — badge / At-Risk / Paused flags
3. **Finance / payout** — sales + payout history
4. **30-day sales** — per-store orders, sales, AOV, sponsored contribution

Wait for the user's "done" signal. Validate at least the operational + sales exports are present.

### Step 2b — Storefront visual + buyer-side audit (v1, qualitative)
Audit the storefront the way a buyer sees it — the same lens the delivery `client-diagnostics`
skill applies to UE/DD/GH storefronts. Catering buyers compare listings side by side in search,
so the visual layer still moves conversion even without an impulse-browse funnel. Qualitative
pass in v1 (no scored schema columns yet); borrow the scoring lens from the `hero-image-review`
skill, don't invent a new rubric.

**Where to look:** the public buyer view on `ezcater.com`, NOT the portal menu editor (that's
the editing backend, and it can hang). The storefront is address-gated — set an event location
in the store's market, search the brand, open the listing. The search results page is itself
data: it shows ranking, badges, and points multipliers you need for the paid read below.

**Sampling:** most brands run one shared menu across locations. Audit the **highest-volume
store's** full storefront, then spot-check the **hero per store** (heroes can vary by location).
Menu, category, and packaging findings generalize from the sampled store.

Capture:
- **Hero image** — present, on-brand, high-resolution, not a stale/pre-rebrand asset or an ezCater default
- **Menu photo coverage** — rough % of items with real photos (flag under ~80%)
- **Category structure** — logical order, best-sellers and headcount bundles surfaced up top
- **Packaging presentation** — per-person pricing, headcount tiers, Feeds-10/25/50 bundles visibly displayed
- **Buyer-side paid signals** — covers the paid read when the ezManage login is still pending: a points multiplier = ezRewards active; a "Sponsored" tag = Sponsored Listings running; a visible offer = a live promo; ranking above higher-rated peers = a Preferred Partner bid. Record as inferences to confirm in ezManage.

Record findings as a short "Storefront visuals" section in the return (Step 5), and fold the
paid signals into the paid-levers read. Where assets are missing, off-brand, or stale, **route
a design brief to Dilli** through the standard design-brief flow (Campaign Planning DB entry +
Slack ping in `#design-campaigns`) — the same pattern `ratings-flyer` / `hero-image-review`
use. Never hand-write a `.docx` photo brief.

> v1 is intentionally qualitative and does not feed the Packaging score. The scored version
> (re-adding `hero_set` / `photo_coverage_pct` / `categories_ok` as optional input columns)
> is the v2 extension — until it lands, keep visuals in the narrative, not the numbers.

### Step 3 — Build the unified input CSV
Transform the exports into the schema in `references/ezcater-input-schema.md` (one row per
store × month, `platform = EZ`). Mapping notes:
- Operational Metrics → `on_time_pct`, `rejection_rate_pct`, `order_accuracy_pct`, `cancellation_pct`, `rating`, `review_count`
- 30-day sales / finance → `gross_sales`, `orders` (derive `aov` if not present)
- Rankings / ezRewards / Sponsored / Promotions → `ppp_bid_pct`, `ezrewards_pct`, `sponsored_spend`, `sponsored_attributed_sales`, `promo_count_active`
- `packaging_complete` → from a quick menu audit (per-person pricing, headcount tiers, lead-time-gated packages, required fields). If you can't audit it, default to a documented value and flag the gap — never guess a number that drives a finding.

Save the CSV to `inputs/` next to the source exports for the audit trail.

### Step 4 — Run the diagnostic
```bash
# team (deps installed --user):
python3 scripts/run_diagnostic.py --client <slug> --inputs-dir <inputs-dir> --json <out.json>
# local dev:
/Users/maxx/Desktop/spice-team-skills/skills/client-diagnostics/.venv/bin/python \
  scripts/run_diagnostic.py --client <slug> --inputs-dir <inputs-dir> --json <out.json>
```
The runner prints a markdown action plan to stdout and (with `--json`) writes the full
result. Surface the **foundation-gate banner verbatim** — if it triggered, the plan leads
with fixing fundamentals and visibility spend is HOLD.

### Step 5 — Return the result
Post back: the foundation-gate status, tier breakdown (N Green / Yellow / Red / New), the
badge funnel line, the top `this_cycle` actions, the **Storefront visuals** section from
Step 2b (hero / photo coverage / categories / packaging), and the **buyer-side paid signals**
(ezRewards / Sponsored / promo / ranking) folded into the paid-levers read, plus any Dilli
brief routed. (Notion publishing — reusing the delivery orchestrator's `notion_assembly.py` + chart
helpers — is the Phase 4 extension; not wired yet.)

## What this reproduces

The deterministic core is regression-tested against the human Tiff's Treats audit
(Jun 25 2026): it reproduces the badge funnel (175 → 106 → 31 → 16 → 0) and all five
action moves (badge gap, on-time fixes, rejection config, problem children, promo engine).
See `tests/test_regression_tiffs.py`.

## Files in this skill

- `scripts/run_diagnostic.py` — CLI runner
- `ezcater_diagnostic/` — deterministic core (input_schema, scorers, tiering, badge, findings, radar, action_plan, report, run)
- `references/ezcater-diagnostic-framework.md` — methodology (radar, gate, sub-buckets, tiers, badge, patterns)
- `references/ezcater-input-schema.md` + `ezcater-input-template.csv` — the input contract
- `references/ezcater-export-sop.md` — the four browser exports + where to get them
- `clients/<slug>.json` — per-client config
- `tests/` — unit + Tiff's regression suite

## Anti-patterns

- Don't guess `packaging_complete` or any metric that drives a finding — flag the gap instead.
- Don't guess visual coverage or paid-lever status — read the live buyer-facing storefront (and ezManage when available), or flag it. Never invent a photo % or a bid rate.
- Don't run weekly. Catering is a **monthly** service; weekly cadence breaks the capacity model.
- Don't treat "levers off" as a fire — it's the opportunity. The `levers_all_off` finding (high) carries the action; the tier reflects actual fulfillment health.
