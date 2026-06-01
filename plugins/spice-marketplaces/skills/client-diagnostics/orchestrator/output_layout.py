"""Resolve and create run-time output paths per spec §Contracts."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

RUN_ROOT = Path("/tmp/diagnostic-runs")
SUB_SKILLS = ("topline", "menu", "ops", "campaigns")


@dataclass(frozen=True)
class RunLayout:
    root: Path
    run_state_path: Path

    def sub_skill_results_path(self, sub_skill: str) -> Path:
        return self.root / sub_skill / f"diagnostic-{sub_skill}_results.json"


def create_run_dirs(client_slug: str, when: datetime) -> RunLayout:
    ts = when.strftime("%Y-%m-%dT%H:%M:%S")
    root = RUN_ROOT / client_slug / ts
    for sub in SUB_SKILLS:
        (root / sub / "charts").mkdir(parents=True, exist_ok=True)
    (root / "inputs").mkdir(parents=True, exist_ok=True)
    (root / "cross_cutting").mkdir(parents=True, exist_ok=True)
    (root / "action-plan").mkdir(parents=True, exist_ok=True)
    return RunLayout(root=root, run_state_path=root / "run_state.json")


def archive_dir(client_slug: str) -> Path:
    d = RUN_ROOT / client_slug / "_archive"
    d.mkdir(parents=True, exist_ok=True)
    return d
