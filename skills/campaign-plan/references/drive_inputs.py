#!/usr/bin/env python3
"""Drive inputs helper — manage the 'Campaign Plan Inputs / <weekstart>/' folders.

Auth = service account (same key as sheets_writer.py).
Convention:

    1. Active / <Client> / Campaign Plan Inputs / <weekstart>/ <files>

Ops drops files in the weekstart folder Sun/Mon. Skill pulls them at refresh time.

Usage:
  python drive_inputs.py ensure   --client-folder-id <id> --weekstart 2026-06-09
  python drive_inputs.py list     --folder-id <weekstart-folder-id>
  python drive_inputs.py download --folder-id <weekstart-folder-id> --local-dir /tmp/x
"""
from __future__ import annotations
import argparse
import io
import os
import sys
import warnings

warnings.filterwarnings("ignore")  # silence py3.9 EOL FutureWarnings

KEY = os.path.expanduser("~/.config/spice/google-sheets-writer.json")
SCOPES = ["https://www.googleapis.com/auth/drive"]
INPUTS_FOLDER_NAME = "Campaign Plan Inputs"
FOLDER_MIME = "application/vnd.google-apps.folder"

_DRIVE = None


def _drive():
    global _DRIVE
    if _DRIVE is None:
        if not os.path.exists(KEY):
            raise FileNotFoundError(
                f"service-account key missing at {KEY}; see references/google-service-account-setup.md."
            )
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
        _DRIVE = build("drive", "v3", credentials=creds, cache_discovery=False)
    return _DRIVE


def find_subfolder(name: str, parent_id: str) -> str | None:
    """Return the ID of a subfolder by name (case-sensitive), or None if it doesn't exist."""
    q = (f"name = '{name}' and '{parent_id}' in parents and "
         f"mimeType = '{FOLDER_MIME}' and trashed = false")
    r = _drive().files().list(
        q=q, fields="files(id,name)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    files = r.get("files", [])
    return files[0]["id"] if files else None


def find_or_create_folder(name: str, parent_id: str, dry_run: bool = False) -> str | None:
    """Find a subfolder by name under parent. Create if missing. Returns folder ID."""
    existing = find_subfolder(name, parent_id)
    if existing:
        return existing
    if dry_run:
        return None
    body = {"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]}
    f = _drive().files().create(body=body, fields="id", supportsAllDrives=True).execute()
    return f["id"]


def ensure_inputs_folder(client_drive_folder_id: str, dry_run: bool = False) -> str | None:
    """Ensure 'Campaign Plan Inputs' subfolder exists in the client's Drive folder."""
    return find_or_create_folder(INPUTS_FOLDER_NAME, client_drive_folder_id, dry_run=dry_run)


def ensure_weekstart_folder(client_drive_folder_id: str, weekstart: str,
                            dry_run: bool = False) -> str | None:
    """Ensure 'Campaign Plan Inputs / <weekstart>/' folder exists. Returns weekstart folder ID."""
    inputs_id = ensure_inputs_folder(client_drive_folder_id, dry_run=dry_run)
    if inputs_id is None:
        return None
    return find_or_create_folder(weekstart, inputs_id, dry_run=dry_run)


def find_weekstart_folder(client_drive_folder_id: str, weekstart: str) -> str | None:
    """Look up the weekstart folder without creating it. Returns ID or None."""
    inputs_id = find_subfolder(INPUTS_FOLDER_NAME, client_drive_folder_id)
    if not inputs_id:
        return None
    return find_subfolder(weekstart, inputs_id)


def list_input_files(weekstart_folder_id: str) -> list[dict]:
    """List non-trashed files in the weekstart folder."""
    q = f"'{weekstart_folder_id}' in parents and trashed = false"
    r = _drive().files().list(
        q=q, fields="files(id,name,mimeType,size,modifiedTime)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
        orderBy="name",
    ).execute()
    return r.get("files", [])


def download_inputs(weekstart_folder_id: str, local_dir: str) -> list[str]:
    """Download all files in the weekstart folder to local_dir. Returns list of local paths."""
    from googleapiclient.http import MediaIoBaseDownload
    os.makedirs(local_dir, exist_ok=True)
    drive = _drive()
    files = list_input_files(weekstart_folder_id)
    paths = []
    for f in files:
        local = os.path.join(local_dir, f["name"])
        req = drive.files().get_media(fileId=f["id"], supportsAllDrives=True)
        with open(local, "wb") as fh:
            dl = MediaIoBaseDownload(fh, req)
            done = False
            while not done:
                _, done = dl.next_chunk()
        paths.append(local)
    return paths


# ---- CLI ----

def _cmd_ensure(args):
    fid = ensure_weekstart_folder(args.client_folder_id, args.weekstart, dry_run=args.dry_run)
    tag = " (DRY RUN)" if args.dry_run else ""
    if fid:
        url = f"https://drive.google.com/drive/folders/{fid}"
        print(f"weekstart folder ready{tag}: {fid}\n  {url}")
    else:
        print(f"weekstart folder NOT created{tag}")


def _cmd_list(args):
    files = list_input_files(args.folder_id)
    for f in files:
        size = f.get("size", "—")
        print(f"  {f['name']:42s} {size:>10s} bytes  id={f['id']}")
    print(f"({len(files)} file{'s' if len(files) != 1 else ''})")


def _cmd_download(args):
    paths = download_inputs(args.folder_id, args.local_dir)
    for p in paths:
        print(f"  ✓ {p}")
    print(f"({len(paths)} file{'s' if len(paths) != 1 else ''} downloaded to {args.local_dir})")


def _cmd_find(args):
    fid = find_weekstart_folder(args.client_folder_id, args.weekstart)
    if fid:
        print(f"{fid}  https://drive.google.com/drive/folders/{fid}")
    else:
        sys.exit(f"no weekstart folder for {args.weekstart} under client folder {args.client_folder_id}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ensure", help="create the 'Campaign Plan Inputs / <weekstart>/' folder if missing")
    p.add_argument("--client-folder-id", required=True)
    p.add_argument("--weekstart", required=True, help="YYYY-MM-DD Monday (e.g. 2026-06-09)")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("find", help="look up the weekstart folder ID (no creation)")
    p.add_argument("--client-folder-id", required=True)
    p.add_argument("--weekstart", required=True)

    p = sub.add_parser("list", help="list files in a weekstart folder")
    p.add_argument("--folder-id", required=True)

    p = sub.add_parser("download", help="download all files in a weekstart folder to local dir")
    p.add_argument("--folder-id", required=True)
    p.add_argument("--local-dir", required=True)

    args = ap.parse_args()
    {"ensure": _cmd_ensure, "find": _cmd_find, "list": _cmd_list, "download": _cmd_download}[args.cmd](args)


if __name__ == "__main__":
    main()
