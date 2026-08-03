"""Tests for dedup_gate — deterministic pre-create duplicate blocker.

Run: python3 -m unittest test_dedup_gate -v
The gate makes task creation idempotent: mechanical duplicates are blocked
by code, not by the model remembering to check. The LLM's semantic dedup
runs on top of (never instead of) this gate.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dedup_gate as dg  # noqa: E402

TODAY = "2026-07-06"


def prop(**kw):
    return {
        "title": kw.get("title", "Send proposal to Capriotti's"),
        "owner_notion_id": kw.get("owner", "owner-1"),
        "client_name": kw.get("client", "Capriotti's"),
        "meeting_name": kw.get("meeting", "Capriotti's Weekly Sync"),
        "meeting_date": kw.get("meeting_date", "2026-07-06"),
    }


def existing(**kw):
    return {
        "url": kw.get("url", "https://x/t1"),
        "title": kw.get("title", "Send proposal to Capriotti's"),
        "owner_ids": kw.get("owner_ids", ["owner-1"]),
        "client_name": kw.get("client", "Capriotti's"),
        "description": kw.get("description", ""),
        "created_time": kw.get("created", "2026-07-01"),
        "status": kw.get("status", "Not started"),
    }


class GateCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.ledger = os.path.join(self.dir, "created-tasks.jsonl")

    def check(self, proposals, existing_tasks=None, today=TODAY):
        return dg.check(proposals, existing_tasks or [], self.ledger, today)

    def record(self, created, today=TODAY):
        dg.record(created, self.ledger, today)


class TestExactTitle(GateCase):
    def test_exact_title_same_owner_recent_blocked(self):
        r = self.check([prop()], [existing()])
        self.assertEqual(r["allowed"], [])
        self.assertEqual(r["blocked"][0]["reason"], "exact_title_match")

    def test_exact_title_different_owner_allowed(self):
        r = self.check([prop(owner="owner-2")], [existing()])
        self.assertEqual(len(r["allowed"]), 1)

    def test_exact_title_old_task_allowed(self):
        r = self.check([prop()], [existing(created="2026-05-01")])
        self.assertEqual(len(r["allowed"]), 1)

    def test_title_match_case_and_punct_insensitive(self):
        r = self.check([prop(title="send proposal to capriottis!!")],
                       [existing(title="Send Proposal to Capriotti's")])
        self.assertEqual(r["blocked"][0]["reason"], "exact_title_match")


class TestMeetingKey(GateCase):
    def test_meeting_already_in_ledger_blocks_rerun(self):
        self.record([{**prop(), "notion_url": "https://x/created1"}])
        r = self.check([prop(title="Totally different follow-up")])
        self.assertEqual(r["blocked"][0]["reason"], "meeting_already_processed")

    def test_meeting_in_existing_description_blocks(self):
        e = existing(title="Something else",
                     description="Context.\n\nSource: Capriotti's Weekly Sync (2026-07-06)")
        r = self.check([prop(title="Different title")], [e])
        self.assertEqual(r["blocked"][0]["reason"], "meeting_already_processed")

    def test_different_meeting_same_day_allowed(self):
        self.record([{**prop(meeting="Goop Strategy Call"), "notion_url": "https://x/c2"}])
        r = self.check([prop(meeting="Capriotti's Weekly Sync",
                             title="A brand new unrelated ask")])
        self.assertEqual(len(r["allowed"]), 1)


class TestSignature(GateCase):
    def test_reworded_same_action_same_owner_client_blocked(self):
        e = existing(title="Send proposal to Capriotti's", created="2026-07-01")
        r = self.check([prop(title="Capriotti's proposal — send")], [e])
        self.assertEqual(r["blocked"][0]["reason"], "signature_match")

    def test_same_words_different_client_allowed(self):
        e = existing(title="Update menu photos", client="Goop Kitchen")
        r = self.check([prop(title="Update menu photos", client="Capriotti's",
                             meeting="Other Sync")], [e])
        self.assertEqual(len(r["allowed"]), 1)

    def test_signature_outside_14d_allowed(self):
        e = existing(title="Send the Capriotti's proposal", created="2026-06-10")
        r = self.check([prop(title="Send proposal — Capriotti's")], [e])
        self.assertEqual(len(r["allowed"]), 1)


class TestInBatch(GateCase):
    def test_in_batch_duplicate_second_blocked(self):
        p1 = prop(title="Pull UE settlement data")
        p2 = prop(title="Pull UE settlement data")
        r = self.check([p1, p2])
        self.assertEqual(len(r["allowed"]), 1)
        self.assertEqual(r["blocked"][0]["reason"], "in_batch_duplicate")


class TestLedgerRecord(GateCase):
    def test_record_then_check_blocks_same_signature(self):
        created = {**prop(), "notion_url": "https://x/new1"}
        self.record([created])
        r = self.check([prop(title="Send proposal to Capriotti's",
                             meeting="A Different Meeting")])
        self.assertEqual(r["blocked"][0]["reason"], "previously_created")

    def test_ledger_lines_are_jsonl(self):
        self.record([{**prop(), "notion_url": "https://x/new1"}])
        with open(self.ledger) as f:
            line = json.loads(f.readline())
        self.assertEqual(line["notion_url"], "https://x/new1")
        self.assertIn("signature", line)


class TestOwnerCap(GateCase):
    """Deterministic per-owner flood cap — the July 1 + July 2 floods (15-19 tasks on
    one owner) happened because the cap lived in prose the model ignored. It lives in
    code now: no run can put more than cap_per_owner Not-started tasks on one person."""

    def many(self, n, owner="owner-1", client="Capriotti's", meeting="Big Team Meeting"):
        return [prop(title="Action item number %d ship it" % i, owner=owner,
                     client=client, meeting=meeting) for i in range(n)]

    def test_owner_capped_at_five(self):
        r = self.check(self.many(7))
        self.assertEqual(len(r["allowed"]), 5)
        self.assertEqual(len(r["overflow"]), 2)
        self.assertTrue(all(o["reason"] == "owner_cap_exceeded" for o in r["overflow"]))

    def test_cap_is_per_owner(self):
        r = self.check(self.many(6, owner="owner-A")
                       + self.many(3, owner="owner-B", meeting="Other Meeting"))
        allowed_owners = [p["owner_notion_id"] for p in r["allowed"]]
        self.assertEqual(allowed_owners.count("owner-A"), 5)
        self.assertEqual(allowed_owners.count("owner-B"), 3)
        self.assertEqual(len(r["overflow"]), 1)

    def test_cap_keeps_first_five_in_priority_order(self):
        # caller passes proposals in urgency order; the gate keeps the first five.
        r = self.check(self.many(7))
        self.assertEqual([p["title"] for p in r["allowed"]],
                         ["Action item number %d ship it" % i for i in range(5)])

    def test_unassigned_never_capped(self):
        # unassigned tasks are not a per-person notification flood.
        r = self.check(self.many(8, owner=None))
        self.assertEqual(len(r["allowed"]), 8)
        self.assertEqual(r["overflow"], [])

    def test_under_cap_no_overflow(self):
        r = self.check(self.many(5))
        self.assertEqual(len(r["allowed"]), 5)
        self.assertEqual(r["overflow"], [])

    def test_custom_cap(self):
        r = dg.check(self.many(4), [], self.ledger, TODAY, cap_per_owner=2)
        self.assertEqual(len(r["allowed"]), 2)
        self.assertEqual(len(r["overflow"]), 2)


class TestRobustness(GateCase):
    def test_missing_ledger_all_allowed(self):
        r = self.check([prop()])
        self.assertEqual(len(r["allowed"]), 1)

    def test_no_owner_still_gated_by_meeting(self):
        self.record([{**prop(), "notion_url": "https://x/c1"}])
        r = self.check([prop(owner=None, title="Another thing")])
        self.assertEqual(r["blocked"][0]["reason"], "meeting_already_processed")


if __name__ == "__main__":
    unittest.main()
