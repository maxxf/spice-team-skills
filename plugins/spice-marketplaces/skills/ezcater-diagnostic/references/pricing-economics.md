# ezCater Service — Pricing & Unit Economics (v1 model)

Verifies the plan's pricing against the catering hours model. Starting numbers — ratify
against real hours once the first cohort runs.

## Pricing (base + simplified per-location)

- **Base platform fee:** $500/mo
- **Per location:** $150/mo first 10, $75/mo beyond
- **Minimum:** 5 locations (Spice doesn't take brands under 5)
- **50+ locations:** custom enterprise quote (the formula below is the ceiling; discount from it)

`fee(n) = 500 + 150·min(n,10) + 75·max(0, n−10)`

## Cost model (monthly, marketing/visibility layer)

Offshore blended loaded rates — Ops $15/hr, GM $30/hr, +10% overhead.
- Ops hours/mo = `1.0 + 0.05·n` (export pulls + monthly report, scales mildly with stores)
- GM hours/mo = `1.0 + 0.02·n + 4/3` (strategy + quarterly diagnostic amortized)

## Result

| Locations | Catering fee/mo | Cost/mo | Margin | Ops hrs/mo | GM hrs/mo | DM equivalent | Below DM? |
|---|---|---|---|---|---|---|---|
| 5 | $1,250 | $101 | 91.9% | 1.25 | 2.43 | $1,750 | ✅ |
| 6 | $1,400 | $102 | 92.7% | 1.30 | 2.45 | $1,925 | ✅ |
| 10 | $2,000 | $108 | 94.6% | 1.50 | 2.53 | $2,625 | ✅ |
| 25 | $3,125 | $131 | 95.8% | 2.25 | 2.83 | $5,250 | ✅ |
| 50 | $5,000 | $168 | 96.6% | 3.50 | 3.33 | $9,625 | ✅ |
| 175 | $14,375* | $353 | 97.5% | 9.75 | 5.83 | $31,500 | ✅ |

\* 175 = custom enterprise tier; formula value is the pre-discount ceiling.

## Takeaways

- **Both verification gates pass:** margin ≥60% at every size (far above — 92–97%), and every
  tier is below the 3-platform DM equivalent.
- **Margin is not the constraint.** Offshore labor + a monthly cadence make this a very
  high-margin line. The real gates are the **$100K MRR cap** and **GM/ops capacity**
  (see the plan's trip-wire), not price.
- **Headroom exists to discount** large multi-unit chains aggressively and still clear 80%+
  margin — useful for landing an anchor enterprise account like Tiff's.
- DM-equivalent column uses the delivery ladder ($350 first 5, $175 after) purely as the
  "must be cheaper" reference; catering is a separate, leaner SKU.
