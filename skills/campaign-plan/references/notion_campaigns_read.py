#!/usr/bin/env python3
"""Pull one client's Campaign Planning rows from Notion via the RAW REST API.

Why this exists: the Notion MCP's `query_data_sources` (SQL/view filter) is gated behind a
Notion Business plan, so a Cowork run — or any run leaning on the MCP — can't filter campaigns
by client. The raw REST endpoint `POST /v1/databases/{id}/query` is NOT gated. This reader hits
it directly with the integration token and writes the exact `campaigns_json` array that
`db_to_tracker.py` consumes — so `refresh.py` pulls the plan headlessly on any machine that has
the token (your Mac or the Mini), no Business plan required.

Token: NOTION_TOKEN env var, else ~/.config/spice/notion-token (same token weekly-prep uses).

Client filter: `notion_client_page_id` in clients/<slug>.json (the client's page ID in the
Notion Clients DB). Find it once by opening the client's row in the Clients DB and copying the
page ID from the URL; new_client.py can capture it at onboarding.

Usage:
  python notion_campaigns_read.py --client goop-kitchen --out /path/to/goop_campaigns.json
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)

# Campaign Planning database (raw-API database id — the /p/ id, not the collection uuid).
CAMPAIGN_PLANNING_DB = "1c8d3ff018e780169ad4f3268648490b"
NOTION_VERSION = "2022-06-28"
TOKEN_FILE = os.path.expanduser("~/.config/spice/notion-token")


def _load_token():
    tok = os.environ.get("NOTION_TOKEN")
    if not tok and os.path.exists(TOKEN_FILE):
        raw = open(TOKEN_FILE).read().strip()
        if raw.startswith("{"):
            try:
                j = json.loads(raw)
                raw = j.get("token") or j.get("notion_token") or j.get("NOTION_TOKEN") or raw
            except Exception:
                pass
        tok = raw
    return tok


# ── Notion property extractors ──────────────────────────────────────────────
def _txt(p):
    return "".join(t.get("plain_text", "") for t in (p.get("title") or p.get("rich_text") or [])) or ""


def _sel(p):
    s = p.get("select")
    return s.get("name") if s else None


def _status(p):
    s = p.get("status")
    return s.get("name") if s else None


def _multi(p):
    return [o.get("name") for o in (p.get("multi_select") or []) if o.get("name")]


def _date(p):
    d = p.get("date")
    return d.get("start") if d else None


def _num(p):
    return p.get("number")


def _row_from_page(page):
    """Map a Notion page object into the campaigns_json shape db_to_tracker.py expects."""
    p = page.get("properties", {})
    return {
        "Campaign name": _txt(p.get("Campaign name", {})),
        "Entry Type": _sel(p.get("Entry Type", {})),
        "Channels": _multi(p.get("Channels", {})),
        "Campaign Type": _sel(p.get("Campaign Type", {})),
        "Offer Details": _txt(p.get("Offer Details", {})),
        "Locations": _txt(p.get("Locations", {})),
        "Customer Segment": _sel(p.get("Customer Segment", {})),
        "Status": _status(p.get("Status", {})),
        "Start Date": _date(p.get("Start Date", {})),
        "End Date": _date(p.get("End Date", {})),
        "ROAS Target": _num(p.get("ROAS Target", {})),
        "Actual ROAS": _num(p.get("Actual ROAS", {})),
        "Performance Notes": _txt(p.get("Performance Notes", {})),
        "Client Review Since": _date(p.get("Client Review Since", {})),
        "_notion_url": page.get("url"),
    }


def _query_all(token, client_page_id):
    """Query every Campaign (Entry Type=Campaign) for one client, following pagination."""
    url = f"https://api.notion.com/v1/databases/{CAMPAIGN_PLANNING_DB}/query"
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION,
               "Content-Type": "application/json"}
    # Filter by the client relation ONLY. Do NOT also filter Entry Type == "Campaign" here:
    # db_to_tracker.py treats a blank Entry Type as "Campaign" (and skips Design Asset / Ad
    # Creative itself), and most real campaign rows leave Entry Type blank — so a server-side
    # Entry Type filter would silently drop them. Let db_to_tracker do the entry-type call.
    body = {
        "page_size": 100,
        "filter": {"property": "Client", "relation": {"contains": client_page_id}},
    }
    pages, cursor = [], None
    while True:
        if cursor:
            body["start_cursor"] = cursor
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        pages.extend(data.get("results", []))
        if data.get("has_more"):
            cursor = data.get("next_cursor")
        else:
            break
    return pages


def pull(client_slug, out_path, token=None):
    """Pull the client's campaigns and write the campaigns_json array. Returns the row count."""
    token = token or _load_token()
    if not token:
        raise RuntimeError(f"no Notion token (set NOTION_TOKEN or install {TOKEN_FILE})")
    cfg_path = os.path.join(SKILL, "clients", f"{client_slug}.json")
    if not os.path.exists(cfg_path):
        raise RuntimeError(f"no client config at {cfg_path}")
    cfg = json.load(open(cfg_path))
    # Canonical field is top-level `notion_client_page_id`; fall back to the strategy block's
    # `notion_parent_page_id` (same value — the client's page behind the Campaign Planning
    # `Client` relation), which existing configs already carry.
    page_id = cfg.get("notion_client_page_id") or (cfg.get("tier_strategy") or {}).get("notion_parent_page_id")
    if not page_id:
        raise RuntimeError(
            f"clients/{client_slug}.json has no client page id — add 'notion_client_page_id' (the "
            f"page behind the Campaign Planning 'Client' relation: open one of the client's campaign "
            f"rows, open the linked Client, copy the id from its URL).")
    pages = _query_all(token, page_id)
    rows = [_row_from_page(pg) for pg in pages]
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(rows, f, indent=2)
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--client", required=True, help="client slug -> clients/<slug>.json")
    ap.add_argument("--out", required=True, help="path to write the campaigns_json array")
    a = ap.parse_args()
    try:
        n = pull(a.client, a.out)
    except Exception as e:
        sys.exit(f"notion_campaigns_read: {e}")
    print(f"wrote {a.out}: {n} campaign rows for {a.client} (raw REST — no Business-plan gate)")


if __name__ == "__main__":
    main()
