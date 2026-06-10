#!/usr/bin/env python3
"""One-command refresh of a client's campaign plan workbook.

The repeatable update loop, wrapped. Reads a per-client config from clients/<slug>.json,
then runs the two deterministic steps in order:

  1. db_to_tracker.py   — project the Campaign Planning DB rows -> tracker CSV   (PLANNING)
  2. build_campaign_plan_xlsx.py — render the formatted workbook + fold in perf  (REPORTING)

The only step this DOESN'T do is the Notion pull itself (querying the Campaign Planning DB
needs the MCP, which lives in the skill/Claude, not a plain script). The skill writes the
DB rows to <data_dir>/<campaigns_json> first; this wrapper does everything after that.

Usage:
  python references/refresh.py --client goop-kitchen
  python references/refresh.py --client goop-kitchen --as-of 2026-05-21

Config (clients/<slug>.json):
  client_display_name : title shown in the workbook
  data_dir            : folder holding the inputs (campaigns json, perf csv, ads csv)
  campaigns_json      : DB-rows JSON the skill wrote from Notion (relative to data_dir)
  campaign_perf_csv   : weekly-reporting campaign_performance.csv (relative to data_dir; optional)
  ads_detail_csv      : ads funnel CSV (relative to data_dir; optional)
  output              : where to write the .xlsx (drag this into the client's Drive folder)
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)  # allow importing sibling reference modules


def _resolve(data_dir: str, name: str | None) -> str | None:
    """Find the file by name. Checks (in order): absolute path; data_dir/inputs/; data_dir/.
    inputs/ is where Drive pulls land — checked first so Drive trumps stale local copies."""
    if not name:
        return None
    if os.path.isabs(name):
        return name if os.path.exists(name) else None
    for candidate in (os.path.join(data_dir, "inputs", name), os.path.join(data_dir, name)):
        if os.path.exists(candidate):
            return candidate
    return None


def _monday_of(d: dt.date) -> dt.date:
    """Return the Monday of the week containing d (ISO weekday 1 = Mon)."""
    return d - dt.timedelta(days=d.weekday())


def _maybe_pull_from_drive(cfg: dict, weekstart: str) -> int:
    """If the config has a drive_folder_id, download the Campaign Plan Inputs / <weekstart>/
    files into <data_dir>/inputs/ so the bridge can read them. Returns count downloaded.
    Silent no-op if drive_inputs module can't auth or folder is missing."""
    folder_id = cfg.get("drive_folder_id")
    data_dir = cfg["data_dir"]
    if not folder_id:
        return 0
    try:
        from drive_inputs import find_weekstart_folder, download_inputs
    except ImportError:
        print("   (drive_inputs unavailable — skipping Drive pull)")
        return 0
    ws_folder = find_weekstart_folder(folder_id, weekstart)
    if not ws_folder:
        print(f"   (no 'Campaign Plan Inputs / {weekstart}/' folder yet — using existing data_dir contents)")
        return 0
    local_inputs = os.path.join(data_dir, "inputs")
    paths = download_inputs(ws_folder, local_inputs)
    if paths:
        print(f"→ pulled {len(paths)} input file(s) from Drive `Campaign Plan Inputs/{weekstart}/`:")
        for p in paths:
            print(f"    {os.path.basename(p)}")
    return len(paths)


def _read_csv(path):
    import csv
    if not path or not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _load_net_sales(cfg, data_dir):
    """Load net (total) sales by platform + location from weekly-reporting, for the marketing-
    spend-% and marketing-driven-sales-% metrics. Looks for `net_sales.csv` (or weekly-
    reporting's `by_location.csv`) in the inputs. Flexible columns: Platform (optional),
    Location, and a net-sales column (Net Sales / Total Net Sales / Sales). Returns
    {"total","platform","location"} or None when no file is present."""
    import v2_aggregate as agg
    path = (_resolve(data_dir, cfg.get("net_sales_csv", "net_sales.csv"))
            or _resolve(data_dir, "by_location.csv"))
    rows = _read_csv(path)
    if not rows:
        return None

    def col(r, *names):
        for n in names:
            for key in r:
                if key.strip().lower() == n:
                    return r[key]
        return None

    out = {"total": 0.0, "platform": {}, "location": {}}
    for r in rows:
        net = agg._num(col(r, "net sales", "total net sales", "net_sales", "sales"))
        if not net:
            continue
        out["total"] += net
        plat = (col(r, "platform") or "").strip()
        if plat:
            out["platform"][plat] = out["platform"].get(plat, 0) + net
        loc = (col(r, "location", "locations", "store") or "").strip()
        if loc:
            out["location"][loc] = out["location"].get(loc, 0) + net
    return out if out["total"] else None


def _v2_refresh(cfg, args, tracker_csv, data_dir, weekstart, display):
    """v2 path: write the 9-tab live Sheet directly via the Sheets API + emit a Slack draft."""
    import sheets_writer as sw
    import v2_aggregate as agg
    import slack_draft as sd

    sheet_id = cfg["sheet_id"]
    # Friendly week label for the Dashboard title: "W22 (May 25–May 31)" derived from the
    # Monday weekstart, so every client reads consistently instead of a raw ISO date.
    _ws = dt.date.fromisoformat(weekstart)
    _we = _ws + dt.timedelta(days=6)
    week_label = f"W{_ws.isocalendar()[1]} ({_ws.strftime('%b %-d')}–{_we.strftime('%b %-d')})"
    print("→ v2: ensuring canonical tabs")
    sw.ensure_template_tabs(sheet_id)

    tracker_rows = _read_csv(tracker_csv)
    ads_rows = _read_csv(_resolve(data_dir, cfg.get("ads_detail_csv")))
    # offers CSV is optional; look for dd_offers / ue_offers in inputs, else the configured one
    offers_path = (_resolve(data_dir, cfg.get("offers_csv"))
                   or _resolve(data_dir, "dd_offers_%s.csv" % weekstart)
                   or _resolve(data_dir, "ue_offers_%s.csv" % weekstart))
    offers_rows = _read_csv(offers_path)

    # Prior-week comparison: read History BEFORE we overwrite this week's snapshot, so the
    # WoW columns + Portfolio Trend can reference the most recent earlier week.
    rollup = agg.history_weekly_rollup(sw.read_history(sheet_id))
    prior_week = max((w for w in rollup if w < weekstart), default=None)
    prior = rollup.get(prior_week) if prior_week else None
    prior_ads = prior["ads"] if prior else None
    prior_offers = prior["offers"] if prior else None
    if prior_week:
        print(f"   (comparing vs prior week {prior_week})")
    else:
        print("   (no prior week in History yet — WoW shows '—' until next week / backfill)")

    # Net sales (for the marketing-efficiency % metrics). Prefer a live cross-pull from the
    # client's weekly sales sheet; fall back to a net_sales.csv / by_location.csv in inputs.
    net_sales = None
    if cfg.get("net_sales_sheet_id"):
        try:
            import net_sales_pull as nsp
            net_sales = nsp.pull_net_sales(
                cfg["net_sales_sheet_id"], weekstart,
                cfg.get("net_sales_platform_tab", "Weekly Platform Overview 2.0"),
                cfg.get("net_sales_location_tab", "By Location 2.0"))
            if not (net_sales and net_sales.get("total")):
                net_sales = None
        except Exception as e:
            print(f"   (net-sales sheet pull failed: {str(e)[:90]})")
            net_sales = None
    if not net_sales:
        net_sales = _load_net_sales(cfg, data_dir)
    if net_sales:
        print(f"   (net sales: ${net_sales['total']:,.0f} total, {len(net_sales['platform'])} platforms, {len(net_sales['location'])} locations)")
    else:
        print("   (no net sales source — Mkt Spend % / Mkt-Driven Sales % show '—')")

    # Store-tier map (Red/Yellow/Green) from the sales sheet, for the By-Tier segmentation.
    tier_map = None
    if cfg.get("net_sales_sheet_id"):
        try:
            import net_sales_pull as nsp
            tier_map = nsp.pull_tier_map(cfg["net_sales_sheet_id"], cfg.get("tier_tab", "By Tier"))
            if tier_map:
                print(f"   (tier map: {len(tier_map)} locations tiered)")
        except Exception as e:
            print(f"   (tier-map pull skipped: {str(e)[:80]})")

    # Active Campaigns = a clean by-location view of what's actually running (ads + offers).
    # Planning/pipeline state stays internal in Notion + the GM-owned Q-Plan tabs. Falls back
    # to a flat Live list for planning-only clients with no performance exports yet.
    if ads_rows or offers_rows:
        groups = agg.active_campaigns_by_location(ads_rows, offers_rows, cfg.get("location_aliases"))
        n_ac = sw.write_active_campaigns_by_location(sheet_id, groups, week=week_label)
        print(f"   Active Campaigns by location: {n_ac} rows ({len(groups)} locations)")
    else:
        ac = [r for r in agg.active_campaigns_from_tracker(tracker_rows) if r.get("Status") == "Live"]
        print(f"   Active Campaigns (Live only): {sw.write_active_campaigns(sheet_id, ac, last_updated=weekstart)} rows")
    # Prior-week net sales (for the Net Sales / Mkt Spend % tile WoW — the sales sheet has it now).
    prior_net_total = None
    if cfg.get("net_sales_sheet_id"):
        try:
            import net_sales_pull as nsp
            pw = (dt.date.fromisoformat(weekstart) - dt.timedelta(days=7)).isoformat()
            pn = nsp.pull_net_sales(cfg["net_sales_sheet_id"], pw,
                                    cfg.get("net_sales_platform_tab", "Weekly Platform Overview 2.0"),
                                    cfg.get("net_sales_location_tab", "By Location 2.0"))
            prior_net_total = pn.get("total") or None
        except Exception:
            prior_net_total = None

    # Canonical weekly-reporting metrics (deduped, correct denominators) for the efficiency
    # sections. Per-campaign tabs stay export-derived.
    sales_metrics = None
    if cfg.get("net_sales_sheet_id"):
        try:
            import net_sales_pull as nsp
            sales_metrics = nsp.pull_sales_metrics(
                cfg["net_sales_sheet_id"], weekstart,
                cfg.get("net_sales_platform_tab", "Weekly Platform Overview 2.0"),
                cfg.get("net_sales_location_tab", "By Location 2.0"))
            if sales_metrics and sales_metrics.get("overview"):
                ov = sales_metrics["overview"]
                print(f"   (canonical metrics: Mkt Spend % {ov.get('mkt_spend_pct')}, ROAS {ov.get('roas')}, CPO {ov.get('cpo')})")
        except Exception as e:
            print(f"   (canonical metrics pull skipped: {str(e)[:80]})")
            sales_metrics = None

    dash = agg.dashboard_from_data(tracker_rows, ads_rows, offers_rows,
                                   history_rollup=rollup, weekstart=weekstart, net_sales=net_sales,
                                   location_aliases=cfg.get("location_aliases"), tier_map=tier_map,
                                   prior_net_total=prior_net_total, sales_metrics=sales_metrics)
    print(f"   Dashboard: {sw.write_dashboard(sheet_id, dash, client=display, week=week_label)} rows")
    try:
        print(f"   Charts: {sw.write_charts(sheet_id, dash)} embedded")
    except Exception as e:
        print(f"   (charts skipped: {str(e)[:90]})")
    try:
        seeded = sw.seed_definitions(sheet_id)
        if seeded:
            print(f"   Notes & Definitions: seeded {seeded} rows")
    except Exception as e:
        print(f"   (definitions seed skipped: {str(e)[:80]})")
    if ads_rows:
        print(f"   Ads Reporting: {sw.write_ads_reporting(sheet_id, agg.ads_reporting_from_csv(ads_rows, prior=prior_ads))} rows")
    if offers_rows:
        print(f"   Offers Reporting: {sw.write_offers_reporting(sheet_id, agg.offers_reporting_from_csv(offers_rows, prior=prior_offers))} rows")

    # History upsert (ads + offers) — idempotent per week; source for next week's WoW + trend.
    perf = []
    for a in ads_rows:
        perf.append({"campaign": a.get("Campaign", ""), "platform": a.get("Platform", ""),
                     "location": a.get("Locations") or a.get("Location", ""),
                     "spend": agg._num(a.get("Spend")),
                     "sales": agg._num(a.get("Attributed Sales") or a.get("Sales")),
                     "orders": agg._num(a.get("Orders")), "kind": "Ad"})
    for o in offers_rows:
        perf.append({"campaign": o.get("Promotion") or o.get("Offer") or o.get("Campaign", ""),
                     "platform": o.get("Platform", ""),
                     "location": o.get("Locations") or o.get("Location", ""),
                     "spend": agg._num(o.get("Promo Spend") or o.get("Discount Spend") or o.get("Spend")),
                     "sales": agg._num(o.get("Attributed Sales") or o.get("Sales")),
                     "orders": agg._num(o.get("Redemptions") or o.get("Orders")), "kind": "Offer"})
    if perf:
        print(f"   History: wrote {sw.write_history(sheet_id, agg.history_rows(weekstart, perf))} rows (this week)")

    # Slack draft (GM edits + sends)
    k = dash["kpis"]
    summary = {"headline": {"spend": k["total_spend"], "sales": k["total_sales"],
                            "blended_roas": k["blended_roas"]}}
    changes_path = os.path.join(data_dir, f"changes_{weekstart}.md")
    if os.path.exists(changes_path):
        summary["changes_md"] = open(changes_path).read()
    draft = sd.build_draft(summary)
    draft_path = os.path.join(data_dir, f"slack_draft_{weekstart}.txt")
    with open(draft_path, "w") as f:
        f.write(draft)

    # Final gate: structural QA. Surfaces off-by-one / drift before the GM ships it.
    v = sw.validate_sheet(sheet_id)
    if v["ok"]:
        print("   QA: ✓ structure valid")
    else:
        print("   QA: ✗ ISSUES FOUND —")
        for e in v["errors"]:
            print(f"      - {e}")

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    print(f"\n✅ {display} v2 campaign plan refreshed")
    print(f"   Live Sheet: {url}")
    print(f"   Slack draft: {draft_path}")
    if cfg.get("slack_channel"):
        print(f"   GM reviews the draft + sends to {cfg['slack_channel']} Monday.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True, help="client slug -> clients/<slug>.json")
    ap.add_argument("--as-of", default=None, help="reference date YYYY-MM-DD for Live/queue math (also drives the weekstart for Drive pull)")
    ap.add_argument("--overwrite-perf", action="store_true")
    ap.add_argument("--no-push", action="store_true", help="Skip publishing to the live Google Sheet (file only).")
    ap.add_argument("--no-drive-pull", action="store_true", help="Skip pulling inputs from Drive folder (uses local data_dir only).")
    args = ap.parse_args()

    cfg_path = os.path.join(SKILL, "clients", f"{args.client}.json")
    if not os.path.exists(cfg_path):
        sys.exit(f"no config at {cfg_path}. Create clients/{args.client}.json (see clients/goop-kitchen.json).")
    with open(cfg_path) as f:
        cfg = json.load(f)

    data_dir = cfg["data_dir"]
    display = cfg["client_display_name"]
    py = sys.executable
    tracker_csv = os.path.join(data_dir, f"{args.client}_tracker.csv")
    os.makedirs(data_dir, exist_ok=True)

    # Compute the weekstart (Monday of the as_of week) for Drive folder lookup.
    as_of_date = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()
    weekstart = _monday_of(as_of_date).isoformat()

    # Step 0 — PULL FROM DRIVE: download this week's inputs from the client's Drive folder
    # into <data_dir>/inputs/. Falls back gracefully if folder doesn't exist.
    if not args.no_drive_pull:
        _maybe_pull_from_drive(cfg, weekstart)

    # Step 1 — PLANNING: DB rows -> tracker CSV (if the Notion pull was written)
    campaigns_json = _resolve(data_dir, cfg.get("campaigns_json"))
    if campaigns_json:
        cmd = [py, os.path.join(HERE, "db_to_tracker.py"),
               "--db-json", campaigns_json, "--output", tracker_csv]
        if args.as_of:
            cmd += ["--as-of", args.as_of]
        print("→ planning: projecting Campaign Planning DB rows into tracker rows")
        subprocess.run(cmd, check=True)
    else:
        print(f"⚠️  no campaigns JSON found ({cfg.get('campaigns_json')}). "
              f"Run the Notion pull first (skill Phase 0). Using existing tracker if present.")
        if not os.path.exists(tracker_csv):
            sys.exit("no tracker CSV to render. Pull the DB rows first.")

    # v2 branch — write tabs directly via Sheets API (Dashboard / Active Campaigns / Ads
    # Reporting / Offers Reporting / History) + Slack draft. Skips the xlsx build + push,
    # which would clobber the v2 tabs. Gated on cfg["v2"] == true AND a sheet_id present.
    if cfg.get("v2") and cfg.get("sheet_id"):
        _v2_refresh(cfg, args, tracker_csv, data_dir, weekstart, display)
        return

    # Step 2 — REPORTING (v0.1): render workbook + fold in performance + ads funnel
    cmd = [py, os.path.join(HERE, "build_campaign_plan_xlsx.py"),
           "--client", display, "--tracker-csv", tracker_csv, "--output", cfg["output"]]
    perf = _resolve(data_dir, cfg.get("campaign_perf_csv"))
    ads = _resolve(data_dir, cfg.get("ads_detail_csv"))
    if perf:
        cmd += ["--campaign-perf-csv", perf]
    if ads:
        cmd += ["--ads-detail-csv", ads]
    if args.overwrite_perf:
        cmd += ["--overwrite-perf"]
    print("→ reporting: rendering workbook" + (" + performance" if perf else "") + (" + ads funnel" if ads else ""))
    subprocess.run(cmd, check=True)

    # Step 3 — PUBLISH: push the workbook into the client's Drive folder as a live Google Sheet
    # (in place, stable link). Auto-runs when the service-account key is present; --no-push skips.
    key_path = os.path.expanduser("~/.config/spice/google-sheets-writer.json")
    sheet_url = None
    if not args.no_push and os.path.exists(key_path):
        print("→ publishing: pushing to the live Google Sheet")
        r = subprocess.run([py, os.path.join(HERE, "push_to_sheet.py"),
                            "--client", args.client, "--xlsx", cfg["output"]],
                           capture_output=True, text=True)
        sys.stdout.write(r.stdout)
        if r.returncode != 0:
            print("⚠️  Sheet push failed:\n" + r.stderr.strip())
        else:
            for line in r.stdout.splitlines():
                if "https://" in line:
                    sheet_url = "https://" + line.split("https://", 1)[1].strip()

    print(f"\n✅ {display} campaign plan refreshed → {cfg['output']}")
    if sheet_url:
        print(f"   Live Sheet: {sheet_url}")
    elif not os.path.exists(key_path):
        print(f"   (No Sheets key found — file only. Drag into Drive folder {cfg.get('drive_folder_id','')} to share.)")
    if cfg.get("slack_channel"):
        print(f"   Post the Friday/Monday heads-up in {cfg['slack_channel']}.")


if __name__ == "__main__":
    main()
