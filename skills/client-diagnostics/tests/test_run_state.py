import json
import tempfile
from pathlib import Path
from orchestrator import run_state


def test_initial_state_shape():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "run_state.json"
        state = run_state.init("goop-kitchen-2026-05-08T14:30:00", path)
        assert state["run_id"] == "goop-kitchen-2026-05-08T14:30:00"
        assert state["phase"] == 1
        assert state["sub_skill_status"] == {
            "diagnostic-topline": "pending",
            "diagnostic-menu": "pending",
            "diagnostic-ops": "pending",
            "diagnostic-campaigns": "pending",
        }
        assert state["foundation_gate"] is None
        assert state["prior_run_id"] is None
        assert path.exists()
        assert json.loads(path.read_text())["run_id"] == state["run_id"]


def test_update_is_atomic_no_partial_writes():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "run_state.json"
        run_state.init("rid", path)
        run_state.update(path, sub_skill_status={"diagnostic-topline": "ok"})
        loaded = json.loads(path.read_text())
        assert loaded["sub_skill_status"]["diagnostic-topline"] == "ok"
        assert loaded["sub_skill_status"]["diagnostic-menu"] == "pending"  # not clobbered
        assert not list(path.parent.glob("*.tmp")), "temp file leaked"


def test_set_foundation_gate_and_phase():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "run_state.json"
        run_state.init("rid", path)
        run_state.update(path, phase=3, foundation_gate={"triggered": True, "triggers": [], "override_action_plan": True})
        loaded = json.loads(path.read_text())
        assert loaded["phase"] == 3
        assert loaded["foundation_gate"]["triggered"] is True
