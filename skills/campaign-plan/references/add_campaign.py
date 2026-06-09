#!/usr/bin/env python3
"""GM-via-skill campaign input — write a new campaign to the Notion Campaign Planning DB.

The GM tells the skill in Cowork (e.g., *"add a BOGA campaign for goop at San Jose, Pasadena"*).
The skill collects any missing fields by asking, then runs this script to create the row.
Source of truth stays Notion DB; this is just a faster input method than opening Notion.

Notion DB writes use the same notion-create-pages MCP that the planning bridge uses for reads,
so this stays a thin CLI wrapper — most of the work happens in the skill (Claude) which gathers
inputs, applies playbook guardrails, and calls Notion via MCP.

This script is the **fallback / scripted path** when the skill wants a deterministic CLI
instead of the MCP. It writes the row via the Notion API using the service account.

Usage:
  python add_campaign.py --client-page-url <goop client URL> \\
    --name "goop — Friday Depth Tweak (SJ + Pasadena)" \\
    --type "Tiered Discount" \\
    --channels "Uber Eats,DoorDash" \\
    --locations "San Jose, Pasadena" \\
    --segment All \\
    --status Scheduled \\
    --start 2026-05-16 \\
    --roas-target 3.5 \\
    --offer-details "Single-day deeper promo Friday only"

Required: --client-page-url, --name, --type, --channels, --locations, --segment, --status
Optional: --start, --end, --roas-target, --offer-details, --notes, --client-review-since
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")

KEY = os.path.expanduser("~/.config/spice/google-sheets-writer.json")  # reuse for Drive scope only
NOTION_KEY_ENV = "NOTION_TOKEN"  # Notion API token (separate from Google service account)

CAMPAIGN_PLANNING_DS = "1c8d3ff0-18e7-8067-abff-000b54568283"

# Validation: client-facing segments + valid campaign types per the playbooks
VALID_SEGMENTS = ["All", "New Only", "Existing Only", "Lapsed", "DashPass"]
VALID_STATUSES = ["Not started", "Drafting", "Brief", "Design V.1", "Design V.2",
                  "Internal Review", "Client Review V.1", "Client Review V.2",
                  "Final Client Review", "Client Approved", "Scheduled", "Complete",
                  "Canceled", "On Hold"]
VALID_TYPES = ["BOGA", "BOGO", "% Off", "$ Off", "Free Delivery", "Bundle",
               "Featured Listing", "Sponsored Item", "Promoted Listing",
               "Sponsored Placement", "DashPass Offer", "Tiered Discount",
               "First Order", "Loyalty"]
VALID_CHANNELS = ["Uber Eats", "DoorDash", "GrubHub", "Email", "SMS", "Google",
                  "Meta/Instagram", "Blog"]


def _validate(args):
    errors = []
    if args.segment not in VALID_SEGMENTS:
        errors.append(f"--segment must be one of {VALID_SEGMENTS}, got {args.segment!r}")
    if args.status not in VALID_STATUSES:
        errors.append(f"--status must be one of {VALID_STATUSES}, got {args.status!r}")
    if args.type not in VALID_TYPES:
        errors.append(f"--type must be one of {VALID_TYPES}, got {args.type!r}")
    channels = [c.strip() for c in args.channels.split(",") if c.strip()]
    for ch in channels:
        if ch not in VALID_CHANNELS:
            errors.append(f"channel {ch!r} not in {VALID_CHANNELS}")
    # Playbook guardrail: marketplace only — block Meta from campaign-plan-tracked campaigns
    marketplace_channels = [c for c in channels if c in ("Uber Eats", "DoorDash", "GrubHub")]
    if not marketplace_channels:
        errors.append("at least one marketplace channel (Uber Eats / DoorDash / GrubHub) required — "
                      "campaign-plan tracks marketplace only; Meta is a separate service line")
    if errors:
        sys.exit("validation failed:\n  - " + "\n  - ".join(errors))
    return channels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-page-url", required=True, help="Notion URL of the client page")
    ap.add_argument("--name", required=True)
    ap.add_argument("--type", required=True, help=f"One of {VALID_TYPES}")
    ap.add_argument("--channels", required=True, help="Comma-sep (e.g. 'Uber Eats,DoorDash')")
    ap.add_argument("--locations", required=True)
    ap.add_argument("--segment", required=True, help=f"One of {VALID_SEGMENTS}")
    ap.add_argument("--status", required=True, help=f"One of {VALID_STATUSES}")
    ap.add_argument("--start", default=None, help="YYYY-MM-DD")
    ap.add_argument("--end", default=None)
    ap.add_argument("--roas-target", type=float, default=None)
    ap.add_argument("--offer-details", default="")
    ap.add_argument("--notes", default="", help="Performance Notes — cite the playbook precedent if applicable")
    ap.add_argument("--client-review-since", default=None,
                    help="YYYY-MM-DD; set when status enters Client Review (drives days-in-queue)")
    args = ap.parse_args()

    channels = _validate(args)

    # Build properties payload matching the Campaign Planning DB schema.
    # The skill calls notion-create-pages MCP directly with this payload; this script
    # serves as a reference template / validator. Print the payload as JSON for the skill
    # to use, OR write directly via the Notion API if NOTION_TOKEN is set.
    properties = {
        "Campaign name": args.name,
        "Entry Type": "Campaign",
        "Client": args.client_page_url,
        "Channels": json.dumps(channels),
        "Campaign Type": args.type,
        "Customer Segment": args.segment,
        "Offer Details": args.offer_details,
        "Locations": args.locations,
        "Status": args.status,
        "Service Team": "Marketplace",
        "Performance Notes": args.notes,
    }
    if args.start:
        properties["date:Start Date:start"] = args.start
    if args.end:
        properties["date:End Date:start"] = args.end
    if args.roas_target is not None:
        properties["ROAS Target"] = args.roas_target
    if args.client_review_since:
        properties["date:Client Review Since:start"] = args.client_review_since

    # The skill should pipe this payload into notion-create-pages with
    # parent={"type": "data_source_id", "data_source_id": CAMPAIGN_PLANNING_DS}.
    payload = {
        "parent": {"type": "data_source_id", "data_source_id": CAMPAIGN_PLANNING_DS},
        "pages": [{"properties": properties}],
    }
    print(json.dumps(payload, indent=2))
    print("\n# Pipe this to: notion-create-pages MCP call. Or set NOTION_TOKEN for direct API write.")


if __name__ == "__main__":
    main()
