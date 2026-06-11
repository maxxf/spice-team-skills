#!/usr/bin/env python3
"""Strategy-session read layer — merge saved tier recs + diagnostic tiers + canonical
performance into one per-location JSON for the Plan-campaigns conversation.

Brand-agnostic: everything comes from clients/<slug>.json + that client's sheets.

Usage:  python strategy_read.py --client <slug> [--weekstart YYYY-MM-DD]
Output: one JSON object on stdout (spec: specs/2026-06-11-strategy-roadmap-design.md §Interfaces).
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import sys
import warnings

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
            if roas < 4 and eff_tier in ("Top", "Top/Mid"):
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
        # mkt_driven_pct is not a METRIC_KEYS metric — derive from mktg_driven_sales/total_sales
        out[loc] = {"roas": _cnum(m.get("roas")), "spend_pct": _cnum(m.get("mkt_spend_pct")),
                    "mkt_driven_pct": round(mds / sales * 100, 1) if (mds is not None and sales) else None,
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
