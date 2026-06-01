#!/usr/bin/env python3
"""aggregate_platforms.py - Combine platform JSON outputs into unified CSVs + tracker column.

Usage:
    python aggregate_platforms.py --output-dir OUTPUT --store-map MAP.json \
        [--tracker-platform-csv PLATFORM.csv] [--tracker-location-csv LOCATION.csv] \
        [--current-week 13]

Reads *_results.json files from OUTPUT directory.
Produces: platform_overview.csv, by_location.csv, campaign_performance.csv, tracker_update.csv

Updated April 2026: Removed Gross Sales. Added Commissions, Net Sales, Other Adjustments.
Net Payout calculated from components. Net Payout % = Net Payout / Total Sales.
"""
import argparse, csv, json, glob, os, sys, re

PLATFORM_LABELS = {
    "uber_eats": "UBER EATS",
    "doordash": "DOORDASH",
    "grubhub": "GRUBHUB"
}

# Financial Waterfall (7) + Marketing Attribution (13) = 20 metrics
OVERVIEW_METRICS = [
    # Financial Waterfall
    "Total Sales", "Net Sales",
    "Commissions", "Commissions %",
    "Other Adjustments",
    "Net Payout", "Net Payout %",
    # Marketing Attribution
    "Marketing Driven Sales", "Organic Sales",
    "Total Orders", "Orders from Marketing", "Organic Orders", "AOV",
    "Ad Spend", "Discounts (Offers)",
    "Total Marketing Investment", "Marketing Credits",
    "Marketing Spend / Sales %",
    "Marketing ROAS", "Marketing CPO"
]

# Tracker paste metrics — same 20-metric order
TRACKER_METRICS = [
    "Total Sales", "Net Sales",
    "Commissions", "Commissions %",
    "Other Adjustments",
    "Net Payout", "Net Payout %",
    "Marketing Driven Sales", "Organic Sales",
    "Total Orders", "Orders from Marketing", "Organic Orders", "AOV",
    "Ad Spend", "Discounts (Offers)",
    "Total Marketing Investment", "Marketing Credits",
    "Marketing Spend / Sales %",
    "Marketing ROAS", "Marketing CPO"
]

LOC_METRICS = [
    "Total Sales", "Net Sales",
    "Commissions", "Commissions %",
    "Other Adjustments",
    "Net Payout", "Net Payout %",
    "Marketing Driven Sales", "Organic Sales",
    "Total Orders", "Orders from Marketing", "Organic Orders", "AOV",
    "Ad Spend", "Discounts (Offers)",
    "Total Marketing Investment", "Marketing Credits",
    "Marketing Spend / Sales %",
    "Marketing ROAS", "Marketing CPO"
]

# ── Formatting ──────────────────────────────────────────────────────────────

def fmt_currency(v):
    if v is None or v == 0: return "$0"
    return f"${v:,.0f}"

def fmt_currency_cents(v):
    if v is None or v == 0: return "$0.00"
    return f"${v:,.2f}"

def fmt_pct(v):
    if v is None: return "--"
    return f"{v:.0f}%"

def fmt_roas(v):
    if v is None: return "--"
    return f"{v:.1f}"

def fmt_int(v):
    if v is None or v == 0: return "0"
    return f"{v:,}"

def fmt_metric(name, value):
    if value is None:
        return "--"
    if "ROAS" in name:
        return fmt_roas(value)
    if "%" in name:
        return fmt_pct(value)
    if name == "AOV":
        return fmt_currency_cents(value)
    if "Orders" in name or name == "Total Orders":
        return fmt_int(int(value))
    if any(k in name for k in ["Sales", "Spend", "Payout", "Ad Spend", "Discounts",
                                 "Investment", "Commissions", "Adjustments"]):
        return fmt_currency(value)
    return str(value)

def fmt_delta(v):
    """Format a WoW or vs-avg delta as +X.X% or -X.X%."""
    if v is None: return "--"
    return f"{'+' if v >= 0 else ''}{v:.1f}%"


# ── Parse tracker value ─────────────────────────────────────────────────────

def parse_val(s):
    """Parse a formatted tracker value to float. Handles $1,234 / 5.3% / 10.3x / 1,234 / #DIV/0!"""
    if not s or s.strip() in ("", "--", "--*", "#DIV/0!"):
        return None
    s = s.strip()
    s = s.replace("$", "").replace(",", "").replace("%", "").replace("x", "")
    try:
        return float(s)
    except ValueError:
        return None


# ── Store map ───────────────────────────────────────────────────────────────

def load_store_map(fp):
    if not fp or not os.path.exists(fp):
        return {}
    with open(fp) as fh:
        return json.load(fh)

def normalize_store_name(name, store_map, city=None, address=None):
    if not name:
        return "Unknown"
    if name in store_map:
        return store_map[name]
    if city and address:
        composite = f"{name}|{city}|{address}"
        if composite in store_map:
            return store_map[composite]
    name_lower = name.lower().strip()
    for k, v in store_map.items():
        if k.lower().strip() == name_lower:
            return v
    if city and address:
        composite_lower = f"{name}|{city}|{address}".lower().strip()
        for k, v in store_map.items():
            if k.lower().strip() == composite_lower:
                return v
    return name


# ── Extract overview from JSON ──────────────────────────────────────────────

def extract_overview(data):
    ov = data.get("overview", {})
    return {
        "Total Sales": ov.get("total_sales", 0),
        "Net Sales": ov.get("net_sales", 0),
        "Commissions": ov.get("commissions", 0),
        "Commissions %": ov.get("commissions_pct", 0),
        "Other Adjustments": ov.get("other_adjustments", 0),
        "Net Payout": ov.get("net_payout", 0),
        "Net Payout %": ov.get("net_payout_pct", 0),
        "Marketing Driven Sales": ov.get("marketing_driven_sales", 0),
        "Organic Sales": ov.get("organic_sales", 0),
        "Total Orders": ov.get("total_orders", 0),
        "Orders from Marketing": ov.get("orders_from_marketing", 0),
        "Organic Orders": ov.get("organic_orders", 0),
        "AOV": ov.get("aov", 0),
        "Ad Spend": ov.get("ad_spend", 0),
        "Discounts (Offers)": ov.get("discounts", 0),
        "Total Marketing Investment": ov.get("total_marketing_investment", 0),
        "Marketing Credits": ov.get("marketing_credits", 0),
        "Marketing Spend / Sales %": ov.get("marketing_investment_pct", 0),
        "Marketing ROAS": ov.get("marketing_roas"),
        "Marketing CPO": ov.get("marketing_cpo"),
    }


def sum_overviews(overviews):
    combined = {}
    sum_keys = ["Total Sales", "Net Sales",
                "Commissions", "Ad Spend", "Other Adjustments",
                "Marketing Driven Sales", "Organic Sales",
                "Total Orders", "Orders from Marketing", "Organic Orders",
                "Discounts (Offers)", "Total Marketing Investment", "Marketing Credits",
                "Net Payout"]
    for k in sum_keys:
        combined[k] = sum(ov.get(k, 0) or 0 for ov in overviews)

    ts = combined["Total Sales"]
    to = combined["Total Orders"]
    tmi = combined["Total Marketing Investment"]
    om = combined["Orders from Marketing"]

    combined["AOV"] = ts / to if to > 0 else 0
    combined["Commissions %"] = (combined["Commissions"] / ts * 100) if ts > 0 else 0
    combined["Marketing Spend / Sales %"] = (tmi / ts * 100) if ts > 0 else 0
    combined["Marketing ROAS"] = (combined["Marketing Driven Sales"] / tmi) if tmi > 0 else None
    combined["Marketing CPO"] = (tmi / om) if om > 0 else None
    combined["Net Payout %"] = (combined["Net Payout"] / ts * 100) if ts > 0 else 0
    return combined


# ── Tracker CSV parsers ─────────────────────────────────────────────────────

def parse_platform_tracker(fp):
    """Parse Google Sheet Weekly Platform Overview CSV export.
    Returns: {week_num: {section: {metric: raw_string_value}}}
    """
    if not fp or not os.path.exists(fp):
        return {}
    with open(fp) as fh:
        rows = list(csv.reader(fh))

    # Find header row: "Platform,Week,43,44,..."
    week_row_idx = None
    for i, row in enumerate(rows):
        if len(row) > 2 and row[0].strip() == "Platform" and row[1].strip() == "Week":
            week_row_idx = i
            break
    if week_row_idx is None:
        print("WARNING: Could not find Platform/Week header in tracker platform CSV")
        return {}

    # Map column index → week number
    weeks = {}
    for j in range(2, len(rows[week_row_idx])):
        val = rows[week_row_idx][j].strip()
        if val and val.isdigit():
            weeks[j] = int(val)

    # Parse section/metric rows (skip header + date row)
    result = {}
    current_section = None
    for i in range(week_row_idx + 2, len(rows)):
        row = rows[i]
        if not row or len(row) < 3:
            continue
        section = row[0].strip()
        if section:
            current_section = section
        metric = row[1].strip() if len(row) > 1 else ""
        if not metric or not current_section:
            continue
        for j, wk_num in weeks.items():
            if j < len(row):
                val = row[j].strip()
                if val:
                    result.setdefault(wk_num, {}).setdefault(current_section, {})[metric] = val
    return result


def parse_location_tracker(fp):
    """Parse Google Sheet By Location CSV export.
    Returns: {week_num: {location: {metric: raw_string_value}}}
    """
    if not fp or not os.path.exists(fp):
        return {}
    with open(fp) as fh:
        rows = list(csv.reader(fh))

    # Find header row: ",Location,Week,43,44,..."
    week_row_idx = None
    for i, row in enumerate(rows):
        if len(row) > 3 and row[1].strip() == "Location" and row[2].strip() == "Week":
            week_row_idx = i
            break
    if week_row_idx is None:
        print("WARNING: Could not find Location/Week header in tracker location CSV")
        return {}

    # Map column index → week number
    weeks = {}
    for j in range(3, len(rows[week_row_idx])):
        val = rows[week_row_idx][j].strip()
        if val and val.isdigit():
            weeks[j] = int(val)

    # Parse location/metric rows
    result = {}
    current_location = None
    for i in range(week_row_idx + 2, len(rows)):
        row = rows[i]
        if not row or len(row) < 4:
            continue
        location = row[1].strip() if len(row) > 1 else ""
        if location:
            current_location = location
        metric = row[2].strip() if len(row) > 2 else ""
        if not metric or not current_location:
            continue
        for j, wk_num in weeks.items():
            if j < len(row):
                val = row[j].strip()
                if val:
                    result.setdefault(wk_num, {}).setdefault(current_location, {})[metric] = val
    return result


def prev_week_nums(current_week, count):
    """Get the previous N week numbers, wrapping from 1→52."""
    weeks = []
    wk = current_week
    for _ in range(count):
        wk = wk - 1 if wk > 1 else 52
        weeks.append(wk)
    return weeks


def compute_delta(current_val, compare_val):
    """Compute % change between current and comparison value."""
    if current_val is None or compare_val is None or compare_val == 0:
        return None
    return ((current_val - compare_val) / abs(compare_val)) * 100


def build_comparisons(current_data, tracker_history, current_week, entity_key="section"):
    """Build WoW and 4wk-avg comparison dicts.

    current_data: {entity: {metric: formatted_value}}  (our output)
    tracker_history: {week_num: {entity: {metric: raw_value}}}  (from tracker)
    current_week: int

    Returns: {entity: {metric: {"prev": str, "wow": str, "avg4": str, "vs4": str}}}
    """
    prev_wks = prev_week_nums(current_week, 1)
    trail_wks = prev_week_nums(current_week, 4)
    comparisons = {}

    for entity, metrics in current_data.items():
        comparisons[entity] = {}
        for metric, cur_formatted in metrics.items():
            cur_num = parse_val(cur_formatted)
            comp = {"prev": "--", "wow": "--", "avg4": "--", "vs4": "--"}

            # WoW: compare to previous week
            prev_wk = prev_wks[0]
            prev_val_raw = tracker_history.get(prev_wk, {}).get(entity, {}).get(metric)
            if prev_val_raw:
                prev_num = parse_val(prev_val_raw)
                comp["prev"] = prev_val_raw
                delta = compute_delta(cur_num, prev_num)
                comp["wow"] = fmt_delta(delta)

            # 4-week trailing average
            trail_vals = []
            for wk in trail_wks:
                v = tracker_history.get(wk, {}).get(entity, {}).get(metric)
                if v:
                    pv = parse_val(v)
                    if pv is not None:
                        trail_vals.append(pv)
            if trail_vals:
                avg = sum(trail_vals) / len(trail_vals)
                comp["avg4"] = fmt_metric(metric, avg)
                delta = compute_delta(cur_num, avg)
                comp["vs4"] = fmt_delta(delta)

            comparisons[entity][metric] = comp
    return comparisons


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", required=True, help="Directory containing *_results.json files")
    p.add_argument("--store-map", help="JSON file mapping platform store names to canonical names")
    p.add_argument("--tracker-platform-csv", help="Google Sheet Weekly Platform Overview CSV export")
    p.add_argument("--tracker-location-csv", help="Google Sheet By Location CSV export")
    p.add_argument("--current-week", type=int, help="Current week number (for WoW + 4wk avg)")
    p.add_argument("--prev-tracker", help="(Legacy) Prior week tracker CSV for WoW comparison")
    a = p.parse_args()

    outdir = a.output_dir

    # Prefer validated location_map.json (from validate_locations.py), fall back to --store-map
    validated_map = os.path.join(outdir, "location_map.json")
    if os.path.exists(validated_map):
        store_map = load_store_map(validated_map)
        print(f"Using validated location map: {validated_map} ({len(store_map)} entries)")
    else:
        store_map = load_store_map(a.store_map)
        if store_map:
            print(f"Using --store-map: {a.store_map}")
        else:
            print("WARNING: No store map provided. Location names will be used as-is.")

    json_files = glob.glob(os.path.join(outdir, "*_results.json"))
    if not json_files:
        print(f"ERROR: No *_results.json files found in {outdir}")
        sys.exit(1)

    platforms = {}
    all_locations = {}
    all_campaigns = []

    for jf in json_files:
        with open(jf) as fh:
            data = json.load(fh)
        plat = data["platform"]
        label = PLATFORM_LABELS.get(plat, plat.upper())
        platforms[label] = extract_overview(data)

        # Locations
        for loc_data in data.get("by_location", []):
            raw_name = loc_data.get("location") or loc_data.get("store_name") or loc_data.get("name", "Unknown")
            loc_city = loc_data.get("city")
            loc_addr = loc_data.get("street_address")
            loc_name = normalize_store_name(raw_name, store_map, city=loc_city, address=loc_addr)
            loc_metrics = {
                "Total Sales": loc_data.get("total_sales", 0),
                "Net Sales": loc_data.get("net_sales", 0),
                "Commissions": loc_data.get("commissions", 0),
                "Commissions %": loc_data.get("commissions_pct", 0),
                "Other Adjustments": loc_data.get("other_adjustments", 0),
                "Net Payout": loc_data.get("net_payout", 0),
                "Net Payout %": loc_data.get("net_payout_pct", 0),
                "Marketing Driven Sales": loc_data.get("marketing_driven_sales", 0),
                "Organic Sales": loc_data.get("organic_sales", 0),
                "Total Orders": loc_data.get("total_orders", 0),
                "Orders from Marketing": loc_data.get("orders_from_marketing", 0),
                "Organic Orders": loc_data.get("organic_orders", 0),
                "AOV": loc_data.get("aov", 0),
                "Ad Spend": loc_data.get("ad_spend", 0),
                "Discounts (Offers)": loc_data.get("discounts", 0),
                "Total Marketing Investment": loc_data.get("total_marketing_investment", 0),
                "Marketing Credits": loc_data.get("marketing_credits", 0),
                "Marketing Spend / Sales %": loc_data.get("marketing_investment_pct", 0),
                "Marketing ROAS": loc_data.get("marketing_roas"),
                "Marketing CPO": loc_data.get("marketing_cpo"),
            }
            if loc_name in all_locations:
                existing = all_locations[loc_name]
                for k in ["Total Sales", "Net Sales",
                          "Commissions", "Ad Spend", "Other Adjustments",
                          "Marketing Driven Sales", "Organic Sales",
                          "Total Orders", "Orders from Marketing", "Organic Orders",
                          "Discounts (Offers)", "Total Marketing Investment",
                          "Marketing Credits", "Net Payout"]:
                    existing[k] = (existing.get(k, 0) or 0) + (loc_metrics.get(k, 0) or 0)
                ts = existing["Total Sales"]
                to = existing["Total Orders"]
                mds = existing["Marketing Driven Sales"]
                om = existing["Orders from Marketing"]
                if mds > ts:
                    existing["Marketing Driven Sales"] = ts
                    mds = ts
                if om > to:
                    existing["Orders from Marketing"] = to
                    om = to
                existing["Organic Sales"] = ts - existing["Marketing Driven Sales"]
                existing["Organic Orders"] = to - existing["Orders from Marketing"]
                tmi = existing["Total Marketing Investment"]
                existing["AOV"] = ts / to if to > 0 else 0
                existing["Commissions %"] = (existing["Commissions"] / ts * 100) if ts > 0 else 0
                existing["Marketing Spend / Sales %"] = (tmi / ts * 100) if ts > 0 else 0
                existing["Marketing ROAS"] = (existing["Marketing Driven Sales"] / tmi) if tmi > 0 else None
                existing["Marketing CPO"] = (tmi / om) if om > 0 else None
                existing["Net Payout %"] = (existing["Net Payout"] / ts * 100) if ts > 0 else 0
            else:
                ts = loc_metrics["Total Sales"]
                to = loc_metrics["Total Orders"]
                mds = loc_metrics.get("Marketing Driven Sales", 0) or 0
                om = loc_metrics.get("Orders from Marketing", 0) or 0
                if mds > ts:
                    loc_metrics["Marketing Driven Sales"] = ts
                    loc_metrics["Organic Sales"] = 0
                if om > to:
                    loc_metrics["Orders from Marketing"] = to
                    loc_metrics["Organic Orders"] = 0
                all_locations[loc_name] = loc_metrics

        # Campaigns
        for camp in data.get("campaigns", []):
            def safe_float(v):
                if v is None: return None
                try: return float(v)
                except (ValueError, TypeError): return None
            all_campaigns.append({
                "Platform": label,
                "Campaign Type": camp.get("campaign_type", ""),
                "Location": camp.get("location") or camp.get("store_name", "All"),
                "Spend": fmt_currency(safe_float(camp.get("spend"))) if camp.get("spend") is not None else "--*",
                "Sales": fmt_currency(safe_float(camp.get("sales"))) if camp.get("sales") is not None else "--",
                "Orders": fmt_int(int(safe_float(camp.get("orders")) or 0)) if camp.get("orders") is not None else "--",
                "ROAS": fmt_roas(safe_float(camp.get("roas"))) if camp.get("roas") is not None else "--",
            })

    # Combined overview
    combined = sum_overviews(list(platforms.values()))

    # ── Build formatted dicts for comparison ────────────────────────────────
    # Platform overview: {section: {metric: formatted_value}}
    fmt_platform = {}
    for section_name, section_data in [("OVERVIEW", combined)] + list(platforms.items()):
        fmt_platform[section_name] = {}
        for m in OVERVIEW_METRICS:
            fmt_platform[section_name][m] = fmt_metric(m, section_data.get(m))

    # Location: {location: {metric: formatted_value}}
    fmt_location = {}
    for loc_name, loc_data in all_locations.items():
        fmt_location[loc_name] = {}
        for m in LOC_METRICS:
            fmt_location[loc_name][m] = fmt_metric(m, loc_data.get(m))

    # ── Compute comparisons if tracker data provided ────────────────────────
    plat_comp = {}  # {section: {metric: {prev, wow, avg4, vs4}}}
    loc_comp = {}   # {location: {metric: {prev, wow, avg4, vs4}}}
    has_comparisons = False

    if a.tracker_platform_csv and a.current_week:
        plat_history = parse_platform_tracker(a.tracker_platform_csv)
        if plat_history:
            plat_comp = build_comparisons(fmt_platform, plat_history, a.current_week)
            has_comparisons = True
            print(f"Loaded platform tracker: {len(plat_history)} weeks of history")

    if a.tracker_location_csv and a.current_week:
        loc_history = parse_location_tracker(a.tracker_location_csv)
        if loc_history:
            loc_comp = build_comparisons(fmt_location, loc_history, a.current_week)
            has_comparisons = True
            print(f"Loaded location tracker: {len(loc_history)} weeks of history")

    # ── Write platform_overview.csv ─────────────────────────────────────────
    ov_path = os.path.join(outdir, "platform_overview.csv")
    with open(ov_path, "w", newline="") as fh:
        w = csv.writer(fh)
        if has_comparisons:
            w.writerow(["Section", "Metric", "Value", "PrevWeek", "WoW", "Avg4Wk", "vs4Wk"])
        else:
            w.writerow(["Section", "Metric", "Value"])
        for section_name in ["OVERVIEW"] + [k for k in platforms.keys()]:
            for m in OVERVIEW_METRICS:
                v = fmt_platform[section_name][m]
                if has_comparisons:
                    c = plat_comp.get(section_name, {}).get(m, {})
                    w.writerow([section_name, m, v, c.get("prev","--"), c.get("wow","--"),
                                c.get("avg4","--"), c.get("vs4","--")])
                else:
                    w.writerow([section_name, m, v])
    print(f"Wrote {ov_path}")

    # ── Write by_location.csv ───────────────────────────────────────────────
    loc_path = os.path.join(outdir, "by_location.csv")
    with open(loc_path, "w", newline="") as fh:
        w = csv.writer(fh)
        if has_comparisons:
            w.writerow(["Location", "Metric", "Value", "PrevWeek", "WoW", "Avg4Wk", "vs4Wk"])
        else:
            w.writerow(["Location", "Metric", "Value"])
        for loc_name in sorted(all_locations.keys(), key=lambda l: all_locations[l].get("Total Sales", 0), reverse=True):
            for m in LOC_METRICS:
                v = fmt_location[loc_name][m]
                if has_comparisons:
                    c = loc_comp.get(loc_name, {}).get(m, {})
                    w.writerow([loc_name, m, v, c.get("prev","--"), c.get("wow","--"),
                                c.get("avg4","--"), c.get("vs4","--")])
                else:
                    w.writerow([loc_name, m, v])
    print(f"Wrote {loc_path}")

    # ── Write campaign_performance.csv ──────────────────────────────────────
    camp_path = os.path.join(outdir, "campaign_performance.csv")
    with open(camp_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["Platform", "Campaign Type", "Location", "Spend", "Sales", "Orders", "ROAS"])
        w.writeheader()
        w.writerows(all_campaigns)
    print(f"Wrote {camp_path}")

    # ── Write tracker_update.csv (paste-ready column) ───────────────────────
    tracker_path = os.path.join(outdir, "tracker_update.csv")
    with open(tracker_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Section", "Metric", "Value"])
        for section_name, section_data in platforms.items():
            for m in TRACKER_METRICS:
                v = section_data.get(m)
                w.writerow([section_name, m, fmt_metric(m, v)])
        for loc_name in sorted(all_locations.keys(), key=lambda l: all_locations[l].get("Total Sales", 0), reverse=True):
            for m in TRACKER_METRICS:
                v = all_locations[loc_name].get(m)
                w.writerow([loc_name, m, fmt_metric(m, v)])
    print(f"Wrote {tracker_path}")

    print(f"\nAggregation complete. {len(platforms)} platforms, {len(all_locations)} locations, {len(all_campaigns)} campaigns.")
    if has_comparisons:
        prev_wks = prev_week_nums(a.current_week, 4)
        print(f"Comparisons: WoW vs week {prev_wks[0]}, 4wk avg of weeks {prev_wks}")


if __name__ == "__main__":
    main()
