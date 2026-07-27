# Cross-Cutting Patterns (Orchestrator-owned)

Patterns spanning 2+ sub-skill domains live here. Per-domain patterns live in `Cowork/Skills/diagnostic-<sub>/references/patterns-<sub>.md` (Wk 2 work).

The Location Tier Strategy is the canonical cross-cutting pattern: each store gets per-bucket scores from menu/ops/campaigns sub-skills, then the orchestrator merges into a single rollup.

---

## Location Tier Strategy (Green / Yellow / Red / New)

Replaces the old A/B/C-by-payout tiering. Every store is classified across three sub-buckets, then rolled up to a single tier. The tier dictates the default action.

### Sub-bucket scoring (per store)

Each sub-bucket scored Healthy / Watch / Broken:

**Menu performance**
- **Healthy**: UE menu CVR ≥ cuisine "Average" benchmark, photo coverage ≥ 80%, hero set, all categories populated
- **Watch**: CVR within 20% below benchmark, OR photo coverage 50–80%, OR 1 category empty
- **Broken**: CVR <20% below benchmark, OR photo coverage <50%, OR 2+ categories empty, OR no hero

**Ops performance**
- **Healthy**: error rate <2%, cancellation <2%, uptime >97%, rating ≥4.5, hours accurate, no involuntary downtime events
- **Watch**: error rate 2–5%, OR cancellation 2–5%, OR uptime 90–97%, OR rating 4.2–4.5, OR an intentional/capacity downtime event (merchant-triggered temporary closure, high dasher-wait auto-pause)
- **Broken**: error rate >5%, OR cancellation >5%, OR uptime <90%, OR rating <4.2, OR repeated hours-mismatch incidents, OR an **involuntary downtime event** (DoorDash auto-pause on high avoidable/POS-cancel rate, or a dasher-reported store closure)

> Discrete downtime **events override the smoothed averages** — read the DoorDash
> downtime export by category, don't collapse it to one uptime %. See
> `diagnostic-framework.md` → "Discrete downtime EVENTS override the smoothed
> averages" for the full category → verdict table. Involuntary events force
> Broken even at 99% average uptime.

**Campaign performance**
- **Healthy**: blended ROAS ≥3.5x, spend efficient relative to incremental orders
- **Watch**: ROAS 2.5–3.5x, OR spend running but <10 incremental orders/week
- **Broken**: ROAS <2.5x, OR ad spend running while ops Broken (money on fire), OR no campaigns active and store qualifies for them

> **Promo count is a margin NOTE, not a tier determinant.** A stacked promo mix
> no longer forces a Watch. ROAS is spend-weighted (blended), not a mean of
> per-row ROAS. See `diagnostic-framework.md`.

### Rollup rule

| Sub-bucket profile | Tier | Default action |
|---|---|---|
| All 3 Healthy | 🟢 **Green** | Scale: increase ad budget, expand to additional platforms, feature in marketing |
| Any 1 Watch, rest Healthy | 🟡 **Yellow** | Targeted fix on the weak bucket. Maintain current spend. |
| Any 1 Broken **or** 2+ Watch | 🔴 **Red** | **Stop campaigns at this store.** Fix the broken bucket(s) before any growth investment. |
| Launched <60 days, insufficient data | 🆕 **New** | Awareness investment + diagnostic re-run at 60-day mark to assign permanent tier |

**Edge cases:**
- **Ops Broken always wins → Red.** A store with Broken ops is Red, regardless of Menu/Campaign scores. This now actually fires on discrete involuntary downtime events (auto-pause / dasher-reported closure) because those events are detected, not averaged away. Money burning at a broken store — or spend pushed into a store DoorDash keeps pausing — is the fastest revenue leak.
- **New trumps the others.** If launched <60 days, the store is New, even if data already looks good. Don't stamp Green on a store that hasn't seen a normal cycle.
- **Single-platform stores.** If a store only has data on 1 of UE/DD/GH, score the available platform and note the limitation. Don't blend zeros.

### What this replaces

Prior A/B/C/Critical system tiered stores by net payout within geo segment, then forced Critical on ops-flagged stores. The new system flips the logic: **performance health drives tier, not revenue size.** A high-revenue store with Broken ops is Red, not "Tier A with a Critical flag." This makes the action plan unambiguous: Red stores stop spending, full stop.

For revenue-size analysis (e.g., "where is most of the money"), use the Top-15 by Net Payout view in the Location Tiers toggle. That stays as a separate cut, not a tier.

---

## Code synchronization

The rollup rule above is encoded in `orchestrator/cross_cutting.py::rollup_tiers`. **Update both the docs and the code together** when the rule changes.
