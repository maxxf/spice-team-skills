#!/usr/bin/env python3
"""validate_report.py — Hard validation gate for weekly reporting.

Runs AFTER extraction agents produce *_results.json and BEFORE Notion generation.
Validates formula integrity per platform, cross-checks location sums, and catches
the class of errors where net_sales ≠ total_sales - discounts, payout % uses wrong
denominator, etc.

Exit code 0 = all critical checks pass. Proceed to Notion.
Exit code 1 = at least one critical check failed. HALT.

Usage:
    python validate_report.py --output-dir OUTPUT [--profile-json PROFILE.json]

Reads:
    OUTPUT/*_results.json (platform extraction outputs)
    PROFILE.json (optional — client KPI ranges for soft checks)

Produces:
    OUTPUT/validation_report.json (machine-readable results)
    OUTPUT/validation_report.md  (human-readable for Notion/Slack paste)
"""
import argparse, glob, json, os, sys
from datetime import datetime

# ── Metric keys from output-schema.json ─────────────────────────────────────
# These are the raw JSON field names (snake_case), not display names.
FINANCIAL_WATERFALL = [
    "total_sales", "net_sales", "commissions", "commissions_pct",
    "other_adjustments", "net_payout", "net_payout_pct"
]
MARKETING_ATTRIBUTION = [
    "marketing_driven_sales", "organic_sales", "total_orders",
    "orders_from_marketing", "organic_orders", "aov", "ad_spend",
    "discounts", "total_marketing_investment", "marketing_credits",
    "marketing_investment_pct", "marketing_roas", "marketing_cpo"
]
ALL_METRICS = FINANCIAL_WATERFALL + MARKETING_ATTRIBUTION

# ── Tolerance constants ─────────────────────────────────────────────────────
CURRENCY_TOLERANCE = 1.0     # ±$1 for additive checks
PAYOUT_TOLERANCE = 2.0       # ±$2 for net payout (more components)
LOCATION_SUM_TOLERANCE = 2.0 # ±$2 for location → overview sum
PCT_TOLERANCE = 0.5          # ±0.5 percentage points
PAYOUT_RECONCILE_PCT = 2.0   # Flag if calc vs column differs > 2%
PAYOUT_PCT_RANGE = (50, 85)  # Soft flag outside this range


def load_platform_jsons(output_dir):
    """Load all *_results.json files from the output directory."""
    pattern = os.path.join(output_dir, "*_results.json")
    files = glob.glob(pattern)
    if not files:
        return None, "No *_results.json files found in output directory"

    platforms = {}
    for fpath in files:
        with open(fpath) as f:
            data = json.load(f)
        platform = data.get("platform", os.path.basename(fpath).replace("_results.json", ""))
        platforms[platform] = data
    return platforms, None


def safe_get(metrics, key, default=0):
    """Get a metric value, treating None as 0."""
    v = metrics.get(key)
    return v if v is not None else default


def check_close(actual, expected, tolerance, label):
    """Check if actual ≈ expected within tolerance. Returns (pass, message)."""
    diff = abs(actual - expected)
    if diff <= tolerance:
        return True, None
    return False, f"{label}: expected {expected:.2f}, got {actual:.2f} (diff: {diff:.2f}, tolerance: ±{tolerance})"


def validate_metrics(metrics, label_prefix):
    """Validate formula integrity for a single metrics block (overview or location).

    Returns (critical_failures, soft_warnings).
    """
    critical = []
    warnings = []

    ts = safe_get(metrics, "total_sales")
    ns = safe_get(metrics, "net_sales")
    disc = safe_get(metrics, "discounts")
    comm = safe_get(metrics, "commissions")
    comm_pct = safe_get(metrics, "commissions_pct")
    other = safe_get(metrics, "other_adjustments")
    ad = safe_get(metrics, "ad_spend")
    np_ = safe_get(metrics, "net_payout")
    np_pct = safe_get(metrics, "net_payout_pct")
    mds = safe_get(metrics, "marketing_driven_sales")
    os_ = safe_get(metrics, "organic_sales")
    to = safe_get(metrics, "total_orders")
    om = safe_get(metrics, "orders_from_marketing")
    oo = safe_get(metrics, "organic_orders")
    tmi = safe_get(metrics, "total_marketing_investment")
    mip = safe_get(metrics, "marketing_investment_pct")

    # ── Critical checks ─────────────────────────────────────────────────

    # 1. Net Sales = Total Sales - Discounts
    expected_ns = ts - disc
    ok, msg = check_close(ns, expected_ns, CURRENCY_TOLERANCE,
                          f"{label_prefix} Net Sales = Total Sales - Discounts")
    if not ok:
        critical.append(msg)

    # 2. Marketing Driven Sales + Organic Sales = Total Sales
    expected_ts = mds + os_
    ok, msg = check_close(ts, expected_ts, CURRENCY_TOLERANCE,
                          f"{label_prefix} Marketing + Organic = Total Sales")
    if not ok:
        critical.append(msg)

    # 3. Orders from Marketing + Organic Orders = Total Orders
    expected_to = om + oo
    if to != expected_to:
        critical.append(
            f"{label_prefix} Marketing Orders + Organic Orders = Total Orders: "
            f"expected {expected_to}, got {to}"
        )

    # 4. Net Payout = Net Sales - Commissions - Ad Spend - Other Adjustments
    expected_np = ns - comm - ad - other
    ok, msg = check_close(np_, expected_np, PAYOUT_TOLERANCE,
                          f"{label_prefix} Net Payout = NS - Comm - Ad - Other")
    if not ok:
        critical.append(msg)

    # 5. Net Payout % = Net Payout / Total Sales * 100
    if ts > 0:
        expected_np_pct = (np_ / ts) * 100
        ok, msg = check_close(np_pct, expected_np_pct, PCT_TOLERANCE,
                              f"{label_prefix} Net Payout % = Net Payout / Total Sales")
        if not ok:
            critical.append(msg)

    # 6. Commissions % = Commissions / Total Sales * 100
    if ts > 0:
        expected_comm_pct = (comm / ts) * 100
        ok, msg = check_close(comm_pct, expected_comm_pct, PCT_TOLERANCE,
                              f"{label_prefix} Commissions % = Comm / Total Sales")
        if not ok:
            critical.append(msg)

    # 7. Total Marketing Investment = Ad Spend + Discounts
    expected_tmi = ad + disc
    ok, msg = check_close(tmi, expected_tmi, CURRENCY_TOLERANCE,
                          f"{label_prefix} TMI = Ad Spend + Discounts")
    if not ok:
        critical.append(msg)

    # 8. Marketing Spend / Sales % = TMI / Total Sales * 100
    if ts > 0 and tmi > 0:
        expected_mip = (tmi / ts) * 100
        ok, msg = check_close(mip, expected_mip, PCT_TOLERANCE,
                              f"{label_prefix} Mkt Spend % = TMI / Total Sales")
        if not ok:
            critical.append(msg)

    # ── Sign checks ─────────────────────────────────────────────────────
    # Commissions, ad_spend, discounts, other_adjustments should be >= 0
    # (stored as absolute values per schema)
    for field in ["commissions", "ad_spend", "discounts"]:
        v = safe_get(metrics, field)
        if v < 0:
            critical.append(f"{label_prefix} {field} is negative ({v:.2f}) — expected absolute value")

    # ── Soft checks ─────────────────────────────────────────────────────

    # Payout % range
    if ts > 0 and (np_pct < PAYOUT_PCT_RANGE[0] or np_pct > PAYOUT_PCT_RANGE[1]):
        warnings.append(
            f"{label_prefix} Net Payout % = {np_pct:.1f}% — outside expected "
            f"{PAYOUT_PCT_RANGE[0]}-{PAYOUT_PCT_RANGE[1]}% range"
        )

    # Payout reconciliation (if platform payout column available)
    plat_payout = metrics.get("platform_payout_column")
    plat_tax = metrics.get("platform_tax_passed", 0)
    if plat_payout is not None and ts > 0:
        adjusted_plat = plat_payout - (plat_tax if plat_tax else 0)
        if adjusted_plat > 0:
            recon_diff_pct = abs(np_ - adjusted_plat) / adjusted_plat * 100
            if recon_diff_pct > PAYOUT_RECONCILE_PCT:
                warnings.append(
                    f"{label_prefix} Payout reconciliation: calculated ${np_:,.0f} vs "
                    f"platform-minus-tax ${adjusted_plat:,.0f} — diff {recon_diff_pct:.1f}% "
                    f"(threshold: {PAYOUT_RECONCILE_PCT}%)"
                )

    return critical, warnings


def validate_location_sums(platform_data, label):
    """Check that sum of location metrics ≈ overview metrics."""
    critical = []
    overview = platform_data.get("overview", {})
    locations = platform_data.get("by_location", [])

    if not locations:
        return critical  # No locations to check

    # Additive metrics that should sum from locations to overview
    additive_metrics = [
        "total_sales", "net_sales", "commissions", "other_adjustments",
        "net_payout", "marketing_driven_sales", "organic_sales",
        "total_orders", "orders_from_marketing", "organic_orders",
        "ad_spend", "discounts", "total_marketing_investment", "marketing_credits"
    ]

    for metric in additive_metrics:
        overview_val = safe_get(overview, metric)
        loc_sum = sum(safe_get(loc, metric) for loc in locations)
        ok, msg = check_close(
            loc_sum, overview_val, LOCATION_SUM_TOLERANCE,
            f"{label} location sum vs overview [{metric}]"
        )
        if not ok:
            critical.append(msg)

    return critical


def validate_metric_completeness(platform_data, label):
    """Check that all 20 metrics are present in the overview."""
    warnings = []
    overview = platform_data.get("overview", {})

    missing = [m for m in ALL_METRICS if m not in overview]
    if missing:
        warnings.append(f"{label} overview missing metrics: {', '.join(missing)}")

    return warnings


def validate_extraction_flags(platform_data, label):
    """Surface any validation flags the extraction agent itself reported."""
    warnings = []
    validation = platform_data.get("validation", {})

    if validation.get("sales_check") is False:
        warnings.append(f"{label} extraction agent FAILED its own sales_check")
    if validation.get("orders_check") is False:
        warnings.append(f"{label} extraction agent FAILED its own orders_check")

    flags = validation.get("flags", [])
    for flag in flags:
        warnings.append(f"{label} extraction flag: {flag}")

    return warnings


def load_profile(profile_path):
    """Load optional client profile with KPI targets."""
    if not profile_path or not os.path.exists(profile_path):
        return None
    with open(profile_path) as f:
        return json.load(f)


def check_kpi_targets(platforms, profile):
    """Soft-check overview metrics against KPI targets from profile."""
    warnings = []
    if not profile or "kpi_targets" not in profile:
        return warnings

    targets = profile["kpi_targets"]

    # Aggregate overview across all platforms for KPI comparison
    total_np_pct = None
    total_mkt_pct = None
    total_aov = None

    total_np = sum(safe_get(p.get("overview", {}), "net_payout") for p in platforms.values())
    total_ts = sum(safe_get(p.get("overview", {}), "total_sales") for p in platforms.values())
    total_tmi = sum(safe_get(p.get("overview", {}), "total_marketing_investment") for p in platforms.values())
    total_orders = sum(safe_get(p.get("overview", {}), "total_orders") for p in platforms.values())

    if total_ts > 0:
        total_np_pct = (total_np / total_ts) * 100
        total_mkt_pct = (total_tmi / total_ts) * 100
    if total_orders > 0:
        total_aov = total_ts / total_orders

    # Check ranges
    if "net_payout_pct" in targets and total_np_pct is not None:
        lo, hi = targets["net_payout_pct"]
        if total_np_pct < lo or total_np_pct > hi:
            warnings.append(
                f"KPI: Aggregate Net Payout % = {total_np_pct:.1f}% "
                f"(target: {lo}-{hi}%)"
            )

    if "marketing_pct" in targets and total_mkt_pct is not None:
        lo, hi = targets["marketing_pct"]
        if total_mkt_pct < lo or total_mkt_pct > hi:
            warnings.append(
                f"KPI: Aggregate Marketing Spend % = {total_mkt_pct:.1f}% "
                f"(target: {lo}-{hi}%)"
            )

    if "aov" in targets and total_aov is not None:
        lo, hi = targets["aov"]
        if total_aov < lo or total_aov > hi:
            warnings.append(
                f"KPI: Aggregate AOV = ${total_aov:.2f} "
                f"(target: ${lo:.2f}-${hi:.2f})"
            )

    return warnings


def generate_report_md(all_critical, all_warnings, platforms_checked):
    """Generate human-readable validation report."""
    lines = []
    passed = len(all_critical) == 0

    lines.append("# Validation Report")
    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Platforms checked:** {', '.join(platforms_checked)}")
    lines.append(f"**Result:** {'✅ ALL CHECKS PASSED' if passed else '❌ CRITICAL FAILURES DETECTED'}")
    lines.append("")

    if all_critical:
        lines.append("## ❌ Critical Failures (BLOCKING)")
        lines.append("")
        for i, msg in enumerate(all_critical, 1):
            lines.append(f"{i}. {msg}")
        lines.append("")

    if all_warnings:
        lines.append("## ⚠️ Warnings (non-blocking)")
        lines.append("")
        for i, msg in enumerate(all_warnings, 1):
            lines.append(f"{i}. {msg}")
        lines.append("")

    if passed and not all_warnings:
        lines.append("All formula checks, location sums, and metric completeness verified. No issues found.")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Validate weekly reporting extraction output")
    parser.add_argument("--output-dir", required=True, help="Directory containing *_results.json")
    parser.add_argument("--profile-json", default=None, help="Optional client profile with KPI targets")
    args = parser.parse_args()

    # Load platform JSONs
    platforms, err = load_platform_jsons(args.output_dir)
    if err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    # Load optional profile
    profile = load_profile(args.profile_json)

    all_critical = []
    all_warnings = []
    platforms_checked = []

    for platform_name, data in sorted(platforms.items()):
        platforms_checked.append(platform_name)
        label = platform_name.upper().replace("_", " ")

        # 1. Validate overview formula integrity
        overview = data.get("overview", {})
        crit, warn = validate_metrics(overview, f"[{label}]")
        all_critical.extend(crit)
        all_warnings.extend(warn)

        # 2. Validate each location's formula integrity
        for loc_data in data.get("by_location", []):
            loc_name = loc_data.get("location", "UNKNOWN")
            crit, warn = validate_metrics(loc_data, f"[{label} / {loc_name}]")
            all_critical.extend(crit)
            all_warnings.extend(warn)

        # 3. Check location sums match overview
        crit = validate_location_sums(data, f"[{label}]")
        all_critical.extend(crit)

        # 4. Check metric completeness
        warn = validate_metric_completeness(data, f"[{label}]")
        all_warnings.extend(warn)

        # 5. Surface extraction agent's own flags
        warn = validate_extraction_flags(data, f"[{label}]")
        all_warnings.extend(warn)

    # 6. KPI target checks (soft)
    if profile:
        kpi_warn = check_kpi_targets(platforms, profile)
        all_warnings.extend(kpi_warn)

    # ── Output ──────────────────────────────────────────────────────────

    passed = len(all_critical) == 0

    # JSON report
    report_json = {
        "timestamp": datetime.now().isoformat(),
        "platforms_checked": platforms_checked,
        "passed": passed,
        "critical_failures": all_critical,
        "warnings": all_warnings,
        "checks_run": {
            "formula_integrity": True,
            "location_sums": True,
            "metric_completeness": True,
            "extraction_flags": True,
            "kpi_targets": profile is not None
        }
    }

    json_path = os.path.join(args.output_dir, "validation_report.json")
    with open(json_path, "w") as f:
        json.dump(report_json, f, indent=2)

    # Markdown report
    md_content = generate_report_md(all_critical, all_warnings, platforms_checked)
    md_path = os.path.join(args.output_dir, "validation_report.md")
    with open(md_path, "w") as f:
        f.write(md_content)

    # Stdout summary
    print(f"\n{'='*60}")
    print(f"VALIDATION {'PASSED ✅' if passed else 'FAILED ❌'}")
    print(f"{'='*60}")
    print(f"Platforms: {', '.join(platforms_checked)}")
    print(f"Critical failures: {len(all_critical)}")
    print(f"Warnings: {len(all_warnings)}")

    if all_critical:
        print(f"\n--- CRITICAL FAILURES ---")
        for msg in all_critical:
            print(f"  ✗ {msg}")

    if all_warnings:
        print(f"\n--- WARNINGS ---")
        for msg in all_warnings:
            print(f"  ⚠ {msg}")

    print(f"\nReports written to:")
    print(f"  {json_path}")
    print(f"  {md_path}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
