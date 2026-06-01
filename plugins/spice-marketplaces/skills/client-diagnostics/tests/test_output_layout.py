from datetime import datetime
from pathlib import Path
import tempfile
from orchestrator import output_layout


def test_run_dir_layout(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp))
        ts = datetime(2026, 5, 8, 14, 30, 0)
        layout = output_layout.create_run_dirs("goop-kitchen", ts)

        assert layout.root == Path(tmp) / "goop-kitchen" / "2026-05-08T14:30:00"
        assert (layout.root / "inputs").is_dir()
        assert (layout.root / "topline" / "charts").is_dir()
        assert (layout.root / "menu" / "charts").is_dir()
        assert (layout.root / "ops" / "charts").is_dir()
        assert (layout.root / "campaigns" / "charts").is_dir()
        assert (layout.root / "cross_cutting").is_dir()
        assert (layout.root / "action-plan").is_dir()
        assert layout.run_state_path == layout.root / "run_state.json"
        assert layout.sub_skill_results_path("topline") == layout.root / "topline" / "diagnostic-topline_results.json"


def test_archive_dir_per_client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp))
        archive = output_layout.archive_dir("goop-kitchen")
        assert archive == Path(tmp) / "goop-kitchen" / "_archive"
        assert archive.is_dir()


def test_create_run_dirs_idempotent(monkeypatch):
    """Calling twice with same timestamp doesn't error."""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp))
        ts = datetime(2026, 5, 8, 14, 30, 0)
        layout1 = output_layout.create_run_dirs("c", ts)
        layout2 = output_layout.create_run_dirs("c", ts)
        assert layout1.root == layout2.root


def test_sub_skill_results_path_for_each_known_sub_skill(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(output_layout, "RUN_ROOT", Path(tmp))
        layout = output_layout.create_run_dirs("c", datetime(2026, 5, 8))
        for sub in ("topline", "menu", "ops", "campaigns"):
            p = layout.sub_skill_results_path(sub)
            assert p.parent == layout.root / sub
            assert p.name == f"diagnostic-{sub}_results.json"
