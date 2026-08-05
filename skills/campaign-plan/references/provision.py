#!/usr/bin/env python3
"""Provision a client end to end — one command, no manual steps.

Replaces the sequence that used to take Maxx and a teammate three weeks and a Slack
thread: create a Sheet somewhere, share it with the robot, hand-write a config, get it
committed to the plugin, bump the version, discover the Sheet was an .xlsx.

What it does, idempotently:

  1. Validates the client's Drive folder is reachable and writable by the robot.
  2. Creates a NATIVE Google Sheet in that folder (never an .xlsx) if one isn't there.
  3. Ensures the 11 canonical tabs exist.
  4. Ensures the 'Campaign Plan Inputs' folder exists.
  5. Finds the client's weekly tracker Sheet and detects its actual tab names.
  6. Writes the config to the HQ clients directory.
  7. Runs the preflight doctor and reports.

No permission call, anywhere. Client folders live in a shared drive, so a Sheet created
inside one is reachable by the robot through drive membership — there is nothing to
grant and no human Share step. (See references.md, US-000.) The historical Share
friction came from three Sheets being hand-created in a personal My Drive instead.

Usage:
  python3 references/provision.py --slug pret --display-name "PRET A Manger" \\
      --drive-folder-id <id> [--slack-channel '#int-pret'] [--notion-page-id <id>]
  python3 references/provision.py --slug pret --check     # report state, change nothing
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import client_config  # noqa: E402

SHEET_MIME = "application/vnd.google-apps.spreadsheet"
FOLDER_MIME = "application/vnd.google-apps.folder"
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
KEY = os.path.expanduser(
    os.environ.get("SPICE_SHEETS_KEY", "~/.config/spice/google-sheets-writer.json")
)

# A tracker Sheet is recognised by its tabs, not its filename — names vary per client
# ("goop kitchen | weekly metrics", "Tiff's Treats | Weekly Metrics").
TRACKER_PLATFORM_HINTS = ["weekly platform overview", "platform overview"]
TRACKER_LOCATION_HINTS = ["by location"]
# Tabs that must never be chosen as the weekly platform tab, however closely they match.
# Abby's tracker carries both 'Monthly Platform Overview' and 'Weekly Platform Overview';
# picking the monthly one would silently report the wrong period.
TRACKER_TAB_EXCLUDE = ["monthly", "template", "archive", "raw", "instructions"]


def _pick_tab(titles: list[str], hints: list[str]) -> str | None:
    """Choose a tab by HINT priority, not by tab order.

    Iterating titles first and matching 'any hint' lets a tab that happens to sit earlier
    in the workbook beat a more specific hint — which is how Abby's picked 'Monthly
    Platform Overview' over 'Weekly Platform Overview'. Walk the hints in priority order
    instead, and skip tabs excluded outright.
    """
    usable = [t for t in titles
              if not any(x in t.lower() for x in TRACKER_TAB_EXCLUDE)]
    for hint in hints:
        for t in usable:
            if hint in t.lower():
                return t
    return None

_DRIVE = None
_SHEETS = None


def _clients():
    global _DRIVE, _SHEETS
    if _DRIVE is None:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        raw = os.environ.get("GOOGLE_SHEETS_WRITER_JSON")
        if raw:
            creds = service_account.Credentials.from_service_account_info(
                json.loads(raw), scopes=SCOPES)
        elif os.path.exists(KEY):
            creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
        else:
            sys.exit(f"no Google credential — set GOOGLE_SHEETS_WRITER_JSON or place the key at {KEY}")
        _DRIVE = build("drive", "v3", credentials=creds, cache_discovery=False)
        _SHEETS = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return _DRIVE, _SHEETS


def _list_children(folder_id: str, mime: str | None = None) -> list[dict]:
    """Children of a Drive folder. supportsAllDrives is mandatory — client folders live
    in a shared drive and without it they come back empty."""
    drive, _ = _clients()
    q = f"'{folder_id}' in parents and trashed = false"
    if mime:
        q += f" and mimeType = '{mime}'"
    out, token = [], None
    while True:
        r = drive.files().list(
            q=q, fields="nextPageToken, files(id,name,mimeType,driveId)",
            supportsAllDrives=True, includeItemsFromAllDrives=True,
            pageToken=token,
        ).execute()
        out.extend(r.get("files", []))
        token = r.get("nextPageToken")
        if not token:
            return out


def validate_folder(folder_id: str) -> dict:
    """Confirm the robot can see the folder and create files in it."""
    from googleapiclient.errors import HttpError

    drive, _ = _clients()
    try:
        meta = drive.files().get(
            fileId=folder_id,
            fields="id,name,mimeType,driveId,capabilities(canAddChildren)",
            supportsAllDrives=True,
        ).execute()
    except HttpError as e:
        sys.exit(f"cannot reach Drive folder {folder_id}: {e}\n"
                 f"Confirm the id is right and the folder is in the team's shared drive.")
    if meta["mimeType"] != FOLDER_MIME:
        sys.exit(f"{folder_id} is not a folder (mimeType {meta['mimeType']})")
    if not meta["capabilities"].get("canAddChildren"):
        sys.exit(f"robot cannot create files in '{meta['name']}' — check shared drive membership")
    return meta


def resolve_file(file_id: str) -> dict | None:
    """Fetch a file by id, or None if the robot cannot reach it."""
    from googleapiclient.errors import HttpError

    drive, _ = _clients()
    try:
        return drive.files().get(
            fileId=file_id,
            fields="id,name,mimeType,driveId,trashed,capabilities(canEdit)",
            supportsAllDrives=True,
        ).execute()
    except HttpError:
        return None


def find_campaign_sheet(folder_id: str, display_name: str,
                        configured_id: str | None = None) -> tuple[dict | None, str]:
    """Locate the client's campaign plan Sheet. Returns (file, how_we_found_it).

    Checks the CONFIG before the folder. Three of the six clients (pret, tiffs-treats,
    westville) have working Sheets that live in a personal My Drive rather than their
    client folder, so a folder-only search reports them missing — and creating a "missing"
    Sheet would orphan a live one with months of data in it. The config is the record of
    what is actually in use; the folder is only where new ones go.
    """
    if configured_id:
        f = resolve_file(configured_id)
        if f and not f.get("trashed") and f["mimeType"] == SHEET_MIME and f["capabilities"].get("canEdit"):
            return f, "config"
        if f and f["mimeType"] != SHEET_MIME:
            print(f"   warn: configured sheet_id is not a native Sheet ({f['mimeType']}) — "
                  "convert it (File > Save as Google Sheets) rather than letting a new one be created")
        elif f and f.get("trashed"):
            print("   warn: configured sheet_id is in the trash")
        elif configured_id:
            print("   warn: configured sheet_id is unreachable by the robot")

    for f in _list_children(folder_id, SHEET_MIME):
        n = f["name"].lower()
        if "campaign" in n and ("plan" in n or "tracker" in n):
            return f, "folder"
    return None, "none"


def create_campaign_sheet(folder_id: str, display_name: str) -> dict:
    """Create a native Sheet in the client's folder. No permission call — shared drive
    membership already grants the robot access (US-000)."""
    drive, _ = _clients()
    return drive.files().create(
        body={"name": f"{display_name} — Campaign Plan",
              "mimeType": SHEET_MIME,
              "parents": [folder_id]},
        fields="id,name,driveId,webViewLink",
        supportsAllDrives=True,
    ).execute()


def _read_tracker_tabs(sheet_id: str, name: str) -> dict | None:
    """Read a tracker's real tab names and pick the platform + location tabs.

    Tab names drift between clients — goop has 'By Location 2.0', Tiff's has plain
    'By Location'. Guessing wrong makes the per-location join silently return nothing,
    which is how Tiff's config shipped broken in June. So read them.

    Returns None when the Sheet has no recognisable platform tab, which means it isn't
    a weekly tracker.
    """
    _, sheets = _clients()
    from googleapiclient.errors import HttpError
    try:
        meta = sheets.spreadsheets().get(
            spreadsheetId=sheet_id, fields="sheets.properties.title").execute()
    except HttpError:
        return None
    titles = [s["properties"]["title"] for s in meta.get("sheets", [])]
    platform = _pick_tab(titles, TRACKER_PLATFORM_HINTS)
    location = _pick_tab(titles, TRACKER_LOCATION_HINTS)
    if not platform:
        return None
    return {"id": sheet_id, "name": name, "platform_tab": platform,
            "location_tab": location, "all_tabs": titles}


def inspect_tracker(sheet_id: str) -> dict | None:
    """Resolve an explicitly supplied tracker id and read its tabs.

    Most client trackers live OUTSIDE the client's Drive folder — several are still in
    someone's personal My Drive — so a folder scan reports them missing. Wiring a known
    id in beats letting 'missing' trigger the create path and duplicating a live tracker.
    """
    f = resolve_file(sheet_id)
    if not f:
        return None
    if f.get("mimeType") != SHEET_MIME:
        print(f"   warn: --tracker-sheet-id is not a native Google Sheet ({f.get('mimeType')})")
        return None
    tracker = _read_tracker_tabs(f["id"], f["name"])
    if tracker:
        tracker["via"] = "explicit id"
    return tracker


def detect_tracker(folder_id: str) -> dict | None:
    """Find the client's weekly tracker by scanning the client's Drive folder."""
    for f in _list_children(folder_id, SHEET_MIME):
        if "campaign" in f["name"].lower():
            continue  # that's the campaign plan, not the tracker
        tracker = _read_tracker_tabs(f["id"], f["name"])
        if tracker:
            return tracker
    return None


def build_config(slug, display_name, folder_id, sheet_id, tracker, slack_channel, notion_page_id,
                 existing: dict | None = None) -> dict:
    """Merge discovered values over any existing config, so re-provisioning never
    clobbers hand-tuned fields (location_aliases, tier_strategy, client_forecast)."""
    cfg = dict(existing or {})
    for k in ("_config_path", "_config_source"):
        cfg.pop(k, None)
    cfg.update({
        "client_slug": slug,
        "client_display_name": display_name,
        "data_dir": cfg.get("data_dir") or f"/tmp/campaign-data-{slug}",
        "campaigns_json": cfg.get("campaigns_json") or f"{slug}_campaigns.json",
        "campaign_perf_csv": cfg.get("campaign_perf_csv") or "campaign_performance.csv",
        "ads_detail_csv": cfg.get("ads_detail_csv") or "ads_detail.csv",
        "drive_folder_id": folder_id,
        "sheet_id": sheet_id,
        "v2": True,
    })
    if slack_channel:
        cfg["slack_channel"] = slack_channel
    if notion_page_id:
        cfg["notion_client_page_id"] = notion_page_id
    if tracker:
        cfg["net_sales_sheet_id"] = tracker["id"]
        cfg["net_sales_platform_tab"] = tracker["platform_tab"]
        if tracker["location_tab"]:
            cfg["net_sales_location_tab"] = tracker["location_tab"]
    return cfg


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--display-name", default=None, help="required for a new client")
    ap.add_argument("--drive-folder-id", default=None, help="required for a new client")
    ap.add_argument("--slack-channel", default=None)
    ap.add_argument("--notion-page-id", default=None, help="client's Notion page id")
    ap.add_argument("--tracker-sheet-id", default=None,
                    help="wire up an EXISTING weekly tracker by id (get it from the client's "
                         "Notion 'Weekly Metrics' property). Use this whenever the tracker lives "
                         "outside the client's Drive folder, which is most of them.")
    ap.add_argument("--check", action="store_true", help="report state, change nothing")
    args = ap.parse_args()

    existing = None
    try:
        existing = client_config.load(args.slug)
        print(f"→ existing config: {existing['_config_path']} [{existing['_config_source']}]")
    except FileNotFoundError:
        print(f"→ new client: {args.slug}")

    display = args.display_name or (existing or {}).get("client_display_name")
    folder_id = args.drive_folder_id or (existing or {}).get("drive_folder_id")
    if not display or not folder_id:
        sys.exit("need --display-name and --drive-folder-id for a client with no existing config")

    folder = validate_folder(folder_id)
    print(f"   folder: {folder['name']} (drive={folder.get('driveId') or 'MY_DRIVE'})")
    if not folder.get("driveId"):
        print("   warn: this folder is in a personal My Drive, not the shared drive. A Sheet "
              "created here depends on a revocable per-file grant.")

    # --- campaign plan Sheet (idempotent)
    sheet, how = find_campaign_sheet(folder_id, display, (existing or {}).get("sheet_id"))
    if sheet:
        print(f"   campaign sheet: adopting existing '{sheet['name']}' ({sheet['id']}, via {how})")
        if folder.get("driveId") and sheet.get("driveId") != folder.get("driveId"):
            print("     warn: this Sheet is outside the folder's shared drive — access depends "
                  "on a revocable per-file grant. Move it into the client folder.")
    elif args.check:
        print("   campaign sheet: MISSING (would create)")
    else:
        sheet = create_campaign_sheet(folder_id, display)
        print(f"   campaign sheet: created '{sheet['name']}' ({sheet['id']})")

    sheet_id = sheet["id"] if sheet else None

    # --- canonical tabs
    if sheet_id and not args.check:
        import sheets_writer as sw
        try:
            sw.ensure_template_tabs(sheet_id)
            print("   tabs: canonical set ensured")
        except Exception as e:  # noqa: BLE001 — report, don't abort a provision over formatting
            print(f"   warn: could not ensure tabs: {e}")

    # --- inputs folder
    if args.check:
        from drive_inputs import find_subfolder
        print(f"   inputs folder: {'present' if find_subfolder('Campaign Plan Inputs', folder_id) else 'MISSING (would create)'}")
    else:
        try:
            from drive_inputs import ensure_inputs_folder
            print(f"   inputs folder: {ensure_inputs_folder(folder_id)}")
        except Exception as e:  # noqa: BLE001
            print(f"   warn: could not ensure inputs folder: {e}")

    # --- weekly tracker. Same rule as the campaign Sheet: trust a working configured id
    # over a folder scan, since several trackers also live outside the client folder.
    tracker = None
    if getattr(args, "tracker_sheet_id", None):
        tracker = inspect_tracker(args.tracker_sheet_id)
        if not tracker:
            print(f"   ✗ --tracker-sheet-id {args.tracker_sheet_id} is unreachable, not a "
                  "Sheet, or has no recognisable platform tab.")
            print("     Refusing to fall back to a folder scan — that would report the tracker "
                  "missing and invite creating a duplicate of a live one.")
            return 1
    configured_tracker = (existing or {}).get("net_sales_sheet_id")
    if not tracker and configured_tracker:
        f = resolve_file(configured_tracker)
        if f and not f.get("trashed") and f["mimeType"] == SHEET_MIME:
            tracker = {"id": f["id"], "name": f["name"],
                       "platform_tab": (existing or {}).get("net_sales_platform_tab"),
                       "location_tab": (existing or {}).get("net_sales_location_tab"),
                       "all_tabs": [], "via": "config"}
        else:
            print("   warn: configured net_sales_sheet_id is unreachable or not a Sheet")
    if not tracker:
        tracker = detect_tracker(folder_id)
        if tracker:
            tracker["via"] = "folder"
    if tracker:
        loc = tracker["location_tab"] or "NOT FOUND"
        print(f"   weekly tracker: {tracker['name']}")
        print(f"     platform tab: {tracker['platform_tab']} | location tab: {loc}")
        if not tracker["location_tab"]:
            print(f"     warn: no 'By Location' tab among {tracker['all_tabs']} — "
                  "per-location joins will be empty")
    else:
        print("   weekly tracker: NOT FOUND in this folder.")
        print("     Most trackers live OUTSIDE the client folder. Check the client's Notion page "
              "'Weekly Metrics' property FIRST and pass it with --tracker-sheet-id.")
        print("     Only create a new one from the standard template if Notion has none — "
              "creating one that already exists elsewhere splits the client's history in two.")

    if args.check:
        print("\n--check: nothing was changed.")
        return 0

    # --- config
    cfg = build_config(args.slug, display, folder_id, sheet_id, tracker,
                       args.slack_channel, args.notion_page_id, existing)
    out_dir = client_config.write_dir()
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{args.slug}.json")
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    print(f"   config: {path}")

    os.makedirs(cfg["data_dir"], exist_ok=True)
    stub = os.path.join(cfg["data_dir"], cfg["campaigns_json"])
    if not os.path.exists(stub):
        with open(stub, "w") as f:
            json.dump([], f)

    if not cfg.get("notion_client_page_id"):
        print("   note: no notion_client_page_id — pass --notion-page-id so the Sheet links "
              "can be written onto the client's Notion page")

    # --- verify
    print("\n→ preflight:")
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(HERE, "doctor.py"),
                        "--client", args.slug], cwd=SKILL)
    if r.returncode == 0:
        print(f"\n{args.slug} is provisioned. Next: python3 references/refresh.py "
              f"--client {args.slug} --dry-run")
    else:
        print(f"\n{args.slug} provisioned with problems — see the doctor output above.")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
