from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CLIENTS_DIR = Path(__file__).parent.parent / "clients"


class ClientConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ClientConfig:
    slug: str
    display_name: str
    notion_parent_page_id: str | None
    brand_color_primary: str | None
    thresholds_override: dict
    data_quirks: list[str]


def load(slug: str) -> ClientConfig:
    path = CLIENTS_DIR / f"{slug}.json"
    if not path.exists():
        raise ClientConfigError(
            f"No client config at {path}. Create one from clients/_template.json. "
            f"Available clients: {[p.stem for p in CLIENTS_DIR.glob('*.json') if p.stem != '_template']}"
        )
    raw = json.loads(path.read_text())
    return ClientConfig(
        slug=raw["client_slug"],
        display_name=raw["client_display_name"],
        notion_parent_page_id=raw["notion"].get("parent_page_id"),
        brand_color_primary=raw.get("brand", {}).get("color_primary"),
        thresholds_override=raw.get("thresholds_override", {}),
        data_quirks=raw.get("data_quirks", []),
    )


def list_clients() -> list[str]:
    return sorted(p.stem for p in CLIENTS_DIR.glob("*.json") if p.stem != "_template")
