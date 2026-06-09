#!/usr/bin/env python3
"""Project Campaign Planning DB rows into the campaign-plan tracker CSV.

This is the PLANNING half of the campaign plan. The skill (Claude) queries the Notion
Campaign Planning DB (collection://1c8d3ff0-18e7-8067-abff-000b54568283) for one client,
normalizes each page into the JSON shape below, and hands the array to this script. The
script emits the 16-column tracker CSV that build_campaign_plan_xlsx.py renders.

Deterministic transform — no network. Two responsibilities:
  1. Expand each DB campaign into one tracker row per delivery channel (UE/DD/GH/Meta).
  2. Project the DB's 14-value Status into the 5 client-facing statuses, derive Live from
     the flight window, and compute days-in-queue for items awaiting client sign-off.

Input JSON: array of objects keyed by DB property name. Example row:
  {
    "Campaign name": "goop — Spend X Save Y (SJ + Pasadena)",
    "Entry Type": "Campaign",
    "Channels": ["Uber Eats", "DoorDash"],
    "Campaign Type": "Tiered Discount",
    "Offer Details": "Tiered spend/save, lowered thresholds",
    "Locations": "San Jose, Pasadena",
    "Customer Segment": "All",
    "Status": "Scheduled",
    "Start Date": "2026-05-15",
    "End Date": "",
    "ROAS Target": 3.5,
    "Actual ROAS": null,
    "Performance Notes": "Drove San Jose conversion 25%->33%",
    "Client Review Since": null
  }

Usage:
  python db_to_tracker.py --db-json goop_campaigns.json --output goop_tracker.csv
  python db_to_tracker.py --db-json goop_campaigns.json --as-of 2026-05-21 --output goop_tracker.csv
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
import os

# Workbook tracker columns (must match build_campaign_plan_xlsx.TRACKER_COLS order).
TRACKER_COLS = ["Campaign", "Platform", "Type", "Offer / Ad Detail", "Locations", "Segment",
                "Status", "Days in Queue", "Flight Start", "Flight End",
                "Target ROAS", "Actual ROAS", "Spend ($)", "Attributed Sales ($)",
                "Incremental Orders", "In-Platform Campaign Name", "Notes"]

# DB channel name -> workbook platform name. Only delivery marketplace channels become rows.
# Meta/Instagram is intentionally excluded — the campaign plan tracks marketplace (UE/DD/GH) only.
CHANNEL_TO_PLATFORM = {
    "Uber Eats": "Uber Eats",
    "DoorDash": "DoorDash",
    "GrubHub": "Grubhub",
}

# DB Customer Segment -> client-facing segment bucket (New / Existing / Lapsed / All).
SEGMENT_MAP = {
    "New Only": "New", "Existing Only": "Existing", "Lapsed": "Lapsed",
    "All": "All", "DashPass": "Existing",  # DashPass subscribers are an existing-customer segment
}

# Campaign Type -> Ad vs Offer. Paid-placement types are Ads; everything else is an Offer.
AD_TYPES = {"Featured Listing", "Sponsored Item", "Promoted Listing", "Sponsored Placement"}

# DB Status -> client-facing status. "Scheduled"/"Client Approved" resolve to Live or
# Approved or Ended depending on the flight window, so they're handled in code, not here.
CLIENT_REVIEW = {"Client Review V.1", "Client Review V.2", "Final Client Review"}
PROPOSED = {"Not started", "Drafting", "Brief", "Design V.1", "Design V.2", "Internal Review"}


def _date(s):
    if not s:
        return None
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def project_status(db_status: str, start, end, as_of: dt.date):
    """Return (client_status, days_in_queue_or_blank). Drop returns (None, None)."""
    s = (db_status or "").strip()
    if s == "Canceled":
        return None, ""  # not shown to client
    if s in PROPOSED:
        return "Proposed", ""
    if s in CLIENT_REVIEW:
        return "Blocked-on-client", ""  # days filled by caller from Client Review Since
    if s == "On Hold":
        return "Blocked-on-client", ""
    if s == "Complete":
        return "Ended", ""
    if s in ("Client Approved", "Scheduled"):
        sd, ed = _date(start), _date(end)
        if sd and as_of < sd:
            return "Approved", ""          # signed off, not yet started
        if ed and as_of > ed:
            return "Ended", ""             # ran, now past the flight window
        if sd and as_of >= sd:
            return "Live", ""              # in flight (open-ended end included)
        return "Approved", ""              # approved, no start date yet
    return "Proposed", ""                  # unknown status -> safest default


def in_platform_name(locations: str, campaign_type: str, segment: str) -> str:
    """Reconstruct the campaign-ops convention: Location | Offer/Ad Type | Segment."""
    loc = (locations or "").split(",")[0].strip() or "All"
    return f"{loc} | {campaign_type or 'Offer'} | {segment or 'All'}"


def db_to_rows(campaigns: list[dict], as_of: dt.date) -> tuple[list[list], list[str]]:
    rows, skipped = [], []
    for c in campaigns:
        if (c.get("Entry Type") or "Campaign") != "Campaign":
            skipped.append(f"{c.get('Campaign name','?')} (Entry Type={c.get('Entry Type')})")
            continue
        ctype = c.get("Campaign Type") or ""
        ttype = "Ad" if ctype in AD_TYPES else "Offer"
        status, _ = project_status(c.get("Status"), c.get("Start Date"), c.get("End Date"), as_of)
        if status is None:
            skipped.append(f"{c.get('Campaign name','?')} (Canceled)")
            continue
        days = ""
        if status == "Blocked-on-client":
            since = _date(c.get("Client Review Since"))
            days = (as_of - since).days if since else ""
        channels = [ch for ch in (c.get("Channels") or []) if ch in CHANNEL_TO_PLATFORM]
        if not channels:
            skipped.append(f"{c.get('Campaign name','?')} (no marketplace channel)")
            continue
        segment = SEGMENT_MAP.get((c.get("Customer Segment") or "All").strip(), "All")
        for ch in channels:
            rows.append([
                c.get("Campaign name", ""),
                CHANNEL_TO_PLATFORM[ch],
                ttype,
                c.get("Offer Details") or ctype,
                c.get("Locations") or "",
                segment,
                status,
                days,
                c.get("Start Date") or "",
                c.get("End Date") or "",
                c.get("ROAS Target") if c.get("ROAS Target") not in (None, "") else "",
                c.get("Actual ROAS") if c.get("Actual ROAS") not in (None, "") else "",
                "", "", "",  # Spend / Attributed Sales / Incremental Orders — filled by perf feed
                in_platform_name(c.get("Locations"), ctype, c.get("Customer Segment")),
                c.get("Performance Notes") or "",
            ])
    return rows, skipped


def _snapshot_key(campaign: dict) -> str:
    """Stable identity for diffing across snapshots — uses the Notion page URL if present,
    falls back to the campaign name."""
    return campaign.get("_notion_url") or campaign.get("Campaign name", "")


def _snapshot_fields(campaign: dict) -> dict:
    """The subset of fields we track changes on. Trims noise (e.g., descriptive text)."""
    return {
        "status": campaign.get("Status", ""),
        "segment": campaign.get("Customer Segment", ""),
        "start": str(campaign.get("Start Date") or ""),
        "end": str(campaign.get("End Date") or ""),
        "roas_target": campaign.get("ROAS Target"),
        "locations": campaign.get("Locations", ""),
        "channels": sorted(campaign.get("Channels") or []),
        "campaign_type": campaign.get("Campaign Type", ""),
    }


def write_snapshot(campaigns: list[dict], snapshot_dir: str, weekstart: str) -> str:
    """Write the current DB pull to <snapshot_dir>/<weekstart>.json. Returns the path."""
    os.makedirs(snapshot_dir, exist_ok=True)
    path = os.path.join(snapshot_dir, f"{weekstart}.json")
    payload = {_snapshot_key(c): {**_snapshot_fields(c),
                                   "name": c.get("Campaign name", "")} for c in campaigns}
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path


def _find_prior_snapshot(snapshot_dir: str, before: str) -> str | None:
    """Find the most recent snapshot strictly before the `before` weekstart."""
    if not os.path.isdir(snapshot_dir):
        return None
    snaps = sorted(f for f in os.listdir(snapshot_dir)
                   if f.endswith(".json") and f[:-5] < before)
    return os.path.join(snapshot_dir, snaps[-1]) if snaps else None


def diff_snapshots(prior_path: str, current_campaigns: list[dict]) -> dict:
    """Compare prior snapshot (file) against current campaigns. Returns:
      {
        "added": [{name, fields}, ...],         # new campaigns since last
        "removed": [{name, fields}, ...],       # campaigns no longer present
        "changed": [{name, before, after, deltas: [...]}, ...],  # fields that moved
        "unchanged_count": N,
      }
    """
    with open(prior_path) as f:
        prior = json.load(f)
    current = {_snapshot_key(c): {**_snapshot_fields(c),
                                   "name": c.get("Campaign name", "")} for c in current_campaigns}

    added, removed, changed = [], [], []
    for key, cur in current.items():
        if key not in prior:
            added.append({"name": cur["name"], "fields": cur}); continue
        before = prior[key]
        deltas = [field for field in _snapshot_fields({}).keys()
                  if before.get(field) != cur.get(field)]
        if deltas:
            changed.append({"name": cur["name"], "before": before, "after": cur, "deltas": deltas})
    for key, prv in prior.items():
        if key not in current:
            removed.append({"name": prv.get("name", key), "fields": prv})
    unchanged = len(current) - len(changed) - len(added)
    return {"added": added, "removed": removed, "changed": changed,
            "unchanged_count": unchanged}


def format_changes_md(diff: dict) -> str:
    """Render the diff as a markdown block — feeds the GM's Monday Slack draft."""
    lines = []
    if diff["added"]:
        lines.append(f"**New campaigns ({len(diff['added'])}):**")
        for c in diff["added"]:
            lines.append(f"- {c['name']} ({c['fields']['status']}, {c['fields']['segment']})")
    if diff["changed"]:
        lines.append(f"\n**Status / field changes ({len(diff['changed'])}):**")
        for c in diff["changed"]:
            delta_str = ", ".join(f"{k}: {c['before'].get(k)!r} → {c['after'].get(k)!r}"
                                   for k in c["deltas"] if k in c["after"])
            lines.append(f"- {c['name']} — {delta_str}")
    if diff["removed"]:
        lines.append(f"\n**Removed since last refresh ({len(diff['removed'])}):**")
        for c in diff["removed"]:
            lines.append(f"- {c['name']}")
    if not (diff["added"] or diff["changed"] or diff["removed"]):
        lines.append("_No changes since the last snapshot._")
    lines.append(f"\n_{diff['unchanged_count']} campaign(s) unchanged._")
    return "\n".join(lines)


def write_csv(rows: list[list], out: str):
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(TRACKER_COLS)
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-json", required=True, help="JSON array of Campaign Planning DB rows for one client.")
    ap.add_argument("--as-of", default=None, help="Reference date YYYY-MM-DD for Live/queue math. Default today.")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    as_of = _date(args.as_of) or dt.date.today()
    with open(args.db_json) as f:
        campaigns = json.load(f)

    # Snapshot + diff: compare current DB pull against the prior snapshot, emit changes.
    weekstart = (as_of - dt.timedelta(days=as_of.weekday())).isoformat()
    data_dir = os.path.dirname(os.path.abspath(args.output))
    snapshot_dir = os.path.join(data_dir, "_snapshots")
    prior = _find_prior_snapshot(snapshot_dir, before=weekstart)
    diff = None
    if prior:
        diff = diff_snapshots(prior, campaigns)
        changes_md = format_changes_md(diff)
        changes_path = os.path.join(data_dir, f"changes_{weekstart}.md")
        with open(changes_path, "w") as f:
            f.write(f"# Campaign Plan Changes — {weekstart}\n\n_(vs prior snapshot {os.path.basename(prior)})_\n\n{changes_md}\n")
        print(f"→ changes vs prior snapshot {os.path.basename(prior)}: "
              f"{len(diff['added'])} added, {len(diff['changed'])} changed, "
              f"{len(diff['removed'])} removed, {diff['unchanged_count']} unchanged")
        print(f"  written to {changes_path}")
    snap_path = write_snapshot(campaigns, snapshot_dir, weekstart)
    print(f"  snapshot: {os.path.basename(snap_path)}")

    rows, skipped = db_to_rows(campaigns, as_of)
    write_csv(rows, args.output)
    print(f"wrote {args.output}: {len(rows)} tracker rows from {len(campaigns)} DB campaigns (as of {as_of}).")
    st = lambda name: sum(1 for r in rows if r[6] == name)  # status is column index 6
    print(f"  Live {st('Live')} | Blocked-on-client {st('Blocked-on-client')} | Proposed {st('Proposed')} "
          f"| Approved {st('Approved')} | Ended {st('Ended')}")
    if skipped:
        print(f"  skipped {len(skipped)}: {'; '.join(skipped[:8])}")


if __name__ == "__main__":
    main()
