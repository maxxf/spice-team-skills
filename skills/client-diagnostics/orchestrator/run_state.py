"""Atomic shared run-state I/O. Orchestrator-only writer."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SUB_SKILLS = ("diagnostic-topline", "diagnostic-menu", "diagnostic-ops", "diagnostic-campaigns")


def init(run_id: str, path: Path, prior_run_id: str | None = None) -> dict[str, Any]:
    state = {
        "run_id": run_id,
        "phase": 1,
        "sub_skill_status": {s: "pending" for s in SUB_SKILLS},
        "foundation_gate": None,
        "prior_run_id": prior_run_id,
    }
    _atomic_write(path, state)
    return state


def update(path: Path, **fields) -> dict[str, Any]:
    state = json.loads(path.read_text())
    if "sub_skill_status" in fields:
        state["sub_skill_status"].update(fields.pop("sub_skill_status"))
    state.update(fields)
    _atomic_write(path, state)
    return state


def _atomic_write(path: Path, state: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    os.replace(tmp, path)
