from __future__ import annotations

import pytest

from orchestrator import client_config
from orchestrator.client_config import ClientConfigError


def test_load_dailys_config():
    cfg = client_config.load("dailys")
    assert cfg.slug == "dailys"
    assert cfg.display_name == "Daily's"


def test_load_virgils_config():
    cfg = client_config.load("virgils")
    assert cfg.slug == "virgils"
    assert cfg.display_name == "Virgil's"


def test_load_unknown_client_lists_available():
    with pytest.raises(ClientConfigError) as excinfo:
        client_config.load("nonexistent")
    msg = str(excinfo.value)
    assert "dailys" in msg
    assert "virgils" in msg


def test_template_excluded_from_list_clients():
    clients = client_config.list_clients()
    assert "_template" not in clients
    assert "dailys" in clients
    assert "virgils" in clients


def test_notion_parent_page_id_is_null_for_unfilled_clients():
    dailys = client_config.load("dailys")
    virgils = client_config.load("virgils")
    assert dailys.notion_parent_page_id is None
    assert virgils.notion_parent_page_id is None
