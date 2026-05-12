# Menu & Storefront Pattern Library (v0.1)

Subset of `client-diagnostics/references/diagnostic-framework.md` scoped to the menu sub-skill (radar dims: Conversion, Traffic; tier sub-bucket: "menu").

## Patterns

| pattern_id | Trigger | Severity | Default deliverable |
|---|---|---|---|
| low_cvr_high_traffic | menu_cvr_pct < 18% AND storefront_to_menu_ctr_pct > 9% | high | optimized-menu-sheet (focus="category_consolidation") |
| low_photo_coverage | photo_coverage_pct < 50% | foundation | (foundation gate routing — orchestrator handles) |
| sku_sprawl | categories_count > 8 AND any category empty (categories_populated < categories_count) | medium | optimized-menu-sheet (focus="sku_rationalization") |

The "Window Shopper" pattern in the framework maps to `low_cvr_high_traffic` — high traffic with poor conversion means customers reach the menu but leave without ordering.

## Tier sub-bucket — Menu (per framework lines 89–92)

Each store gets a `menu` flag of green / yellow / red:

- **Healthy (green):** menu_cvr_pct ≥ 18% AND photo_coverage ≥ 80% AND hero_set AND categories_populated == categories_count
- **Watch (yellow):** menu_cvr_pct within 20% below 18% (≥ 14.4%) OR photo_coverage 50–80% OR exactly 1 category empty
- **Broken (red):** menu_cvr_pct < 80% of 18% (< 14.4%) OR photo_coverage < 50% OR 2+ categories empty OR hero_set is False

`new` is reserved for stores with insufficient history; Wk 2 synthetic data never produces it.

## Radar contributions (per framework Brand Health Radar table)

- **Conversion** (UE menu CVR, portfolio mean):
  - <15% → 3
  - 15–18% → 4.5
  - 18–20% → 5
  - 20–25% → 7
  - >25% → 8

- **Traffic** (storefront → menu CTR, portfolio mean):
  - <5% → 3
  - 5–7% → 4
  - 7–9% → 6
  - 9–12% → 7.5
  - >12% → 9

## Cuisine CVR benchmarks (framework lines 47–60, copy)

| Cuisine Type | Good CVR | Average CVR | Poor CVR |
|---|---|---|---|
| Fast Casual / QSR | 15–18% | 12–15% | <12% |
| Pizza / Italian | 16–20% | 13–16% | <13% |
| Asian (Chinese, Thai, Japanese) | 14–18% | 11–14% | <11% |
| Poke / Bowl / Health | 12–16% | 10–12% | <10% |
| Mexican / Latin | 14–18% | 11–14% | <11% |
| Indian / South Asian | 12–16% | 9–12% | <9% |
| Burger / American | 15–20% | 12–15% | <12% |
| Upscale Casual | 10–14% | 8–10% | <8% |
| Juice / Smoothie | 8–12% | 6–8% | <6% |
| Bakery / Dessert | 14–18% | 10–14% | <10% |

Wk 2 uses a single 18% benchmark (Spice fast-casual default). Cuisine-aware lookup is a Wk 3+ enhancement.
