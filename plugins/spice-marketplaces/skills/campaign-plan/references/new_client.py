#!/usr/bin/env python3
"""Onboard a new client to the campaign-plan skill in one shot.

Writes `clients/<slug>.json` from the args, creates the data folder, and (if the service
account key is present) runs the first refresh — which creates the client's live Google
Sheet in their Drive folder and records its sheet_id back into the config.

After this runs, the team can just say "update the campaign plan for [slug]" and the
loop works the same as any existing client.

Usage:
  python references/new_client.py \\
    --slug pret \\
    --display-name "Pret a Manger" \\
    --drive-folder-id 1i1PHXTOCScJaZAknD_k_dBOiACd0R9rf \\
    --slack-channel '#ext-pret-spice'

Skip --slack-channel if not known yet (the share reminder just won't print it).
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)  # allow importing sibling reference modules (drive_inputs, sheets_writer)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help="filesystem-safe slug (e.g. goop-kitchen, pret)")
    ap.add_argument("--display-name", required=True, help="title shown in the workbook + Sheet name")
    ap.add_argument("--drive-folder-id", required=True, help="client's Drive folder ID under 1. Active")
    ap.add_argument("--slack-channel", default=None, help="client Slack channel, e.g. '#ext-client-spice'")
    ap.add_argument("--data-dir", default=None, help="data folder (default /tmp/campaign-data-<slug>)")
    ap.add_argument("--no-initial-refresh", action="store_true",
                    help="Skip the first refresh (no Sheet created yet). Default runs it.")
    args = ap.parse_args()

    cfg_path = os.path.join(SKILL, "clients", f"{args.slug}.json")
    if os.path.exists(cfg_path):
        sys.exit(f"clients/{args.slug}.json already exists — onboarding skipped.")

    data_dir = args.data_dir or f"/tmp/campaign-data-{args.slug}"
    os.makedirs(data_dir, exist_ok=True)

    cfg = {
        "client_slug": args.slug,
        "client_display_name": args.display_name,
        "data_dir": data_dir,
        "campaigns_json": f"{args.slug}_campaigns.json",
        "campaign_perf_csv": "campaign_performance.csv",
        "ads_detail_csv": "ads_detail.csv",
        "output": os.path.expanduser(f"~/Downloads/{args.slug.replace('-', '_')}_Campaign_Plan.xlsx"),
        "drive_folder_id": args.drive_folder_id,
    }
    if args.slack_channel:
        cfg["slack_channel"] = args.slack_channel

    os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
    with open(cfg_path, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    print(f"✅ wrote {cfg_path}")
    print(f"   data folder: {data_dir}")

    # Stub campaigns JSON so the bridge has something to read (even if it's an empty plan).
    campaigns_path = os.path.join(data_dir, cfg["campaigns_json"])
    if not os.path.exists(campaigns_path):
        with open(campaigns_path, "w") as f:
            json.dump([], f)
            f.write("\n")
        print(f"   stub campaigns file: {campaigns_path} (empty — populate from Notion via the skill)")

    # Create the 'Campaign Plan Inputs' Drive subfolder in the client's folder.
    # Ops drops weekly platform exports here; the skill reads from this folder at refresh time.
    try:
        from drive_inputs import ensure_inputs_folder
        inputs_id = ensure_inputs_folder(args.drive_folder_id)
        if inputs_id:
            print(f"   Drive inputs folder ready: https://drive.google.com/drive/folders/{inputs_id}")
    except Exception as e:
        print(f"   ⚠️  could not create 'Campaign Plan Inputs' Drive folder: {e}")
        print(f"      (skipping — create it manually under {args.drive_folder_id} or rerun with auth fixed)")

    if args.no_initial_refresh:
        print("\nSkipped initial refresh per --no-initial-refresh. Next step:")
        print(f"  .venv/bin/python references/refresh.py --client {args.slug}")
        return

    print("\n→ Running initial refresh (creates the live Google Sheet)...")
    r = subprocess.run([sys.executable, os.path.join(HERE, "refresh.py"), "--client", args.slug],
                       cwd=SKILL)
    if r.returncode != 0:
        sys.exit(f"\n⚠️  initial refresh failed (exit {r.returncode}). Config is written; "
                 "re-run refresh after fixing the cause.")


if __name__ == "__main__":
    main()
