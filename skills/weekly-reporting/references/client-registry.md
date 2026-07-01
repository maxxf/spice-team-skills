# Client Registry

Per-client configuration for weekly reporting. The orchestrator looks up clients here to determine which platforms to expect, how to map store names, and where to find their tracker.

**Tracker URLs are also stored in each client's Notion page under the `Data Dashboard` property.**

**`UE Attribution Tier`** (default **2** if unset) controls UE marketing attribution — see `agents/ue-extraction.md` Step 3b:
- **2** — client runs UE ads. Ad-attributed orders/sales come from the Ads Manager **performance** export (`placement_v2` / `campaigns_summary_metrics`, date-filtered). As of Uber's 2026 change the settlement CSV no longer carries per-order ad attribution, so this export is mandatory. If ad spend > 0 but no ad orders are attributed, the run is **blocked** (`validate_report.py`).
- **1** — client does NOT run UE ads; offer-only attribution is correct. (Any UE ad spend > 0 on a Tier-1 client still blocks — it signals misconfig or unattributed ads.)

---

## goop Kitchen

- **Platforms:** Uber Eats, DoorDash, Grubhub
- **Locations:** 14 (California)
- **Location Tiers:** RED (2), YELLOW (2), GREEN (6), UNICORN/PINK (4)
- **Tracker URL:** https://docs.google.com/spreadsheets/d/18we-M-qVdug4LRZiolfScL3emVPE0AuL4Zb9Zqn_A3A/edit?gid=799349784#gid=799349784
- **Notion Client Page:** `2a6d3ff0-18e7-80d9-91ee-e460d6c021c5`
- **Tracker Structure:**
  - Tab "Weekly Platform Overview" (gid=799349784): 4 sections (OVERVIEW, UBER EATS, DOORDASH, GRUBHUB) x 17 metrics
  - Week columns run left-to-right (Week 43 → Week 13+), most recent on the right
  - GH shows $0 marketing spend from week 1+ onward, #DIV/0! in ROAS calcs
- **Client Tier:** Enterprise (DD ads billed via invoice, not settlement)
- **Reporter:** Manish
- **Store Name Mappings (Canonical → Platform names):**

| Canonical Name | UE | DD | GH (city, address) |
|---|---|---|---|
| Beverly Hills | goop kitchen (Beverly Hills) | goop kitchen (Beverly Hills @ Maple Plaza) | Goop Kitchen (Beverly Hills, 9254 Alden Dr) |
| Costa Mesa | goop kitchen (Costa Mesa) | goop kitchen (Costa Mesa) | Goop Kitchen (Costa Mesa, 1750 Newport Blvd) |
| Larchmont | goop kitchen (Larchmont) | goop kitchen (Larchmont) | Goop Kitchen (Los Angeles, 615 N Western Ave) |
| Pasadena | goop kitchen (Pasadena) | goop kitchen (Pasadena) | Goop Kitchen (Pasadena, 1060 E Colorado Blvd) |
| Pico-Robertson | goop kitchen (Pico-Robertson) | goop kitchen (Robertson) | Goop Kitchen (Los Angeles, 8600 W Pico Blvd) |
| San Jose | goop kitchen (San Jose) | goop kitchen (San Jose) | Goop Kitchen (San Jose, 949 Ruff Dr) |
| Santa Monica | goop kitchen (Santa Monica) | goop kitchen (Santa Monica Blvd) | goop Kitchen (Los Angeles, 11419 Santa Monica Blvd) |
| Sherman Oaks | goop kitchen (Sherman Oaks) | goop kitchen (Sherman Oaks) | Goop Kitchen (Los Angeles, 14435 Victory Blvd) |
| Silver Lake | goop kitchen (Silver Lake) | goop kitchen (Silver Lake @ Echo Park Eats) | Goop Kitchen (Los Angeles, 1411 W Sunset Blvd) |
| SoMa | goop kitchen (Soma) | goop kitchen (SoMa) | Goop Kitchen (San Francisco, 60 Morris St) |
| South Bay | goop kitchen (South Bay) | goop kitchen (South Bay) | Goop Kitchen (El Segundo, 710-D S Allied Way) |
| Studio City | goop kitchen (Studio City) | -- | Goop Kitchen (Los Angeles, 411 Lincoln Blvd) |
| Sunnyvale | goop kitchen (Sunnyvale) | goop kitchen (Sunnyvale) | Goop Kitchen (Sunnyvale, 1026 W Evelyn Ave) |
| Venice | goop kitchen (Venice) | goop kitchen (Venice) | -- |
| North Hollywood | -- | goop kitchen (North Hollywood, CA) | goop Kitchen (Los Angeles, 5643 Lankershim Blvd) |

> Note: "Robertson" on DD = "Pico-Robertson" on UE (confirmed, same location). North Hollywood on DD maps to Studio City in the tracker.

- **Quirks:** Client manages menus via OLO/Toast, has own Loop AI account. DD ad spend is invoiced separately (not in settlement CSV).
- **Excluded brands:** None
- **DD Portal Access:** Yes (invoiced — portal exports required for ad spend + attribution)
- **UE Ads Manager Access:** Yes
- **UE Attribution Tier:** 2 (runs UE ads — ad-attributed orders/sales REQUIRED from the Ads Manager performance export; see ue-extraction Step 3b)
- **Ad platforms:** UE Ads Manager, DD Sponsored Listings
- **Notion Portal:** https://www.notion.so/2a6d3ff018e780d991eee460d6c021c5

---

## Capriotti's

- **Platforms:** Uber Eats, DoorDash, Grubhub
- **Locations:** 175
- **Tracker URL:** https://docs.google.com/spreadsheets/d/1S7SwW92F1Z17wAMTzYt1FnO54YkhMox77rYNLnD8zXs/edit?gid=430331116#gid=430331116
- **Notion Client Page:** `1c8d3ff0-18e7-8068-965f-e7f4fdf82d19`
- **Reporter:** Manish
- **Store Name Mappings:** TBD (large portfolio)
- **Quirks:** Very low per-location rate ($5K for 175 locations). Exclude Wing Zone stores from GH extraction.
- **Excluded brands:** Wing Zone
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## BDS (Brooklyn Dumpling Shop) — Corp

- **Platforms:** Uber Eats, DoorDash, Grubhub
- **Locations:** 4 corporate (15 total grouped as 1 account)
- **Tracker URL:** https://docs.google.com/spreadsheets/d/1-Tt9oPbGVynpyFxXtEA7QkMQBATgT_HDCWHzykWUL3k/edit?gid=2009055606#gid=2009055606
- **Notion Client Page:** `1c8d3ff0-18e7-80e9-b9d6-fbddc2ae5167`
- **Reporter:** Dulari
- **Corp Locations:** East Village, Upper East Side, Garden City, Dallas
- **Quirks:** Franchise model, separate Canada billing
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## Fresh Kitchen

- **Platforms:** Uber Eats, DoorDash, Grubhub
- **Locations:** 10+ (South Florida priority)
- **Tracker URL:** https://docs.google.com/spreadsheets/d/18M3Ic9jhpkMfRNJn9oOoTsgdRJrNEq5TasjfkD9dcLI/edit?gid=971831039#gid=971831039
- **Notion Client Page:** `312d3ff0-18e7-8120-b418-eb43987f2166`
- **Reporter:** Manish
- **Quirks:** Campaign ROAS tracked by Manish's separate tracker. FK doesn't want to BOGO the bowl.
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** Yes
- **Ad platforms:** UE Ads Manager, DD Sponsored Listings

---

## Everytable

- **Platforms:** Uber Eats, DoorDash, Grubhub
- **Locations:** TBD
- **Tracker URL:** https://docs.google.com/spreadsheets/d/1D1D_bF1wxYa2taJyTLoYj_NfimjhSzIKG5XS9ruNrlg/edit?gid=971831039#gid=971831039
- **Notion Client Page:** `2edd3ff0-18e7-80e6-9992-e8a483f876c0`
- **Reporter:** Manish
- **Quirks:** Data has had formula errors. Client manages ET-side implementation.
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## Abby's Bagels

- **Platforms:** Uber Eats, DoorDash, Grubhub
- **Locations:** TBD
- **Tracker URL:** https://docs.google.com/spreadsheets/d/1nuMy8pfhuMXuSglm1iM9PFjTd8B3FwPcWMG54EdVFrM/edit?gid=773581537#gid=773581537
- **Notion Client Page:** `2a9d3ff0-18e7-80b3-98a6-c13a369696df`
- **Reporter:** Manish
- **Quirks:** None noted
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## AWAN

- **Platforms:** Uber Eats, DoorDash (Grubhub inactive)
- **Locations:** 3 (West Hollywood, Venice, Larchmont)
- **Tracker URL:** https://docs.google.com/spreadsheets/d/1PWrPQx7RHh_7Bc-yigjqmXFcAwF3_Iv7UUJ1e08a7Tc/edit?gid=971831039#gid=971831039
- **Reporter:** Manish
- **Quirks:** Same owner as Dayglow (separate brand, separate reporting). Shares Slack channel #int-awan-dayglow.
- **Excluded brands:** Dayglow (do NOT mix brands)
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** Yes
- **Ad platforms:** UE Ads Manager, DD Sponsored Listings

---

## Dayglow

- **Platforms:** Uber Eats, DoorDash (Grubhub inactive)
- **Locations:** 6 (Chicago, Silver Lake, Venice, WEHO, Larchmont, Brooklyn)
- **Tracker URL:** https://docs.google.com/spreadsheets/d/1DGMUYGzq6LzZmwZLCyXiUjUVwScQS8T94ReugAF21xo/edit?gid=1700502115#gid=1700502115
- **Notion Client Page:** `28dd3ff0-18e7-8005-8592-cfc97a9c6e2d`
- **Reporter:** Manish
- **Store Name Mappings:**
  - DD: "Dayglow (N Kimball Ave)" = Chicago, "Dayglow (Rose Ave)" = Venice, etc.
  - UE: TBD
- **Quirks:** Same owner as AWAN (separate brand, separate reporting). Menu hours issue (turned off Jan 30, never re-enabled).
- **Excluded brands:** AWAN
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** Yes
- **Ad platforms:** UE Ads Manager, DD Sponsored Listings

---

## Teleferic Barcelona

- **Platforms:** Uber Eats, DoorDash, Grubhub
- **Locations:** 7 (LA, Scottsdale, Long Beach, others)
- **Tracker URL:** https://docs.google.com/spreadsheets/d/1FqWKZP3bzx8o4jvwQuYar0FOJ_wvKn_5BMJoBmTLZGE/edit?gid=971831039#gid=971831039
- **Notion Client Page:** `2e8d3ff0-18e7-80bc-b9e0-e70424630651`
- **Reporter:** Manish
- **Logins:**
  - UE: Already have access
  - DD: success+teleferic@spicedigital.co / Delivery123!
  - GH: success+teleferic@spicedigital.co / Delivery123!
- **Quirks:** Wine category expansion in progress
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## PRET A Manger

- **Platforms:** Uber Eats, DoorDash, Grubhub
- **Locations:** 58 (NYC to start)
- **Tracker URL:** https://docs.google.com/spreadsheets/d/16LCRjxQJuCMVjyQvy6MWOs14rCUkI5RZiFI5GcUD6aI/edit?gid=971831039#gid=971831039
- **Notion Client Page:** `30cd3ff0-18e7-80b8-995c-fc66b87a5297`
- **Reporter:** Dulari
- **Quirks:** Menu manager = Deliverect. SOW started Feb 25, 2026. Newer client — may not have full 2026 backfill scope.
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## Counter Service

- **Platforms:** Uber Eats, DoorDash, Grubhub
- **Locations:** 4
- **Tracker URL:** https://docs.google.com/spreadsheets/d/1jJ_RJphEEXZgPv9XRl2tscCxsFxEtQQBhz03wGRtZrg/edit?gid=480732159#gid=480732159
- **Notion Client Page:** `2e9d3ff0-18e7-804e-88cf-c5d6728b75ea`
- **Reporter:** Dulari
- **Quirks:** Also has Paid Media service
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## Menya Ultra

- **Platforms:** DoorDash, Uber Eats (NO Grubhub, NO website delivery)
- **Locations:** 3 (San Diego — Clairemont, Mira Mesa, UTC La Jolla)
- **Tracker URL:** TBD (task to create exists, URL not yet shared)
- **Notion Client Page:** `1ddd3ff0-18e7-8039-bd8e-c1e659f952a6`
- **Reporter:** Ana (was Manish)
- **Logins:**
  - DD: success+menya@spicedigital.co / Delivery123! or Spice2025!
  - GH: success+menya@spicedigital.co / Delivery123! or Spice2025!
- **Quirks:** Client cares most about net payout over gross sales. Weekly reports due Tuesdays.
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## Ahipoki

- **Platforms:** Uber Eats, DoorDash, Grubhub
- **Locations:** 20+ (Arizona + California)
- **Tracker URL:** TBD (tracker exists per task history, URL not yet shared)
- **Reporter:** Dulari
- **Quirks:** Locations split across AZ and CA for state-level rollup
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## MBFS (My Big Fat Shawarma)

- **Platforms:** Uber Eats, DoorDash
- **Locations:** TBD
- **Tracker URL:** TBD
- **Reporter:** Dulari
- **Quirks:** None noted
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## Cal's Corner

- **Platforms:** TBD
- **Locations:** TBD
- **Tracker URL:** TBD
- **Reporter:** Dulari
- **Quirks:** Unpredictable performance (similar to Gertie)
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## Westville NYC

- **Platforms:** Uber Eats, DoorDash, Grubhub
- **Locations:** 10 NYC + pilot (Arlington VA, Long Island City)
- **Tracker URL:** Not built yet (onboarding task due Apr 22)
- **Notion Client Page:** `326d3ff0-18e7-8040-be5a-ef6c701c497a`
- **Reporter:** Santiago (new)
- **Quirks:** No price markup on 3PD, WhatsApp communication
- **Excluded brands:** None
- **DD Portal Access:** TBD
- **UE Ads Manager Access:** TBD
- **Ad platforms:** TBD

---

## Reporting Assignments

**Current split (from Ro, March 2026):**

| Reporter | Clients |
|----------|---------|
| **Manish** | goop Kitchen, Capriotti's, Everytable, AWAN, Dayglow, Menya Ultra, Teleferic, Abby's |
| **Dulari** | Ahipoki, Counter Service, BDS Corp, MBFS, Cal's Corner, PRET |
| **Ana** | Taking over Menya, MBFS, Abby's (lead); supporting AWAN/Dayglow, Teleferic |
| **Santiago** | BDS, Counter Service, Ahipoki, Capriotti's, Westville (support) |

---

## Reporting Template

- **Template URL:** https://docs.google.com/spreadsheets/d/1It7JPsoHouNTQsRXzl9UVEf4vCufLreJ/edit?gid=971831039#gid=971831039
- **Template Guide (Notion):** https://www.notion.so/2e9d3ff018e7814288e9d82c5aef9728
- **Standard Tabs:** Weekly Platform Overview, By Location, Focus vs Mature, Ops - Focus Locations, Campaign Tracker, DD_Raw_Promos, DD_Raw_SL, UE_Raw_Ads, UE_Raw_Offers, Location_Map, Instructions

---

*Add new clients as they onboard. Keep store name mappings updated after each first run. Tracker URLs should also be set in the Notion client page `Data Dashboard` property.*
