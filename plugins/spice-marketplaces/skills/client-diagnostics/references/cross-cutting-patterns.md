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
- **Healthy**: error rate <2%, cancellation <2%, uptime >97%, rating ≥4.5, hours accurate
- **Watch**: error rate 2–5%, OR cancellation 2–5%, OR uptime 90–97%, OR rating 4.2–4.5
- **Broken**: error rate >5%, OR cancellation >5%, OR uptime <90%, OR rating <4.2, OR repeated hours-mismatch incidents

**Campaign performance**
- **Healthy**: blended ROAS ≥3.5x, spend efficient relative to incremental orders, no over-discounting
- **Watch**: ROAS 2.5–3.5x, OR promo stack ≥2 active, OR spend running but <10 incremental orders/week
- **Broken**: ROAS <2.5x, OR ad spend running while ops Broken (money on fire), OR no campaigns active and store qualifies for them

### Rollup rule

| Sub-bucket profile | Tier | Default action |
|---|---|---|
| All 3 Healthy | 🟢 **Green** | Scale: increase ad budget, expand to additional platforms, feature in marketing |
| Any 1 Watch, rest Healthy | 🟡 **Yellow** | Targeted fix on the weak bucket. Maintain current spend. |
| Any 1 Broken **or** 2+ Watch | 🔴 **Red** | **Stop campaigns at this store.** Fix the broken bucket(s) before any growth investment. |
| Launched <60 days, insufficient data | 🆕 **New** | Awareness investment + diagnostic re-run at 60-day mark to assign permanent tier |

**Edge cases:**
- **Ops Broken always wins.** A store with Broken ops is Red, regardless of Menu/Campaign scores. Money burning at a broken store is the fastest revenue leak.
- **New trumps the others.** If launched <60 days, the store is New, even if data already looks good. Don't stamp Green on a store that hasn't seen a normal cycle.
- **Single-platform stores.** If a store only has data on 1 of UE/DD/GH, score the available platform and note the limitation. Don't blend zeros.

### What this replaces

Prior A/B/C/Critical system tiered stores by net payout within geo segment, then forced Critical on ops-flagged stores. The new system flips the logic: **performance health drives tier, not revenue size.** A high-revenue store with Broken ops is Red, not "Tier A with a Critical flag." This makes the action plan unambiguous: Red stores stop spending, full stop.

For revenue-size analysis (e.g., "where is most of the money"), use the Top-15 by Net Payout view in the Location Tiers toggle. That stays as a separate cut, not a tier.

---

## Code synchronization

The rollup rule above is encoded in `orchestrator/cross_cutting.py::rollup_tiers`. **Update both the docs and the code together** when the rule changes.
