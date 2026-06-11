#!/usr/bin/env python3
"""Plain-assert tests for the pure logic in strategy_read / strategy_write.
Run: .venv/bin/python tests/test_strategy.py  (from the skill root)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "references"))

import strategy_read as sr

# merge_locations: saved recs win over diagnostic; performance overlays; flags fire
saved = {"Venice": {"tier": "Top", "goal": "payout", "reorder_rate": 0.42,
                    "reorder_captured": "2026-03-02"}}
diag = {"Venice": "Green", "Pasadena": "Yellow"}
perf = {"Venice":   {"roas": 7.2, "spend_pct": 2.1, "mkt_driven_pct": 31.0, "sales": 48210.0},
        "Pasadena": {"roas": 8.3, "spend_pct": 4.0, "mkt_driven_pct": 28.0, "sales": 30100.0},
        "Berkeley": {"roas": 0.0, "spend_pct": 0.0, "mkt_driven_pct": 0.0, "sales": 1200.0}}
out = sr.merge_locations(saved, diag, perf, asof="2026-06-11")
locs = {l["location"]: l for l in out["locations"]}
assert locs["Venice"]["saved"]["tier"] == "Top"
assert locs["Venice"]["diagnostic"]["color"] == "Green"
assert locs["Venice"]["performance"]["roas"] == 7.2
assert "reorder_stale" in locs["Venice"]["flags"]          # captured >1 quarter before asof
assert locs["Pasadena"]["saved"] is None                    # no saved rec
assert "perf_above_tier" in locs["Pasadena"]["flags"]       # Yellow color but ROAS >6x
assert out["unmatched"]["performance_only"] == ["Berkeley"] # in perf, not in diagnostic/saved
assert out["unmatched"]["diagnostic_only"] == []
print("strategy_read merge: OK")

import strategy_write as sww

# split_window_by_quarter: 13 ISO Mondays spanning Q2/Q3 → two tabs
weeks = sww.window_weeks("2026-06-15", n_weeks=13)
assert weeks[0] == "2026-06-15" and len(weeks) == 13 and weeks[-1] == "2026-09-07"
split = sww.split_by_quarter(weeks)
assert split == {"Q2 Plan": ["2026-06-15", "2026-06-22", "2026-06-29"],
                 "Q3 Plan": weeks[3:]}, split

# build_tab_matrix: title, events band, headers, tier sections + per-platform lanes
grid = {"window": {"start": "2026-06-15", "end": "2026-09-07"},
        "events": [{"week": "2026-06-29", "label": "July 4"}],
        "rows": [{"tier": "Mid", "location": "LocB", "platform": "UE", "cells": {"2026-06-15": "SL 3%"}},
                 {"tier": "Mid", "location": "LocB", "platform": "DD", "cells": {"2026-06-15": "S$45-S$10 All"}},
                 {"tier": "Top", "location": "LocA", "platform": "DD", "cells": {}}]}
m = sww.build_tab_matrix("Q2 Plan", split["Q2 Plan"], grid, client="Acme", year=2026)
assert m[0][0].startswith("Q2 2026 Plan — Acme")
assert m[1][sww.FIRST_WEEK_COL + 2] == "July 4"           # events band under the right week
assert m[2][:3] == ["Tier", "Location", "Platform"]
tiers_in_order = [r[0] for r in m[3:] if r[0]]
assert tiers_in_order == ["🟢 Top", "🔵 Mid"]               # emoji-coded, canonical order
locb_rows = [r for r in m[3:] if len(r) > 2 and (r[1] == "LocB" or r[2] in ("DD", "UE")) and r[0] in ("", "🔵 Mid")]
dd = next(r for r in m[3:] if r[1] == "LocB" and r[2] == "DD")
ue = next(r for r in m[3:] if r[1] == "" and r[2] == "UE")  # location label only on first lane
assert m.index(dd) < m.index(ue)                            # DD lane sorts first
assert dd[sww.FIRST_WEEK_COL] == "S$45-S$10 All" and dd[sww.FIRST_WEEK_COL + 1] == "—"
assert ue[sww.FIRST_WEEK_COL] == "SL 3%"
spans = sww.tier_row_spans(m)
assert spans == [("Top", 3, 4), ("Mid", 4, 6)], spans       # Mid block = 2 platform lanes
print("strategy_write grid: OK")
