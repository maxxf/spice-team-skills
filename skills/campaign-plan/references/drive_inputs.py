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
import json
import os
import sys
import threading
import time
import warnings

warnings.filterwarnings("ignore")  # silence py3.9 EOL FutureWarnings

KEY = os.path.expanduser("~/.config/spice/google-sheets-writer.json")
SCOPES = ["https://www.googleapis.com/auth/drive"]
INPUTS_FOLDER_NAME = "Campaign Plan Inputs"
FOLDER_MIME = "application/vnd.google-apps.folder"
NATIVE_MIME_PREFIX = "application/vnd.google-apps"

# Cache manifest lives beside the downloaded inputs. Dot-prefixed so the CSV
# readers that glob the inputs dir never pick it up as data.
MANIFEST_NAME = ".drive-cache.json"

# The pull is latency-bound, not bandwidth-bound: measured 2026-08-05 against
# goop's largest week, every file costs a fixed ~0.55s round trip regardless of
# size, so 19 files took 16s while the bytes themselves needed under 4s.
# Downloading in parallel is what makes this fast; 8 is well inside Drive's
# per-user rate limits.
MAX_WORKERS = 8

_DRIVE = None
_LOCAL = threading.local()


def _credentials():
    """Resolved via creds.py: HQ secrets injection first, key file second."""
    import creds
    return creds.credentials(SCOPES)


def _drive():
    global _DRIVE
    if _DRIVE is None:
        from googleapiclient.discovery import build
        _DRIVE = build("drive", "v3", credentials=_credentials(), cache_discovery=False)
    return _DRIVE


def _thread_drive():
    """A Drive client owned by the calling thread.

    googleapiclient service objects wrap a single non-thread-safe httplib2
    connection, so parallel downloads must not share one.
    """
    client = getattr(_LOCAL, "drive", None)
    if client is None:
        from googleapiclient.discovery import build
        client = build("drive", "v3", credentials=_credentials(), cache_discovery=False)
        _LOCAL.drive = client
    return client


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
    """Look up the week's inputs folder. Prefers an exact <weekstart> match; falls back to the
    most-recently-modified subfolder (the team sometimes names the folder by pull date, e.g.
    2026-06-09, rather than the Monday weekstart). Returns ID or None."""
    inputs_id = find_subfolder(INPUTS_FOLDER_NAME, client_drive_folder_id)
    if not inputs_id:
        return None
    exact = find_subfolder(weekstart, inputs_id)
    if exact:
        return exact
    r = _drive().files().list(
        q=f"'{inputs_id}' in parents and mimeType = '{FOLDER_MIME}' and trashed = false",
        fields="files(id,name,modifiedTime)", supportsAllDrives=True,
        includeItemsFromAllDrives=True, orderBy="modifiedTime desc",
    ).execute()
    fs = r.get("files", [])
    return fs[0]["id"] if fs else None


def list_input_files(weekstart_folder_id: str) -> list[dict]:
    """List non-trashed files in the weekstart folder."""
    q = f"'{weekstart_folder_id}' in parents and trashed = false"
    r = _drive().files().list(
        q=q, fields="files(id,name,mimeType,size,modifiedTime)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
        orderBy="name",
    ).execute()
    return r.get("files", [])


# ---- local cache ----

def _cache_key(f: dict) -> str:
    """Identity of a remote file's contents: size plus last-modified stamp."""
    return f"{int(f.get('size') or 0)}:{f.get('modifiedTime', '')}"


def _manifest_path(local_dir: str) -> str:
    return os.path.join(local_dir, MANIFEST_NAME)


def _read_manifest(local_dir: str) -> dict:
    """Previously downloaded files as {name: cache_key}. Unreadable = empty."""
    try:
        with open(_manifest_path(local_dir)) as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, NotADirectoryError):
        return {}
    except (json.JSONDecodeError, OSError) as e:
        print(f"   (cache manifest unreadable, re-downloading everything: {e})")
        return {}


def _write_manifest(local_dir: str, manifest: dict) -> None:
    os.makedirs(local_dir, exist_ok=True)
    tmp = _manifest_path(local_dir) + ".part"
    with open(tmp, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    os.replace(tmp, _manifest_path(local_dir))


def _plan_downloads(files: list[dict], local_dir: str, manifest: dict,
                    force: bool = False) -> tuple[list[dict], list[str]]:
    """Split remote files into (needs download, already valid locally).

    A cache hit requires all three of: the manifest recorded this exact
    size+modifiedTime, the local file exists, and its byte count still matches
    the remote size. Trusting the manifest alone would serve a deleted or
    half-written file as if it were good data.
    """
    todo: list[dict] = []
    cached: list[str] = []
    for f in files:
        local = os.path.join(local_dir, f["name"])
        native = str(f.get("mimeType", "")).startswith(NATIVE_MIME_PREFIX)
        size = int(f.get("size") or 0)
        hit = (
            not force
            and not native
            and manifest.get(f["name"]) == _cache_key(f)
            and os.path.exists(local)
            and os.path.getsize(local) == size
        )
        if hit:
            cached.append(local)
        else:
            todo.append(f)
    return todo, cached


def _worker_count(n_files: int, max_workers: int = MAX_WORKERS) -> int:
    return max(1, min(n_files, max_workers))


def _download_one(f: dict, local_dir: str) -> str:
    """Fetch a single file. Writes to a .part file and renames on success so an
    interrupted pull can never leave a truncated file that looks complete."""
    from googleapiclient.http import MediaIoBaseDownload
    local = os.path.join(local_dir, f["name"])
    tmp = local + ".part"
    req = _thread_drive().files().get_media(fileId=f["id"], supportsAllDrives=True)
    try:
        with open(tmp, "wb") as fh:
            dl = MediaIoBaseDownload(fh, req)
            done = False
            while not done:
                _, done = dl.next_chunk()
        os.replace(tmp, local)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return local


def download_inputs(weekstart_folder_id: str, local_dir: str, force: bool = False,
                    max_workers: int = MAX_WORKERS, progress: bool = True) -> list[str]:
    """Download all files in the weekstart folder to local_dir.

    Files already present and unchanged since the last pull are reused, so a
    re-run in the same week costs one listing call. Returns local paths for
    every input file, cached or freshly downloaded.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    os.makedirs(local_dir, exist_ok=True)
    files = list_input_files(weekstart_folder_id)
    if not files:
        return []

    manifest = _read_manifest(local_dir)
    todo, cached = _plan_downloads(files, local_dir, manifest, force=force)

    if progress and cached:
        print(f"   {len(cached)} of {len(files)} input file(s) already local, reusing")
    if not todo:
        return sorted(cached)

    total = len(todo)
    done_count = 0
    lock = threading.Lock()
    started = time.time()
    fetched: list[str] = []
    failures: list[tuple[str, BaseException]] = []

    if progress:
        print(f"   pulling {total} file(s) from Drive with {_worker_count(total, max_workers)} parallel workers…")

    with ThreadPoolExecutor(max_workers=_worker_count(total, max_workers)) as pool:
        futures = {pool.submit(_download_one, f, local_dir): f for f in todo}
        for fut in as_completed(futures):
            f = futures[fut]
            try:
                path = fut.result()
            except BaseException as e:  # noqa: BLE001 — reported below, never silently dropped
                failures.append((f["name"], e))
                continue
            fetched.append(path)
            manifest[f["name"]] = _cache_key(f)
            with lock:
                done_count += 1
                if progress:
                    print(f"   [{done_count}/{total}] {f['name']}", flush=True)

    _write_manifest(local_dir, manifest)

    if progress:
        mb = sum(os.path.getsize(p) for p in fetched) / 1e6
        print(f"   pulled {len(fetched)} file(s), {mb:.1f} MB in {time.time() - started:.1f}s")

    if failures:
        for name, e in failures:
            print(f"   ✗ {name}: {e}", file=sys.stderr)
        raise RuntimeError(
            f"{len(failures)} of {total} Drive input file(s) failed to download: "
            + ", ".join(n for n, _ in failures)
        )

    return sorted(fetched + cached)


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
    started = time.time()
    paths = download_inputs(args.folder_id, args.local_dir, force=args.force)
    for p in paths:
        print(f"  ✓ {p}")
    print(f"({len(paths)} file{'s' if len(paths) != 1 else ''} in {args.local_dir}, "
          f"{time.time() - started:.1f}s total)")


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
    p.add_argument("--force", action="store_true",
                   help="re-download everything, ignoring files already cached locally")

    args = ap.parse_args()
    {"ensure": _cmd_ensure, "find": _cmd_find, "list": _cmd_list, "download": _cmd_download}[args.cmd](args)


if __name__ == "__main__":
    main()
