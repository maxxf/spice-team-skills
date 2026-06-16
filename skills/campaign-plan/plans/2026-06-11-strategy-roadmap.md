# Strategy & Roadmap Mode Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the interactive tier → strategy → events → roadmap mode to the campaign-plan skill, per `specs/2026-06-11-strategy-roadmap-design.md`.

**Architecture:** Claude (SKILL.md Phase S script) owns all judgment + conversation gates; two new deterministic Python helpers own I/O — `strategy_read.py` (merge config + diagnostic + canonical performance into one per-location JSON) and `strategy_write.py` (split the 90-day grid across Q-plan tabs, write with an explicit `allow_protected` opt-in, persist `tier_strategy` to client config). The existing write guard stays; only the new writer opts in.

**Tech Stack:** Python 3.9 (`.venv` in skill dir), Google Sheets API v4 via existing `sheets_writer.py` service, existing `net_sales_pull.py` canonical pulls. No new dependencies. Tests = plain-assert script run with `.venv/bin/python` (no pytest in venv; codebase has no test framework — keep it dependency-free).

**Environment notes for the implementer:**
- Dev dir: `/Users/maxx/Desktop/Cowork/Skills/campaign-plan/` (NOT a git repo). Deployed copy: `/Users/maxx/Desktop/spice-team-skills/skills/campaign-plan/` (git repo, branch `main`). Commits happen there at sync time — there are no per-task commits in the dev dir. Run everything from the dev dir.
- Live verification client: `goop-kitchen` (`clients/goop-kitchen.json`, sheet `1C75jl5NBmGjTHOhUcf9Pky9eLzI3uYh4R6JlTT34kZA`). Service key at `~/.config/spice/google-sheets-writer.json`.
- **Brand-agnostic requirement is binding** (spec): no client names in code; everything from `clients/<slug>.json`.
- Mind the Sheets write quota (60 writes/min): don't loop live-write verification.

---

## Chunk 1: Reference doc + write-guard opt-in

### Task 1: `references/tier-framework.md` (canonical rubric doc)

**Files:** Create: `references/tier-framework.md`

- [ ] **Step 1: Write the doc.** Content = the spec's "tier framework" section verbatim, restructured as a standalone reference: per-location input axes table, the 5-tier table (Top 0–3% / Mid 4–8% / Low 8–15% / New 15–20% taper / Red hold), re-order logic, goal logic, vocabulary seeding map (Green/Yellow/Red → 5-tier with disambiguators), and a closing note: "Spend bands are canonical defaults; an approved session may persist client-specific bands in `clients/<slug>.json tier_strategy.tiers`." Source: copy from `specs/2026-06-11-strategy-roadmap-design.md` §"The tier framework" + §"Tier vocabulary mapping". No client names.

- [ ] **Step 2: Verify** — `grep -ci "goop\|venice" references/tier-framework.md` → `0`.

### Task 2: `allow_protected` opt-in in `sheets_writer.py`

**Files:** Modify: `references/sheets_writer.py` — `assert_safe_to_write` (~line 247), `clear_range` (~268), `write_range` (~276), `write_full_tab` (~359), and the tab-creation helper that guards new tabs (find via `grep -n "assert_safe_to_write" references/sheets_writer.py` — every call site stays default-False).

- [ ] **Step 1: Thread the parameter.** Signature changes (defaults preserve all existing behavior):

```python
def assert_safe_to_write(sheet_id: str, range_or_name: str, allow_protected: bool = False) -> None:
    """Guardrail: refuse to write a range whose tab is on the protected list.
    allow_protected=True is the explicit opt-in used ONLY by strategy_write.py
    (the Plan-campaigns mode is the one authorized writer for Q-plan tabs)."""
    if allow_protected:
        return
    ...  # body unchanged
```

`clear_range`, `write_range`, `write_full_tab` each gain `allow_protected: bool = False` and pass it through to `assert_safe_to_write`. **No other call site changes** — `refresh.py` and all existing writers stay default-False.

Also add two small public helpers here (verified absent from `sheets_writer.py` — this is required work, not contingency):

```python
def read_range(sheet_id: str, range_a1: str) -> list:
    """Read values from a range. Reads are never guarded."""
    r = _service().spreadsheets().values().get(spreadsheetId=sheet_id, range=range_a1).execute()
    return r.get("values", [])


def create_tab(sheet_id: str, title: str, allow_protected: bool = False) -> int:
    """Create a new tab; returns its gid. Guarded like writes (Q-plan creation needs the opt-in)."""
    assert_safe_to_write(sheet_id, f"'{title}'!A1", allow_protected=allow_protected)
    r = _service().spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={
        "requests": [{"addSheet": {"properties": {"title": title}}}]}).execute()
    return r["replies"][0]["addSheet"]["properties"]["sheetId"]
```

- [ ] **Step 2: Verify guard still bites.** Run:
```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'references'); import sheets_writer as sw
try:
    sw.assert_safe_to_write('x', \"'Q3 Plan'!A1\"); print('FAIL: guard did not raise')
except PermissionError: print('OK: default still raises')
sw.assert_safe_to_write('x', \"'Q3 Plan'!A1\", allow_protected=True); print('OK: opt-in passes')
"
```
Expected: both `OK` lines.

- [ ] **Step 3: Regression — rebuild goop reporting tabs untouched-guard intact:**
```bash
.venv/bin/python references/refresh.py --client goop-kitchen --no-drive-pull
```
Expected: completes with `QA: ✓ structure valid`, no PermissionError, no Q-plan tab modified.

## Chunk 2: `strategy_read.py`

### Task 3: pure merge logic + CLI

**Files:** Create: `references/strategy_read.py` · Test: `tests/test_strategy.py` (created here, extended in Task 4)

- [ ] **Step 1: Write the failing test** (`tests/test_strategy.py`, plain asserts):

```python
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
```

- [ ] **Step 2: Run to verify it fails** — `.venv/bin/python tests/test_strategy.py` → `ModuleNotFoundError: strategy_read`.

- [ ] **Step 3: Implement `references/strategy_read.py`:**

```python
#!/usr/bin/env python3
"""Strategy-session read layer — merge saved tier recs + diagnostic tiers + canonical
performance into one per-location JSON for the Plan-campaigns conversation.

Brand-agnostic: everything comes from clients/<slug>.json + that client's sheets.

Usage:  python strategy_read.py --client goop-kitchen [--weekstart YYYY-MM-DD]
Output: one JSON object on stdout (spec: specs/2026-06-11-strategy-roadmap-design.md §Interfaces).
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STALE_DAYS = 92  # ~1 quarter — re-order rates older than this get flagged


def _cnum(v):
    s = str(v).replace("$", "").replace(",", "").replace("%", "").replace("x", "").strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def merge_locations(saved: dict, diag_colors: dict, perf: dict, asof: str) -> dict:
    """Pure merge per the spec: saved recs seed if present, else diagnostic color;
    performance overlays; flags = reorder_stale | perf_above_tier | perf_below_tier."""
    names = sorted(set(saved) | set(diag_colors) | set(perf))
    asof_d = dt.date.fromisoformat(asof)
    locations, diag_only, perf_only = [], [], []
    for n in names:
        s, color, p = saved.get(n), diag_colors.get(n), perf.get(n)
        if p is None and (s or color):
            diag_only.append(n)
        if p is not None and s is None and color is None:
            perf_only.append(n)
        flags = []
        if s and s.get("reorder_captured"):
            try:
                if (asof_d - dt.date.fromisoformat(s["reorder_captured"])).days > STALE_DAYS:
                    flags.append("reorder_stale")
            except ValueError:
                flags.append("reorder_stale")
        roas = (p or {}).get("roas")
        # disagreement heuristics (proposal hints only — Claude decides at the gate)
        eff_tier = (s or {}).get("tier") or {"Green": "Top/Mid", "Yellow": "Mid/Low", "Red": "Red"}.get(color or "", "")
        if roas is not None:
            if roas > 6 and eff_tier in ("Mid/Low", "Low", "Red"):
                flags.append("perf_above_tier")
            if roas is not None and roas < 4 and eff_tier in ("Top", "Top/Mid"):
                flags.append("perf_below_tier")
        locations.append({
            "location": n, "saved": s,
            "diagnostic": {"color": color} if color else None,
            "performance": p, "flags": flags,
        })
    return {"locations": locations,
            "unmatched": {"diagnostic_only": diag_only, "performance_only": perf_only}}


def _perf_from_canonical(cfg: dict, weekstart: str) -> dict:
    """Per-location performance from the canonical weekly sales sheet (same source the
    Dashboard uses). Returns {location: {roas, spend_pct, mkt_driven_pct, sales}}."""
    import net_sales_pull as nsp
    sm = nsp.pull_sales_metrics(cfg["net_sales_sheet_id"], weekstart,
                                cfg.get("net_sales_platform_tab", "Weekly Platform Overview 2.0"),
                                cfg.get("net_sales_location_tab", "By Location 2.0"))
    out = {}
    for loc, m in (sm.get("location") or {}).items():
        sales = _cnum(m.get("total_sales"))
        mds = _cnum(m.get("mktg_driven_sales"))
        # mkt_driven_pct is not a METRIC_KEYS metric — derive it from mktg_driven_sales/total_sales
        out[loc] = {"roas": _cnum(m.get("roas")), "spend_pct": _cnum(m.get("mkt_spend_pct")),
                    "mkt_driven_pct": round(mds / sales * 100, 1) if (mds and sales) else None,
                    "sales": sales}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--weekstart", help="ISO Monday; default = last completed week")
    args = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = json.load(open(os.path.join(root, "clients", f"{args.client}.json")))
    today = dt.date.today()
    monday = today - dt.timedelta(days=today.weekday())
    weekstart = args.weekstart or (monday - dt.timedelta(days=7)).isoformat()

    saved = (cfg.get("tier_strategy") or {}).get("locations") or {}
    diag = {}
    if cfg.get("net_sales_sheet_id"):
        try:
            import net_sales_pull as nsp
            diag = nsp.pull_tier_map(cfg["net_sales_sheet_id"], cfg.get("tier_tab", "By Tier"))
        except Exception as e:
            print(f"(no diagnostic tier map: {str(e)[:60]})", file=sys.stderr)
    perf = {}
    if cfg.get("net_sales_sheet_id"):
        try:
            perf = _perf_from_canonical(cfg, weekstart)
        except Exception as e:
            print(f"(no canonical performance: {str(e)[:60]})", file=sys.stderr)

    out = merge_locations(saved, diag, perf, asof=today.isoformat())
    out.update({"client": args.client, "asof": today.isoformat(), "weekstart": weekstart,
                "tier_params": (cfg.get("tier_strategy") or {}).get("tiers") or {},
                "roadmap": (cfg.get("tier_strategy") or {}).get("roadmap")})
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test** — `.venv/bin/python tests/test_strategy.py` → `strategy_read merge: OK`.

- [ ] **Step 5: Live read against goop:**
```bash
.venv/bin/python references/strategy_read.py --client goop-kitchen | .venv/bin/python -m json.tool | head -40
```
Expected: JSON with ~15 locations, each with `diagnostic.color` (9 tiered) + `performance` numbers; `unmatched` lists plausible; no traceback. Spot-check one location's roas/spend_pct against the live Dashboard By Location.

## Chunk 3: `strategy_write.py`

### Task 4: window splitting + grid building (pure) + CLI

**Files:** Create: `references/strategy_write.py` · Modify: `tests/test_strategy.py` (append)

- [ ] **Step 1: Append failing tests:**

```python
import strategy_write as sww

# split_window_by_quarter: 13 ISO Mondays spanning Q2/Q3 → two tabs
weeks = sww.window_weeks("2026-06-15", n_weeks=13)
assert weeks[0] == "2026-06-15" and len(weeks) == 13 and weeks[-1] == "2026-09-07"
split = sww.split_by_quarter(weeks)
assert split == {"Q2 Plan": ["2026-06-15", "2026-06-22", "2026-06-29"],
                 "Q3 Plan": weeks[3:]}, split

# build_tab_matrix: title, events band, headers, tier sections in canonical order
grid = {"window": {"start": "2026-06-15", "end": "2026-09-07"},
        "events": [{"week": "2026-06-29", "label": "July 4"}],
        "rows": [{"tier": "Mid", "location": "LocB", "cells": {"2026-06-15": "S$45-S$10 All"}},
                 {"tier": "Top", "location": "LocA", "cells": {}}]}
m = sww.build_tab_matrix("Q2 Plan", split["Q2 Plan"], grid, client="Acme", year=2026)
assert m[0][0].startswith("Q2 2026 Plan — Acme")
assert m[1][sww.FIRST_WEEK_COL + 2] == "July 4"           # events band under the right week
assert m[2][:2] == ["Tier", "Location"]
tiers_in_order = [r[0] for r in m[3:] if r[0]]
assert tiers_in_order.index("Top") < tiers_in_order.index("Mid")  # canonical tier order
locb = next(r for r in m[3:] if len(r) > 1 and r[1] == "LocB")
assert locb[sww.FIRST_WEEK_COL] == "S$45-S$10 All" and locb[sww.FIRST_WEEK_COL + 1] == "—"
print("strategy_write grid: OK")
```

- [ ] **Step 2: Run to verify it fails** — `ModuleNotFoundError: strategy_write`.

- [ ] **Step 3: Implement `references/strategy_write.py`:**

```python
#!/usr/bin/env python3
"""Strategy-session write layer — the ONE authorized writer for Q-plan tabs.

Writes the approved rolling roadmap grid into the Q-plan tab(s) its window spans,
and persists the approved tier_strategy block to clients/<slug>.json.

Safety protocol (spec §6.2):
  --check          dry run: report each target tab's existing content ("empty" or rows),
                   write NOTHING.
  (default)        write tabs that are empty; REFUSE non-empty tabs.
  --overwrite      write all target tabs (Claude must have shown the user the diff and
                   gotten an explicit confirm in chat before passing this).

Usage:
  python strategy_write.py --client <slug> --grid grid.json [--check|--overwrite]
  python strategy_write.py --client <slug> --config tier_strategy.json   # config only
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TIER_ORDER = ["Top", "Mid", "Low", "New", "Red"]
FIRST_WEEK_COL = 2  # cols: 0=Tier 1=Location 2..=weeks


def window_weeks(start: str, n_weeks: int = 13) -> list[str]:
    d = dt.date.fromisoformat(start)
    d -= dt.timedelta(days=d.weekday())          # snap to Monday
    return [(d + dt.timedelta(weeks=i)).isoformat() for i in range(n_weeks)]


def split_by_quarter(weeks: list[str]) -> dict:
    """{ 'Q3 Plan': [mondays...] } — tab names match FORWARD_PLAN_TABS convention."""
    out: dict = {}
    for w in weeks:
        q = (dt.date.fromisoformat(w).month - 1) // 3 + 1
        out.setdefault(f"Q{q} Plan", []).append(w)
    return out


def _wk_label(w: str) -> str:
    d = dt.date.fromisoformat(w)
    return f"W{d.isocalendar()[1]} {d.strftime('%-m/%-d')}"


def build_tab_matrix(tab: str, weeks: list[str], grid: dict, client: str, year: int) -> list:
    """Canonical Q-plan grid (spec §6.2 pinned format)."""
    events = {e["week"]: e["label"] for e in grid.get("events", [])}
    head = [f"{tab.split(' ')[0]} {year} Plan — {client}  (roadmap {grid['window']['start']} → {grid['window']['end']})"]
    band = ["", "Events:"] + [events.get(w, "") for w in weeks]
    hdr = ["Tier", "Location"] + [_wk_label(w) for w in weeks]
    m = [head, band, hdr]
    rows = grid.get("rows", [])
    for tier in TIER_ORDER:
        trows = [r for r in rows if r.get("tier") == tier]
        if not trows:
            continue
        for i, r in enumerate(sorted(trows, key=lambda r: r["location"])):
            cells = r.get("cells", {})
            m.append([tier if i == 0 else "", r["location"]] + [cells.get(w, "—") for w in weeks])
    return m


def _resolve_tab(sw, sheet_id: str, q_tab: str) -> str:
    """Map a computed 'Q3 Plan' name onto the sheet's actual tab if it exists under a naming
    variant ('Q3 Plan', 'Q3 2026 Plan', 'Q3 Plan 2026'). Returns the existing name, or q_tab
    unchanged (caller will create it)."""
    import re
    qn = q_tab.split(" ")[0]  # 'Q3'
    pat = re.compile(rf"^{qn}\s*(20\d\d)?\s*Plan(\s*20\d\d)?$", re.I)
    for name in sw.get_metadata(sheet_id)["tabs"]:
        if pat.match(name.strip()):
            return name
    return q_tab


def _existing(sw, sheet_id: str, tab: str):
    """Current content of a tab, or None ONLY if the tab doesn't exist. Auth/quota errors
    must surface, not silently route into tab creation."""
    try:
        vals = sw.read_range(sheet_id, f"'{tab}'!A1:Z60")
    except Exception as e:
        if "Unable to parse range" in str(e) or getattr(getattr(e, "resp", None), "status", None) == 400:
            return None  # tab genuinely missing
        raise
    return [r for r in (vals or []) if any(str(c).strip() for c in r)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--grid", help="path to grid JSON (spec §Interfaces)")
    ap.add_argument("--config", help="path to tier_strategy JSON to persist")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(root, "clients", f"{args.client}.json")
    cfg = json.load(open(cfg_path))

    if args.config:
        block = json.load(open(args.config))
        # MERGE into the existing block — Phase S calls --config several times (tier gate
        # writes `locations`, strategy gate writes `tiers`, write phase caches Notion ids);
        # a replace here would clobber the earlier gates' output.
        cur = cfg.get("tier_strategy") or {}
        cur.update(block)
        cur["updated"] = dt.date.today().isoformat()
        cfg["tier_strategy"] = cur
        json.dump(cfg, open(cfg_path, "w"), indent=2)
        print(f"config: tier_strategy keys merged: {sorted(block.keys())}")

    if not args.grid:
        return
    import sheets_writer as sw
    grid = json.load(open(args.grid))
    weeks = grid.get("weeks") or window_weeks(grid["window"]["start"])
    sheet_id = cfg["sheet_id"]
    client = cfg.get("client_display_name", args.client)
    by_tab = split_by_quarter(weeks)

    # NOTE: split_by_quarter keys carry no year — a window reaching January targets "Q1 Plan"
    # of whatever year's tab exists. The --check/--overwrite protocol surfaces any collision.
    for q_tab, tab_weeks in by_tab.items():
        year = dt.date.fromisoformat(tab_weeks[0]).year
        tab = _resolve_tab(sw, sheet_id, q_tab)
        existing = _existing(sw, sheet_id, tab)
        if args.check:
            n = len(existing) if existing else 0
            print(f"{tab}: {'MISSING (will create)' if existing is None else ('empty' if n == 0 else f'{n} non-empty rows')}")
            if existing:
                for r in existing[:6]:
                    print("   |", " · ".join(str(c) for c in r[:6]))
            continue
        if existing and not args.overwrite:
            sys.exit(f"REFUSING: '{tab}' has {len(existing)} non-empty rows. Re-run with "
                     f"--overwrite after the user confirms replacement (show them --check first).")
        if existing is None:
            sw.create_tab(sheet_id, tab, allow_protected=True)
        matrix = build_tab_matrix(tab, tab_weeks, grid, client, year)
        n = sw.write_full_tab(sheet_id, tab, matrix, section_header_rows=[1],
                              col_header_rows=[2], freeze_rows=3, freeze_cols=2,
                              title_rows=1, allow_protected=True)
        print(f"{tab}: wrote {n} rows ({len(tab_weeks)} weeks)")


if __name__ == "__main__":
    main()
```

**Implementation notes:** (a) `read_range`/`create_tab` are added to `sheets_writer.py` in Task 2 — this script just uses them; (b) `write_full_tab` clears `A1:Z1000` and unmerges — acceptable for Q-plan tabs being regenerated; (c) `_resolve_tab` handles the naming variants up front (SKILL.md's canonical table says "Q3 [year] Plan" while `FORWARD_PLAN_TABS` uses bare "Q3 Plan" — both exist in the wild, so the regex is required, not contingency).

- [ ] **Step 4: Run tests** — `.venv/bin/python tests/test_strategy.py` → both `OK` lines.

- [ ] **Step 5: Live `--check` against goop (read-only):**
```bash
echo '{"window":{"start":"2026-06-15","end":"2026-09-07"},"events":[],"rows":[]}' > /tmp/grid_check.json
.venv/bin/python references/strategy_write.py --client goop-kitchen --grid /tmp/grid_check.json --check
```
Expected: one line per spanned tab (`Q2 Plan` / `Q3 Plan` or the sheet's actual names after regex resolution) reporting empty/missing/N rows. **No writes.** If tab names on the real sheet differ, implement the regex resolution from the note and re-run.

## Chunk 4: SKILL.md + sync

### Task 5: SKILL.md — router + Phase S

**Files:** Modify: `SKILL.md` (description frontmatter + new sections)

- [ ] **Step 1: Update frontmatter description** — add strategy triggers: `"plan strategy for [client]"`, `"build the [client] roadmap"`, `"tier strategy"`, `"analyze [client] campaigns"`.

- [ ] **Step 2: Insert a `## Mode router (START HERE)` section** directly after the frontmatter intro, before "Strategy authorship". Content (verbatim spec §Entry point): the 3-mode table (Update reporting / Plan campaigns / Run analysis), route-directly-if-explicit-else-ask rule, and Run-analysis complete definition (calls `strategy_read.py`, answers in chat, zero writes, offers mode-switch for write asks).

- [ ] **Step 3: Insert `## Phase S: Plan campaigns (interactive strategy + roadmap session)`** after the router. It scripts the conversation Claude runs:
  1. **Read** — run `strategy_read.py --client <slug>`; load `references/tier-framework.md`.
  2. **Tier gate** — render the per-location scorecard (`Location · Goal(proposed→confirm) · ROAS · Spend% · Menu conv · Ops · Capacity · Re-order(saved→confirm) → Proposed tier · Why`); seed via the vocabulary map; flag movers + stale re-orders; prompt for missing re-order rates and `opened` dates for new-looking locations; color-term adjustments get mapped + confirmed back. **Data-source note:** `strategy_read.py` supplies tier color + ROAS/spend%/mkt-driven%/sales only — there is no wired source for Menu conv / Ops / Capacity. Render those columns as "—" and ask the GM to fill or confirm them at the gate (spec's "Diagnostic + GM confirm" mode); never invent values. **Nothing proceeds without explicit approval.** On approval: write `tier_strategy.locations` via `strategy_write.py --config`.
  3. **Strategy gate** — per-tier blocks per the rubric (spend band default vs envelope-if-given, 55/45 baseline tilted by re-order, campaign types per tier+goal, segmentation, decay/exit), every line citing its playbook rule. Approve/edit per tier → persist `tier_strategy.tiers`.
  4. **Events** — ask NROs/launches, LTOs, client moments, blackouts; pre-fill US holidays in window.
  5. **Roadmap gate** — draft the per-location weekly grid (13 wks) in chat as a markdown table grouped by tier with events band; iterate until approved.
  6. **Write** — build grid JSON → `strategy_write.py --grid` (run `--check` first; if any tab non-empty, show the user what's there and confirm before `--overwrite`). Create/update the Notion strategy page via Notion MCP (first run: resolve client's Documents Hub via search, confirm with user, cache `notion_parent_page_id` + `notion_strategy_page_id` via `--config`). Push each planned campaign through `add_campaign.py` as `Not started` with `--notes "Roadmap <window>"` (notes → "Performance Notes" property).
  7. **Notion page template** (client-shareable): why-this-quarter summary → per-tier sections (posture, goal, locations, spend %/$, campaign types, segmentation, key plays) → roadmap-at-a-glance table.
  Cross-reference: `specs/2026-06-11-strategy-roadmap-design.md` is the authority; edge cases (no diagnostic / new client / unmatched locations / envelope conflict / stale re-order) handled per its Edge-cases section.

- [ ] **Step 4: Update the canonical-tabs table** — change Q-plan tabs' "Auto / Human" from "Human-authored" to "**Session-authored** (Phase S writes on approval; weekly refresh never touches)". Bump skill `version:` to `0.2.0`.

- [ ] **Step 5: Verify brand-agnostic** — `grep -n -i "goop\|venice\|pasadena" SKILL.md` → only pre-existing illustrative references (reference-instance sheet id, Ro's W22 example); no new client-specific logic in the router/Phase S sections.

### Task 6: Full verification + sync to deployed repo

- [ ] **Step 1: Unit tests** — `.venv/bin/python tests/test_strategy.py` → all OK.
- [ ] **Step 2: Guard regression** — re-run the Task 2 Step 2 snippet → both OK lines.
- [ ] **Step 3: Reporting refresh regression** — `refresh.py --client goop-kitchen --no-drive-pull` → `QA: ✓ structure valid`.
- [ ] **Step 4: Live read** — `strategy_read.py --client goop-kitchen` returns clean JSON.
- [ ] **Step 5: Live `--check`** — Task 4 Step 5 command → dry-run report, no writes.
- [ ] **Step 6: Sync to deployed repo:**
```bash
cd /Users/maxx/Desktop/spice-team-skills/skills/campaign-plan
cp /Users/maxx/Desktop/Cowork/Skills/campaign-plan/SKILL.md .
cp /Users/maxx/Desktop/Cowork/Skills/campaign-plan/references/{sheets_writer.py,strategy_read.py,strategy_write.py,tier-framework.md} references/
mkdir -p tests && cp /Users/maxx/Desktop/Cowork/Skills/campaign-plan/tests/test_strategy.py tests/
cd /Users/maxx/Desktop/spice-team-skills && git add skills/campaign-plan && git status --short
```
- [ ] **Step 7: Commit as v1.31.0** (`v1.31.0 campaign-plan: interactive strategy + roadmap mode (3-way router, tier gate, Q-plan writer)`), then **ask Maxx before pushing** (house rule: no push without explicit approval).
