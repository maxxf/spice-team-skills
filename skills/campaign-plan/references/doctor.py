#!/usr/bin/env python3
"""Preflight doctor — fail loudly and specifically, before anything writes.

Every failure that cost Santi time between 2026-06-16 and 2026-07-07 was silent or
generic: no key (silent error), a sheet_id pointing at an .xlsx, a sheet the robot
couldn't reach, missing Python deps, a stale plugin version. This checks all of them
up front and names the exact fix.

Usage:
  python3 references/doctor.py                 # every resolvable client
  python3 references/doctor.py --client goop-kitchen
  python3 references/doctor.py --json          # machine-readable
  python3 references/doctor.py --skip-notion   # skip the Notion probe

Exit codes: 0 = all clients green, 1 = at least one FAIL, 2 = doctor itself broke.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import client_config  # noqa: E402

KEY_PATH = os.path.expanduser(
    os.environ.get("SPICE_SHEETS_KEY", "~/.config/spice/google-sheets-writer.json")
)
NOTION_TOKEN_PATH = os.path.expanduser("~/.config/spice/notion-token")
SHEET_MIME = "application/vnd.google-apps.spreadsheet"
FOLDER_MIME = "application/vnd.google-apps.folder"
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]

FAIL, WARN, OK = "FAIL", "WARN", "OK"


class Report:
    def __init__(self):
        self.rows: list[dict] = []

    def add(self, scope, check, status, detail="", fix=""):
        self.rows.append(
            {"scope": scope, "check": check, "status": status, "detail": detail, "fix": fix}
        )

    @property
    def failed(self):
        return [r for r in self.rows if r["status"] == FAIL]

    @property
    def warned(self):
        return [r for r in self.rows if r["status"] == WARN]


# ---------------------------------------------------------------- environment


def check_env(rep: Report):
    """Credentials, deps, and config resolution — the things that block every client."""
    # Google credential. HQ secrets first, since that is where this is heading.
    cred_source = None
    if os.environ.get("GOOGLE_SHEETS_WRITER_JSON"):
        cred_source = "env (HQ secrets injected)"
        rep.add("env", "google credential", OK, cred_source)
    elif os.path.exists(KEY_PATH):
        cred_source = f"file {KEY_PATH}"
        mode = oct(os.stat(KEY_PATH).st_mode & 0o777)
        rep.add("env", "google credential", OK, cred_source)
        if mode != "0o600":
            rep.add(
                "env", "google credential permissions", WARN, f"mode {mode}",
                f"chmod 600 {KEY_PATH}",
            )
    else:
        rep.add(
            "env", "google credential", FAIL, "not found",
            "hq secrets exec --only GOOGLE_SHEETS_WRITER_JSON -- <cmd>, "
            f"or place the key at {KEY_PATH}",
        )

    # Python deps
    try:
        import googleapiclient  # noqa: F401
        import google.oauth2.service_account  # noqa: F401

        rep.add("env", "google python deps", OK, sys.executable)
    except ImportError as e:
        rep.add(
            "env", "google python deps", FAIL, str(e),
            f"{sys.executable} -m pip install --user google-api-python-client google-auth openpyxl "
            "(or set SPICE_PY to a venv python that has them)",
        )

    # Config resolution — surfaces the order so a stale plugin copy is obvious
    order = client_config.search_path()
    present = [f"{lbl}:{d}" for d, lbl in order if os.path.isdir(d)]
    if present:
        rep.add("env", "config resolution", OK, " | ".join(present))
    else:
        rep.add(
            "env", "config resolution", FAIL, "no clients directory found",
            "expected companies/spice/skills/campaign-plan/clients/ under the HQ root",
        )
    if not any(lbl in ("hq", "env") for d, lbl in order if os.path.isdir(d)):
        rep.add(
            "env", "config source", WARN, "resolving from the plugin bundle only",
            "adding a client will require a plugin commit + version bump until HQ is on the path",
        )


def notion_token():
    tok = os.environ.get("NOTION_TOKEN")
    if tok:
        return tok.strip(), "env (HQ secrets injected)"
    if os.path.exists(NOTION_TOKEN_PATH):
        with open(NOTION_TOKEN_PATH) as f:
            return f.read().strip(), f"file {NOTION_TOKEN_PATH}"
    return None, None


def check_notion(rep: Report):
    tok, source = notion_token()
    if not tok:
        rep.add(
            "env", "notion token", WARN, "not found",
            "campaign pulls will fail; hq secrets exec --only NOTION_TOKEN -- <cmd>",
        )
        return
    try:
        import urllib.request

        req = urllib.request.Request(
            "https://api.notion.com/v1/users/me",
            headers={"Authorization": f"Bearer {tok}", "Notion-Version": "2022-06-28"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            body = json.loads(r.read())
        who = body.get("bot", {}).get("owner", {}).get("type") or body.get("name") or "bot"
        rep.add("env", "notion token", OK, f"{source} — authenticates as {who}")
    except Exception as e:  # noqa: BLE001 — any failure here is a real, reportable failure
        rep.add(
            "env", "notion token", FAIL, f"{source} — {type(e).__name__}: {str(e)[:160]}",
            "token is present but rejected or unreachable; re-issue it and store in HQ secrets",
        )


# ---------------------------------------------------------------- google clients


def google_clients():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    raw = os.environ.get("GOOGLE_SHEETS_WRITER_JSON")
    if raw:
        creds = service_account.Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_file(KEY_PATH, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


# ---------------------------------------------------------------- per client

FILE_FIELDS = "id,name,mimeType,driveId,trashed,capabilities(canEdit,canDelete,canAddChildren)"


def probe_file(drive, file_id):
    """Return (metadata, error_string). Always uses supportsAllDrives — client folders
    live in a Shared Drive and omitting it makes files look like they don't exist."""
    from googleapiclient.errors import HttpError

    try:
        return drive.files().get(
            fileId=file_id, fields=FILE_FIELDS, supportsAllDrives=True
        ).execute(), None
    except HttpError as e:
        return None, f"{e.resp.status if e.resp else '?'} {str(e)[:120]}"


def check_client(rep: Report, drive, slug, cfg):
    scope = slug
    rep.add(scope, "config", OK, f"{cfg['_config_path']} [{cfg['_config_source']}]")

    folder_drive_id = None

    # --- Drive folder
    folder_id = cfg.get("drive_folder_id")
    if not folder_id:
        rep.add(scope, "drive_folder_id", FAIL, "missing from config",
                "add the client's '1. Active' folder id")
    else:
        meta, err = probe_file(drive, folder_id)
        if err:
            rep.add(scope, "drive folder", FAIL, err,
                    "robot cannot see the folder — check it is inside the shared drive")
        elif meta["mimeType"] != FOLDER_MIME:
            rep.add(scope, "drive folder", FAIL, f"not a folder ({meta['mimeType']})",
                    "drive_folder_id points at a file, not the client folder")
        else:
            folder_drive_id = meta.get("driveId")
            can_add = meta["capabilities"].get("canAddChildren")
            rep.add(
                scope, "drive folder", OK if can_add else FAIL,
                f"{meta['name']} (drive={folder_drive_id or 'MY_DRIVE'}, canAddChildren={can_add})",
                "" if can_add else "robot cannot create files here — inputs pull and provisioning will fail",
            )

    # --- Campaign plan Sheet
    sheet_id = cfg.get("sheet_id")
    if not sheet_id:
        rep.add(scope, "sheet_id", WARN, "missing — no live Sheet yet",
                f"python3 references/new_client.py --slug {slug} ... (or provision it)")
    else:
        meta, err = probe_file(drive, sheet_id)
        if err:
            rep.add(scope, "campaign sheet", FAIL, err,
                    "robot has no access — if the Sheet sits in a personal My Drive, move it "
                    "into the shared drive rather than granting a per-file share")
        elif meta["mimeType"] != SHEET_MIME:
            rep.add(
                scope, "campaign sheet", FAIL,
                f"not a native Google Sheet — mimeType {meta['mimeType']}",
                "open the file in Drive, File > Save as Google Sheets, then update sheet_id. "
                "The Sheets API cannot write to an .xlsx.",
            )
        elif meta.get("trashed"):
            rep.add(scope, "campaign sheet", FAIL, "in the trash", "restore it or reprovision")
        elif not meta["capabilities"].get("canEdit"):
            rep.add(scope, "campaign sheet", FAIL, "robot has read-only access",
                    "grant the robot edit rights, or move the Sheet into the shared drive")
        else:
            sheet_drive_id = meta.get("driveId")
            rep.add(scope, "campaign sheet", OK,
                    f"{meta['name']} (drive={sheet_drive_id or 'MY_DRIVE'})")
            # The pret / tiffs-treats / westville failure mode
            if folder_drive_id and sheet_drive_id != folder_drive_id:
                rep.add(
                    scope, "sheet location", WARN,
                    f"Sheet is in {sheet_drive_id or 'a personal My Drive'} but its folder is in "
                    f"{folder_drive_id}",
                    "robot access depends on a revocable per-file grant — move the Sheet into "
                    "the shared drive folder",
                )

    # --- Weekly tracker (net sales source)
    tracker_id = cfg.get("net_sales_sheet_id")
    if not tracker_id:
        rep.add(scope, "weekly tracker", WARN, "net_sales_sheet_id not configured",
                "per-location marketing-spend joins will be empty without it")
    else:
        meta, err = probe_file(drive, tracker_id)
        if err:
            rep.add(scope, "weekly tracker", FAIL, err, "robot cannot read the tracker")
        elif meta["mimeType"] != SHEET_MIME:
            rep.add(scope, "weekly tracker", FAIL, f"not a native Sheet ({meta['mimeType']})",
                    "convert it to a Google Sheet")
        else:
            rep.add(scope, "weekly tracker", OK, meta["name"])

    # --- Notion client page (needed to write the two link properties)
    if not cfg.get("notion_client_page_id"):
        rep.add(scope, "notion_client_page_id", WARN, "missing from config",
                "needed to write the tracker + campaign plan link properties onto the client page")


# ---------------------------------------------------------------- output


def render(rep: Report, as_json: bool):
    if as_json:
        print(json.dumps(rep.rows, indent=2))
        return

    width = max((len(r["scope"]) for r in rep.rows), default=6)
    current = None
    for r in rep.rows:
        if r["scope"] != current:
            current = r["scope"]
            print(f"\n{current}")
        icon = {OK: "  ok  ", WARN: " warn ", FAIL: " FAIL "}[r["status"]]
        print(f"  [{icon}] {r['check']:28} {r['detail']}")
        if r["fix"]:
            print(f"           fix: {r['fix']}")

    print()
    if rep.failed:
        print(f"{len(rep.failed)} FAIL, {len(rep.warned)} warn — fix the failures before refreshing.")
    elif rep.warned:
        print(f"green with {len(rep.warned)} warning(s).")
    else:
        print("all green.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--client", default=None, help="check one client (default: all)")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--skip-notion", action="store_true")
    args = ap.parse_args()

    rep = Report()
    check_env(rep)
    if not args.skip_notion:
        check_notion(rep)

    fatal_env = [r for r in rep.failed if r["check"] in ("google credential", "google python deps")]
    if fatal_env:
        render(rep, args.as_json)
        return 1

    try:
        drive = google_clients()
    except Exception as e:  # noqa: BLE001
        rep.add("env", "google auth", FAIL, f"{type(e).__name__}: {str(e)[:200]}",
                "credential is present but unusable")
        render(rep, args.as_json)
        return 1

    if args.client:
        try:
            targets = [(args.client, client_config.load(args.client))]
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            return 2
    else:
        targets = []
        for slug, _path, _source in client_config.available():
            targets.append((slug, client_config.load(slug)))

    if not targets:
        rep.add("env", "clients", FAIL, "no client configs found", "onboard one with new_client.py")

    for slug, cfg in targets:
        check_client(rep, drive, slug, cfg)

    render(rep, args.as_json)
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
