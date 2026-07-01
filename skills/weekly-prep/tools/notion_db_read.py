#!/usr/bin/env python3
"""
notion_db_read.py — deterministic Notion database reader for weekly-prep.

WHY THIS EXISTS
  Maxx's Notion plan does NOT include the MCP's AI query tools:
    - notion-query-data-sources   -> "requires an Enterprise plan with Notion AI"
    - notion-query-database-view  -> "requires a Business plan or higher"
    - notion-fetch on a database  -> returns SCHEMA ONLY, zero rows
    - notion-search over a source -> lossy semantic grab-bag that SILENTLY DROPS
      rows (verified 2026-06-22: it missed BOTH of that week's booked deals).
  The standard Notion REST API (databases.query) is FREE on every plan with an
  internal integration token. This reader uses it to return COMPLETE, deterministic
  rows — no plan upgrade, no semantic lottery.

SETUP (one-time, ~15 min — see token-setup in the skill):
  1. notion.so/my-integrations -> New internal integration -> copy token (ntn_/secret_...).
  2. Share each DB below with that integration (DB ... menu -> Connections -> add).
  3. The Mac Mini ALREADY sets NOTION_TOKEN (ntn_...) per MAC-MINI-SETUP.md, and this
     reader uses it automatically. (Alt location: ~/.config/spice/notion-token, chmod 600.)
     The ONE gotcha: the integration must be SHARED with each DB above (DB -> Connections),
     or databases.query returns 404 for that DB.

USAGE
  python3 notion_db_read.py pipeline                  # active deals (built-in filter)
  python3 notion_db_read.py tasks --filter '<json>'   # pass a Notion filter object
  python3 notion_db_read.py onboarding
  python3 notion_db_read.py content
  python3 notion_db_read.py pipeline --all            # ignore the built-in active filter

EXIT CODES
  0  success — prints JSON {"db","count","rows":[...]} to stdout
  3  no token configured  -> CALLER MUST fall back to search-enumerate (see skill §4)
  4  bad usage
  5  Notion API error
"""
import json
import os
import sys
import urllib.request
import urllib.error

API_LEGACY = "2022-06-28"      # classic databases.query — works for every integration
API_DATASOURCE = "2025-09-03"  # data_sources.query — for workspaces on the new data-source API
TOKEN_FILE = os.path.expanduser("~/.config/spice/notion-token")

# database_id (page-level id) for each readable DB
# Verified 2026-06-22 via notion-fetch. Each entry: (database_id, data_source_id).
# The reader tries databases.query(database_id) then data_sources.query(data_source_id),
# so it works whether or not this workspace has migrated to the data-sources API.
DBS = {
    "pipeline":   ("1c0d3ff0-18e7-80fa-b0b6-cc5887a502c4", "1c0d3ff0-18e7-805b-ba76-000b04cc35c4"),  # Sales Pipeline (the CRM)
    "tasks":      ("1c8d3ff0-18e7-8054-8b14-cbc13c26bb25", "1c8d3ff0-18e7-80f0-a36b-000b6befe5b1"),  # Team Task Tracker
    "content":    ("2d1d3ff0-18e7-81be-bf3a-ece205560b99", "2d1d3ff0-18e7-8104-8426-000b6fa11fa3"),  # Content Calendar (pipeline+calendar; Pillar=Source Material = mined fodder)
    "onboarding": ("239d3ff0-18e7-807c-be1a-cd98715da818", "239d3ff0-18e7-8041-84d2-000b393bcc69"),  # Client Onboarding tasks
}

# Active sales stages — anything else (Won/Lost/Not a Fit/Ice Box) is excluded by default.
PIPELINE_ACTIVE = ["New Lead", "Reached Out", "Qualified", "Meeting Booked",
                   "Pitched", "Proposal Shared", "Agreement Sent"]

DEFAULT_FILTERS = {
    "pipeline": {"or": [{"property": "Deal stage", "select": {"equals": s}} for s in PIPELINE_ACTIVE]},
}


def load_token():
    tok = os.environ.get("NOTION_TOKEN")
    if tok:
        return tok.strip()
    try:
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    except OSError:
        return None


def flatten(prop):
    """Reduce a Notion property object to a plain scalar / list / None."""
    t = prop.get("type")
    v = prop.get(t)
    if v is None:
        return None
    if t in ("title", "rich_text"):
        return "".join(x.get("plain_text", "") for x in v) or None
    if t == "select":
        return v.get("name")
    if t == "status":
        return v.get("name")
    if t == "multi_select":
        return [x.get("name") for x in v]
    if t == "people":
        return [x.get("name") or x.get("id") for x in v]
    if t == "date":
        return v.get("start")
    if t in ("number", "checkbox", "email", "phone_number", "url",
             "created_time", "last_edited_time"):
        return v
    if t == "formula":
        return v.get(v.get("type"))
    if t == "rollup":
        inner = v.get(v.get("type"))
        if isinstance(inner, list):
            return [flatten(x) if isinstance(x, dict) and "type" in x else x for x in inner]
        return inner
    if t == "relation":
        return [x.get("id") for x in v]
    if t == "unique_id":
        num = v.get("number")
        pre = v.get("prefix")
        return f"{pre}-{num}" if pre else num
    return v  # unknown type: pass through raw


def _post(url, body, version, token):
    """Returns (status_code, payload_or_error_text). status 0 = unreachable."""
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {token}",
                 "Notion-Version": version,
                 "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return 200, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except urllib.error.URLError as e:
        return 0, str(e)


def query(ids, token, filt=None, page_size=100):
    db_id, ds_id = ids
    endpoints = [
        (f"https://api.notion.com/v1/databases/{db_id}/query", API_LEGACY),
        (f"https://api.notion.com/v1/data_sources/{ds_id}/query", API_DATASOURCE),
    ]
    rows, cursor, chosen = [], None, None
    while True:
        body = {"page_size": page_size,
                "sorts": [{"timestamp": "last_edited_time", "direction": "descending"}]}
        if filt:
            body["filter"] = filt
        if cursor:
            body["start_cursor"] = cursor
        if chosen is None:
            # First page: find an endpoint that works, then stick with it for pagination.
            last_err = None
            for url, ver in endpoints:
                status, payload = _post(url, body, ver, token)
                if status == 200:
                    chosen = (url, ver)
                    break
                last_err = f"{status}: {payload}"
            if chosen is None:
                sys.stderr.write(f"Notion query failed on both endpoints — {last_err}\n")
                sys.exit(5)
        else:
            status, payload = _post(chosen[0], body, chosen[1], token)
            if status != 200:
                sys.stderr.write(f"Notion API {status}: {payload}\n")
                sys.exit(5)
        for pg in payload.get("results", []):
            row = {k: flatten(p) for k, p in pg.get("properties", {}).items()}
            row["_id"] = pg.get("id")
            row["_url"] = pg.get("url")
            row["_last_edited"] = pg.get("last_edited_time")
            rows.append(row)
        if not payload.get("has_more"):
            return rows
        cursor = payload.get("next_cursor")


def main():
    args = sys.argv[1:]
    if not args or args[0] not in DBS:
        sys.stderr.write("usage: notion_db_read.py <%s> [--filter '<json>'] [--all]\n"
                         % "|".join(DBS))
        sys.exit(4)
    key = args[0]
    use_all = "--all" in args
    filt = DEFAULT_FILTERS.get(key) if not use_all else None
    if "--filter" in args:
        try:
            filt = json.loads(args[args.index("--filter") + 1])
        except (ValueError, IndexError):
            sys.stderr.write("--filter needs a valid JSON Notion filter object\n")
            sys.exit(4)

    token = load_token()
    if not token:
        sys.stderr.write(
            "NO_TOKEN: no NOTION_TOKEN env and no %s. "
            "Caller must use the search-enumerate fallback (skill §4).\n" % TOKEN_FILE)
        sys.exit(3)

    rows = query(DBS[key], token, filt)
    json.dump({"db": key, "count": len(rows), "rows": rows},
              sys.stdout, ensure_ascii=False, indent=None)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
