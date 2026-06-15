# Location Tier Framework (canonical — decided 2026-06-11)

The rubric the Plan-campaigns strategy session uses to tier locations and set per-tier spend +
campaign strategy. Brand-agnostic: applies to every client; client-specific deviations persist in
`clients/<slug>.json` `tier_strategy`, never here.

**Tier is NOT a ROAS ranking.** It's an overlay of axes, and spend runs *inverse* to
capacity/efficiency — the best at-capacity stores get the least spend; stores that need to grow
get the most, provided they clear the ops/menu gate. The organizing lens is the per-location
**goal**.

## The law underneath: the Spend Maturity Curve

**3P marketing spend is acquisition spend wearing a conversion costume.** The ROI of a marketing
dollar is a function of *where the location sits on its awareness curve*, not of how well the
location performs:

- **Mature location** — you already own the demand, so spend largely buys orders you'd have
  gotten anyway. Spend **cannibalizes**; pulling it back *lifts* net payout.
- **New / dark / scaling location** — spend is the only thing acquiring new eaters, so pulling it
  **bleeds** — you stop the one engine bringing people in.

The proof points (cross-client, why this is a law and not a single-client quirk):
- Ahipoki — pulled $65–70K of 3P spend over 4 months, sales stayed flat (mature → spend was
  cannibalizing).
- Counter Service — held spend flat, reallocated it, +23% sales (mix beats volume on a mature base).
- Struggling accounts — cutting spend lifted net payout up to 11% (cannibalization, quantified).
- Capriotti's — went dark on Uber Eats, cost ~$480K/quarter and a 23% drop in new-eater
  acquisition (the *other* end of the curve: spend was the acquisition engine).

This is the unifying frame under the 3% north star, the cannibalization audit, and every band
below. **The whole tier rubric is the Spend Maturity Curve made operational:** maturity (capacity
+ awareness) sets the goal, the goal sets the band. Top stores sit at the harvest end (spend ≈
cannibalization → trim toward 0–3%); New/Low sit at the acquisition end (spend = the engine → fund
to 8–20%); Red is off-curve until the foundations gate passes. A high ROAS at a mature store isn't
"performance" — it's harvesting demand you already own; a low ROAS at a new store isn't "failure" —
it's the cost of buying eaters that don't exist yet. That's why incrementality tests (stepped
pullbacks) are how we *locate* a store on the curve rather than trusting raw ROAS.

## Per-location inputs (the overlay)

| Axis | Source | Mode |
|---|---|---|
| **Goal** — top-line sales growth vs incremental payout | Proposed from capacity + tier signals; GM/client confirms | Confirm at gate, persisted |
| Ops health (ratings, fulfillment, errors, uptime) | Latest diagnostic / leaderboard | Auto where wired; else GM at gate |
| Menu strength (conversion) | Diagnostic | Auto where wired; else GM at gate |
| Campaign efficiency (ROAS, spend % of sales) | Canonical weekly sales sheet | Auto (`strategy_read.py`) |
| Capacity (at capacity / room to grow / needs base) | Diagnostic + GM confirm | Auto-propose, confirm |
| Re-order rate | **GM captures manually from platforms** | Prompted, persisted with capture date, re-confirmed each session |

## The 5 tiers

Every tier carries a fixed emoji + color, used consistently across the gate scorecard (chat), the
Q-plan tabs (emoji label + soft row tint, painted by `strategy_write.py`), and the Notion strategy
page — one visual language everywhere.

| Tier | Profile | Default goal | Spend (% of location sales) | Strategy posture |
|---|---|---|---|---|
| 🟢 **Top** | Great ops, at capacity, >6x ROAS | Incremental payout | **0–3%** | Protect efficiency: retention/loyalty lean; stepped-pullback tests to prove incrementality; new-cust only if re-order high |
| 🔵 **Mid** | OK ops, room to grow, 4–6x | **Either — explicit call required** | **4–8%** | Growth-goal: acquisition toward top of band. Payout-goal: hold spend, shift mix to efficiency |
| 🟠 **Low** | Weak-but-fixable ops, <4x, needs to grow | Top-line growth | **8–15%** | Acquisition-led base building paired with ops/menu fix workstream; lower ROAS accepted knowingly |
| 🟣 **New** | Brand new | Top-line growth | **15–20% for 4–8 wks, then taper** | Awareness + acquisition-heavy; re-diagnose at 60d |
| 🔴 **Red** | Ops/menu broken | Fix first | **0% — hold** | No spend until Cardinal Rule gate passes (rating ≥4.5, error <2%, uptime >95%, menu conv ≥20%, photos) |

**Don't confuse tier emoji with diagnostic colors** — the diagnostic's Green/Yellow/Red is a
different (3-color) vocabulary that only seeds the proposal; 🟠 Low is not diagnostic-Yellow and
🟢 Top is not diagnostic-Green.

## Top-tier acquisition: pulse-on-trigger, never sprinkle

Top stores are at capacity — always-on or scheduled acquisition there buys customers the store
can't serve incrementally (displaced orders or ops strain). The rules:

- **Default: holidays carry Top-tier acquisition.** The portfolio-wide holiday pushes (~3-4 per
  quarter at ~11x) are the built-in replenishment pulses.
- **Extra pulse only on trigger:** L4W trend negative AND lagging the tier cohort (vs-Tier
  ≤ −5 pts on the Dashboard) — i.e. base decay is outpacing holiday replenishment at that
  specific store.
- **Pulse shape:** 2 weeks, New-customer offer, ride the band to its ceiling (e.g. 1.5% → 3%) —
  **never break the band**. Clean on/off windows double as an incrementality read vs the tier
  cohort (comp methodology in SKILL.md).
- **Gate on re-order rate:** high re-order → pulsed customers convert to LTV, pulse pays. Low
  re-order → fix retention first; a pulse just rents volume.
- **Scheduling guard:** a store serving as a control for an active test never pulses during the
  test window.

## Re-order rate logic

- **High re-order** → new customers stick → justify acquisition at the top of the tier's band;
  tilt the New/Existing/Lapsed split toward **New**.
- **Low re-order** → acquisition leaks → tilt toward retention/reactivation; fix retention before
  scaling acquisition.

The 55/45 acquisition/retention baseline (meta-rule 4) is the starting split; re-order rate moves
it.

## Goal logic

The same metrics read differently per goal: 5x ROAS at 7% spend is fine for a growth store, a
problem for a payout store. Mid tier is where the growth-vs-harvest call is a genuine client
conversation — the tier gate forces it explicit, per location.

## Tier vocabulary seeding (diagnostic colors → 5-tier)

The diagnostic speaks Green/Yellow/Red; this rubric speaks Top/Mid/Low/New/Red. Colors only
*inform the proposal* — the scorecard always proposes in the 5-tier vocabulary:

| Diagnostic | Seeds to | Disambiguator |
|---|---|---|
| Green | Top or Mid | >6x ROAS **and** at capacity → Top; else Mid |
| Yellow | Mid or Low | ≥4x ROAS → Mid; <4x → Low |
| Red | Red | — |
| (any) location open <8 weeks | New | age wins over color |

Location age comes from an `opened` date in `tier_strategy.locations` when present; otherwise ask
the GM at the gate and save it. Saved `tier_strategy` recs are already 5-tier and need no mapping.
If the user adjusts in color terms ("keep Pico Yellow"), map via the table and confirm the
interpretation back ("Yellow at 5.1x → keeping Pico **Mid**").

## Defaults vs client reality

Spend bands above are canonical defaults; an approved session may persist client-specific bands in
`clients/<slug>.json` `tier_strategy.tiers` — config states the client's reality, this doc states
the defaults.
