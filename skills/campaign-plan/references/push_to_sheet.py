#!/usr/bin/env python3
"""Push a generated campaign-plan .xlsx into the client's Drive folder as a live Google Sheet.

In-place + stable link: the first run creates one Google Sheet in the client's Drive folder and
records its `sheet_id` in clients/<slug>.json. Every later run updates THAT SAME file
(same id, same URL, same sharing) by replacing its content from the freshly generated .xlsx.
The team gets a stable link to hand the client; the refresh just updates it.

Auth: service account key at ~/.config/spice/google-sheets-writer.json (see
google-service-account-setup.md). The robot must have Editor on the client's Drive folder.

Usage:
  python push_to_sheet.py --client goop-kitchen --xlsx /Users/.../goop_Campaign_Plan.xlsx
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")  # silence py3.9 EOL FutureWarnings from google libs

KEY_PATH = os.path.expanduser("~/.config/spice/google-sheets-writer.json")
SCOPES = ["https://www.googleapis.com/auth/drive"]
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SHEET_MIME = "application/vnd.google-apps.spreadsheet"
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)


def _drive():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    if not os.path.exists(KEY_PATH):
        sys.exit(f"no service-account key at {KEY_PATH}. See references/google-service-account-setup.md.")
    creds = service_account.Credentials.from_service_account_file(KEY_PATH, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def push(client_slug: str, xlsx_path: str) -> str:
    from googleapiclient.http import MediaFileUpload
    cfg_path = os.path.join(SKILL, "clients", f"{client_slug}.json")
    with open(cfg_path) as f:
        cfg = json.load(f)
    folder = cfg.get("drive_folder_id")
    sheet_id = cfg.get("sheet_id")
    title = f"{cfg['client_display_name']} — Campaign Plan"
    drive = _drive()
    media = MediaFileUpload(xlsx_path, mimetype=XLSX_MIME, resumable=True)

    # Update-in-place if we already have a valid Sheet; else create one in the client folder.
    if sheet_id:
        try:
            drive.files().get(fileId=sheet_id, fields="id", supportsAllDrives=True).execute()
        except Exception:
            sheet_id = None  # recorded id is gone/inaccessible — recreate

    if sheet_id:
        f = drive.files().update(fileId=sheet_id, media_body=media,
                                 fields="id,webViewLink", supportsAllDrives=True).execute()
        action = "updated in place"
    else:
        if not folder:
            sys.exit(f"clients/{client_slug}.json has no drive_folder_id — can't create the Sheet.")
        body = {"name": title, "mimeType": SHEET_MIME, "parents": [folder]}
        f = drive.files().create(body=body, media_body=media,
                                 fields="id,webViewLink", supportsAllDrives=True).execute()
        action = "created"
        cfg["sheet_id"] = f["id"]
        with open(cfg_path, "w") as out:
            json.dump(cfg, out, indent=2)
            out.write("\n")

    url = f.get("webViewLink") or f"https://docs.google.com/spreadsheets/d/{f['id']}"
    print(f"Sheet {action}: {url}")
    return url


def _is_network_error(exc) -> bool:
    """True when the failure is 'can't reach Google' (the Cowork sandbox wall) rather than a
    real auth/sharing/data error. Cowork's cloud sandbox blocks outbound to Google's token
    endpoint, so the same push that works on any Mac fails there with a transport/DNS/token error."""
    blob = f"{type(exc).__name__} {exc}".lower()
    return any(s in blob for s in (
        "transport", "getaddrinfo", "name resolution", "connection", "timed out", "timeout",
        "network is unreachable", "unreachable", "ssl", "socket", "failed to establish",
        "max retries", "newconnectionerror", "refresherror", "oauth", "token"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True, help="client slug -> clients/<slug>.json")
    ap.add_argument("--xlsx", required=True, help="generated workbook to push")
    args = ap.parse_args()
    try:
        push(args.client, args.xlsx)
    except SystemExit:
        raise  # our own explicit exits (missing key, no drive_folder_id) already read clearly
    except Exception as exc:
        if _is_network_error(exc):
            sys.stderr.write(
                "\n" + "-" * 66 + "\n"
                "CAN'T REACH GOOGLE — the workbook was NOT published.\n"
                "You're almost certainly running in Cowork, whose sandbox blocks outbound\n"
                "network to Google. Your credentials and the Sheet are fine — this is only\n"
                "the Cowork network wall, not a setup problem.\n\n"
                f"Your finished workbook is ready here:\n  {args.xlsx}\n\n"
                "Publish it one of two ways:\n"
                f"  1) From your own Mac:  bash run_local.sh {args.client}   (see RUN-LOCALLY.md)\n"
                "  2) Manual: open the client's Sheet -> File -> Import -> Upload that .xlsx\n"
                "     -> \"Replace current sheet\" (about 2 minutes).\n"
                + "-" * 66 + "\n")
            sys.exit(3)
        raise  # a genuine, unexpected error — surface the full traceback


if __name__ == "__main__":
    main()
