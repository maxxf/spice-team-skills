#!/usr/bin/env python3
"""generate_notion_update.py - Generate Notion weekly update markdown.

Usage: python generate_notion_update.py --overview out/platform_overview.csv \
    --by-location out/by_location.csv --campaign-perf out/campaign_performance.csv \
    --client ClientName --week "Mon DD-DD" --output out/notion_update.md

Optional: --agenda-context FILE --action-items FILE --ops-quality FILE

Updated April 2026: 17-metric structure (Financial Waterfall + Marketing Attribution).
Removed Gross Sales. Added Commissions, Net Sales, Other Adjustments.
"""
import argparse, csv, json, os, sys

def load_sections(fp, key_col):
    """Load CSV into {key: {metric: {value, prev, wow, avg4, vs4}}} or {key: {metric: value}}."""
    data = {}
    if not fp or not os.path.exists(fp): return data, False
    has_comp = False
    with open(fp) as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        has_comp = "WoW" in fields
        for r in reader:
            key = r[key_col]
            if has_comp:
                data.setdefault(key, {})[r["Metric"]] = {
                    "value": r.get("Value", "0"),
                    "prev": r.get("PrevWeek", "--"),
                    "wow": r.get("WoW", "--"),
                    "avg4": r.get("Avg4Wk", "--"),
                    "vs4": r.get("vs4Wk", "--"),
                }
            else:
                data.setdefault(key, {})[r["Metric"]] = {"value": r.get("Value", "0")}
    return data, has_comp

def gv(d, metric, field="value"):
    """Get a value from the loaded data structure."""
    entry = d.get(metric, {})
    if isinstance(entry, dict):
        return entry.get(field, "--")
    return entry

def pv(v):
    """Parse a formatted value to float."""
    if not v or v in ("0", "--", "--*"): return 0
    try: return float(str(v).replace("%","").replace("x","").replace("$","").replace(",",""))
    except: return 0

def gen_flags(ov, loc):
    flags = []
    for s, d in ov.items():
        if s == "OVERVIEW": continue
        r = pv(gv(d, "Marketing ROAS"))
        tmi = pv(gv(d, "Total Marketing Investment"))
        ts = pv(gv(d, "Total Sales"))
        spend_pct = (tmi / ts * 100) if ts > 0 else 0
        if r > 0 and r < 2: flags.append(f"LOW ROAS: {s} = {r:.1f} (below 2.0)")
        if spend_pct > 20: flags.append(f"HIGH SPEND: {s} = {spend_pct:.0f}% of sales")
    for l, d in loc.items():
        pp = pv(gv(d, "Net Payout %"))
        if pp > 100: flags.append(f"PAYOUT >100%: {l} = {pp:.0f}%")
        if 0 < pp < 40: flags.append(f"LOW PAYOUT: {l} = {pp:.0f}%")
    return flags

def load_text_file(fp):
    if not fp or not os.path.exists(fp): return ""
    with open(fp) as fh: return fh.read().strip()

def generate_highlights_data(ov, loc, flags, has_comp):
    """Generate raw data block for Claude to rewrite as strategist briefing."""
    overview = ov.get("OVERVIEW", {})
    lines = []
    lines.append("<!-- KEY_HIGHLIGHTS_DATA: Claude should replace this entire block with 3-5 strategist bullets.")
    lines.append("Each bullet: metric + context + recommendation. Write like a strategist, not a dashboard.")
    lines.append("")
    lines.append("RAW DATA:")

    metrics = ["Total Sales","Net Sales","Total Orders","AOV","Total Marketing Investment","Marketing ROAS",
               "Net Payout","Net Payout %","Commissions","Commissions %",
               "Marketing Driven Sales","Organic Sales"]
    for m in metrics:
        v = gv(overview, m)
        if has_comp:
            wow = gv(overview, m, "wow")
            vs4 = gv(overview, m, "vs4")
            lines.append(f"  OVERVIEW | {m}: {v} (WoW: {wow}, vs 4wk avg: {vs4})")
        else:
            lines.append(f"  OVERVIEW | {m}: {v}")

    for sec in ["UBER EATS", "DOORDASH", "GRUBHUB"]:
        d = ov.get(sec, {})
        if not d or pv(gv(d, "Total Sales")) == 0: continue
        lines.append(f"  ---")
        for m in ["Total Sales","Total Orders","Marketing ROAS",
                   "Net Payout %","Commissions %"]:
            v = gv(d, m)
            if has_comp:
                wow = gv(d, m, "wow")
                vs4 = gv(d, m, "vs4")
                lines.append(f"  {sec} | {m}: {v} (WoW: {wow}, vs 4wk avg: {vs4})")
            else:
                lines.append(f"  {sec} | {m}: {v}")

    lines.append(f"  ---")
    lines.append(f"  LOCATION OUTLIERS:")
    for ln in sorted(loc.keys()):
        d = loc[ln]
        sales = gv(d, "Total Sales")
        roas = gv(d, "Marketing ROAS")
        pp = gv(d, "Net Payout %")
        if has_comp:
            sales_vs4 = gv(d, "Total Sales", "vs4")
            roas_wow = gv(d, "Marketing ROAS", "wow")
            lines.append(f"  {ln}: Sales={sales} (vs4wk:{sales_vs4}), ROAS={roas} (WoW:{roas_wow}), Payout%={pp}")
        else:
            lines.append(f"  {ln}: Sales={sales}, ROAS={roas}, Payout%={pp}")

    if flags:
        lines.append(f"  ---")
        lines.append(f"  FLAGS: {' | '.join(flags)}")

    lines.append("-->")
    lines.append("")
    lines.append("*[Claude: replace this section with 3-5 strategist bullets using the data above]*")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--overview", required=True)
    p.add_argument("--by-location", required=True)
    p.add_argument("--campaign-perf")
    p.add_argument("--client", default="Client")
    p.add_argument("--week", default="Week")
    p.add_argument("--output", required=True)
    p.add_argument("--agenda-context")
    p.add_argument("--action-items")
    p.add_argument("--ops-quality")
    p.add_argument("--validation-report", help="Path to validation_report.md from validate_report.py")
    a = p.parse_args()

    ov, has_comp = load_sections(a.overview, "Section")
    loc, _ = load_sections(a.by_location, "Location")

    camps = []
    if a.campaign_perf and os.path.exists(a.campaign_perf):
        with open(a.campaign_perf) as fh: camps = list(csv.DictReader(fh))

    flags = gen_flags(ov, loc)
    agenda_ctx = load_text_file(a.agenda_context)
    action_items = load_text_file(a.action_items)
    ops_quality = load_text_file(a.ops_quality)

    lines = []
    L = lines.append

    L(f"# {a.client} Weekly Update - {a.week}")
    L("")

    # --- Agenda ---
    L("## Agenda")
    L("")
    L(agenda_ctx if agenda_ctx else "*No previous meeting context available.*")
    L("")

    # --- Action Items ---
    L("## Action Items")
    L("")
    if action_items:
        L(action_items)
    else:
        L("### Carried Over")
        L("- [ ] *No open items from previous meetings*")
        L("")
        L("### New This Week")
        L("- [ ] ")
    L("")

    # --- Key Highlights ---
    L("## Key Highlights")
    L("")
    L(generate_highlights_data(ov, loc, flags, has_comp))
    L("")

    # --- Platform Performance ---
    L("## Platform Performance")
    L("")

    # Financial Waterfall (7) + Marketing Attribution (13) = 20 metrics
    platform_metrics = [
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

    for sec in ["OVERVIEW","UBER EATS","DOORDASH","GRUBHUB"]:
        d = ov.get(sec, {})
        if not d: continue
        if sec != "OVERVIEW" and pv(gv(d, "Total Sales")) == 0: continue
        L(f"### {sec}")
        if has_comp:
            L("| Metric | Value | WoW | vs 4wk Avg |")
            L("|--------|-------|-----|------------|")
            for m in platform_metrics:
                v = gv(d, m)
                wow = gv(d, m, "wow")
                vs4 = gv(d, m, "vs4")
                L(f"| {m} | {v} | {wow} | {vs4} |")
        else:
            L("| Metric | Value |")
            L("|--------|-------|")
            for m in platform_metrics:
                L(f"| {m} | {gv(d, m)} |")
        L("")

    # --- Location Performance ---
    L("## Location Performance")
    L("")
    loc_summary_metrics = ["Total Sales", "Net Sales", "Total Orders", "AOV",
                           "Commissions %", "Ad Spend", "Discounts (Offers)",
                           "Total Marketing Investment",
                           "Marketing ROAS", "Net Payout", "Net Payout %"]

    if has_comp:
        header = "| Location | " + " | ".join(loc_summary_metrics) + " | Sales WoW | Sales vs 4wk |"
        sep = "|" + "|".join(["---"]*(len(loc_summary_metrics)+3)) + "|"
        L(header); L(sep)
        for ln in sorted(loc.keys(), key=lambda l: pv(gv(loc[l], "Total Sales")), reverse=True):
            d = loc[ln]
            vals = [gv(d, m) for m in loc_summary_metrics]
            wow = gv(d, "Total Sales", "wow")
            vs4 = gv(d, "Total Sales", "vs4")
            L(f"| {ln} | " + " | ".join(vals) + f" | {wow} | {vs4} |")
    else:
        header = "| Location | " + " | ".join(loc_summary_metrics) + " |"
        sep = "|" + "|".join(["---"]*(len(loc_summary_metrics)+1)) + "|"
        L(header); L(sep)
        for ln in sorted(loc.keys(), key=lambda l: pv(gv(loc[l], "Total Sales")), reverse=True):
            d = loc[ln]
            vals = [gv(d, m) for m in loc_summary_metrics]
            L(f"| {ln} | " + " | ".join(vals) + " |")
    L("")

    # --- Operations & Quality ---
    L("## Operations & Quality")
    L("")
    if flags:
        L("### Performance Flags")
        for flag in flags: L(f"- {flag}")
        L("")
    if ops_quality:
        L(ops_quality)
    elif not flags:
        L("No flags or ops issues this week.")
    L("")

    # --- Campaign Performance ---
    L("## Campaign Performance")
    L("")
    if camps:
        L("| Platform | Type | Location | Spend | Sales | Orders | ROAS |")
        L("|----------|------|----------|-------|-------|--------|------|")
        for c in camps:
            L(f"| {c['Platform']} | {c['Campaign Type']} | {c['Location']} | {c['Spend']} | {c['Sales']} | {c['Orders']} | {c['ROAS']} |")
    else:
        L("No campaign data available.")
    L("")

    # --- Validation ---
    validation_md = load_text_file(a.validation_report) if a.validation_report else None
    if validation_md:
        L("## Validation")
        L("")
        L(validation_md)
        L("")

    # --- Footer ---
    L("---")
    L("*Source: Platform settlement exports. Net Payout calculated from components (Net Sales - Commissions - Ad Spend - Other Adjustments), not from platform payout column. All sales figures exclude tax.*")

    with open(a.output, "w") as fh: fh.write("\n".join(lines))
    print(f"Wrote Notion update: {a.output} ({len(lines)} lines)")

if __name__ == "__main__": main()
