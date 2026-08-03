"""dedup_gate — deterministic pre-create duplicate blocker for circleback-to-notion.

Creation is idempotent by construction: before the skill creates any Notion
task it runs `check`; after creating it runs `record`. Mechanical duplicates
(same meeting re-processed, same title, same reworded action) are blocked by
code — the LLM's semantic dedup runs on top of this gate, never instead of it.

Stdlib only.

CLI:
  python3 dedup_gate.py check  --proposals p.json --existing e.json \
      --ledger state/created-tasks.jsonl --today YYYY-MM-DD
  python3 dedup_gate.py record --created c.json \
      --ledger state/created-tasks.jsonl --today YYYY-MM-DD
"""
import argparse
import json
import os
import re
from datetime import date, timedelta

EXACT_TITLE_WINDOW_DAYS = 30
SIGNATURE_WINDOW_DAYS = 14
LEDGER_WINDOW_DAYS = 30
STOPWORDS = {"a", "an", "and", "the", "to", "for", "of", "on", "in", "with",
             "at", "by", "our", "their", "his", "her", "its"}


def _d(s):
    return date.fromisoformat(str(s)[:10]) if s else None


def _norm(text):
    return re.sub(r"[^a-z0-9 ]", "", (text or "").lower().replace("'", "")).strip()


def _tokens(text):
    return frozenset(w for w in _norm(text).split() if w and w not in STOPWORDS)


def _meeting_key(name, meeting_date):
    return "%s|%s" % (_norm(name), str(meeting_date or "")[:10])


def _signature(title, owner, client):
    return "%s|%s|%s" % ("+".join(sorted(_tokens(title))), owner or "", _norm(client))


def _load_ledger(ledger_path):
    entries = []
    if ledger_path and os.path.exists(ledger_path):
        with open(ledger_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    return entries


def check(proposals, existing_tasks, ledger_path, today, cap_per_owner=5):
    today_d = _d(today)
    ledger = _load_ledger(ledger_path)

    ledger_meetings = {e.get("meeting_key") for e in ledger if e.get("meeting_key")}
    ledger_sigs = {e["signature"] for e in ledger
                   if e.get("signature") and _d(e.get("date"))
                   and (today_d - _d(e["date"])).days <= LEDGER_WINDOW_DAYS}
    existing_descs = _norm(" || ".join(t.get("description") or "" for t in existing_tasks))

    allowed, blocked = [], []
    batch_sigs = set()

    for p in proposals:
        mkey = _meeting_key(p.get("meeting_name"), p.get("meeting_date"))
        sig = _signature(p.get("title"), p.get("owner_notion_id"), p.get("client_name"))
        reason, match = None, None

        meeting_norm = _norm(p.get("meeting_name"))
        if mkey in ledger_meetings or (meeting_norm and meeting_norm in existing_descs):
            reason = "meeting_already_processed"
            match = p.get("meeting_name")

        if reason is None:
            for t in existing_tasks:
                created = _d(t.get("created_time"))
                age = (today_d - created).days if created else None
                same_owner = p.get("owner_notion_id") in (t.get("owner_ids") or [])
                same_client = _norm(t.get("client_name")) == _norm(p.get("client_name"))
                if same_owner and same_client and age is not None \
                        and age <= EXACT_TITLE_WINDOW_DAYS \
                        and _norm(t.get("title")) == _norm(p.get("title")):
                    reason, match = "exact_title_match", t.get("url")
                    break
                if same_owner and age is not None and age <= SIGNATURE_WINDOW_DAYS \
                        and _tokens(t.get("title")) == _tokens(p.get("title")) \
                        and same_client:
                    reason, match = "signature_match", t.get("url")
                    break

        if reason is None and sig in ledger_sigs:
            reason = "previously_created"

        if reason is None and sig in batch_sigs:
            reason = "in_batch_duplicate"

        if reason:
            blocked.append({"proposal": p, "reason": reason, "match": match})
        else:
            batch_sigs.add(sig)
            allowed.append(p)

    # Deterministic per-owner flood cap. The July 1 + July 2 floods (15-19 tasks on one
    # owner) happened because the cap lived in prose the model skipped under load. It is
    # code now: proposals arrive in the caller's urgency order, so keep each owner's first
    # `cap_per_owner` as allowed (created Not-started) and spill the rest to `overflow`
    # (created `Need review`, never active). Unassigned work is not a per-person flood, so
    # it is exempt from the cap.
    capped, overflow, per_owner = [], [], {}
    for p in allowed:
        oid = p.get("owner_notion_id")
        if not oid:
            capped.append(p)
            continue
        per_owner[oid] = per_owner.get(oid, 0) + 1
        if per_owner[oid] <= cap_per_owner:
            capped.append(p)
        else:
            overflow.append({"proposal": p, "reason": "owner_cap_exceeded"})

    return {"allowed": capped, "overflow": overflow, "blocked": blocked,
            "counts": {"allowed": len(capped), "overflow": len(overflow),
                       "blocked": len(blocked)}}


def record(created, ledger_path, today):
    os.makedirs(os.path.dirname(ledger_path) or ".", exist_ok=True)
    with open(ledger_path, "a") as f:
        for c in created:
            f.write(json.dumps({
                "date": today,
                "title": c.get("title"),
                "signature": _signature(c.get("title"), c.get("owner_notion_id"),
                                        c.get("client_name")),
                "meeting_key": _meeting_key(c.get("meeting_name"), c.get("meeting_date")),
                "notion_url": c.get("notion_url"),
            }) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["check", "record"])
    p.add_argument("--proposals")
    p.add_argument("--existing")
    p.add_argument("--created")
    p.add_argument("--ledger", required=True)
    p.add_argument("--today", required=True)
    p.add_argument("--cap", type=int, default=5, help="max Not-started tasks per owner per run")
    a = p.parse_args()

    def load(path, default):
        if path and os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return default

    if a.mode == "check":
        out = check(load(a.proposals, []), load(a.existing, []), a.ledger, a.today, a.cap)
        print(json.dumps(out, indent=1))
    else:
        record(load(a.created, []), a.ledger, a.today)
        print(json.dumps({"recorded": len(load(a.created, []))}))


if __name__ == "__main__":
    main()
