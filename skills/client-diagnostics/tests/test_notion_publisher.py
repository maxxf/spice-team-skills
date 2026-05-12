"""Wk 4 Chunk 3: notion_publisher tests.

Covers filter_image_blocks() (image-block stripping + manifest emission) and
publish() (config validation + injectable create_page_fn dispatch).
"""
from __future__ import annotations

import pytest

from orchestrator import notion_publisher
from orchestrator.client_config import ClientConfig
from orchestrator.notion_publisher import NotionPublishError


def _img_block(chart_id: str, filename: str) -> dict:
    return {
        "type": "image",
        "image": {
            "type": "external",
            "external": {"url": f"file:///tmp/{filename}"},
        },
        "_chart_id": chart_id,
    }


def _sample_blocks() -> list[dict]:
    """5 blocks: heading, paragraph, image, divider, image — image positions are 2 and 4."""
    return [
        {"type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Topline"}}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Body copy."}}]}},
        _img_block("radar_7dim", "chart1.png"),
        {"type": "divider", "divider": {}},
        _img_block("tier_donut", "chart2.png"),
    ]


def _config(notion_parent_page_id: str | None) -> ClientConfig:
    return ClientConfig(
        slug="testclient",
        display_name="Test",
        notion_parent_page_id=notion_parent_page_id,
        brand_color_primary=None,
        thresholds_override={},
        data_quirks=[],
    )


def test_filter_image_blocks_replaces_with_paragraph():
    blocks = _sample_blocks()
    filtered, _manifest = notion_publisher.filter_image_blocks(blocks)
    # Length unchanged
    assert len(filtered) == len(blocks)
    # Image positions (2 and 4) became paragraphs
    assert filtered[2]["type"] == "paragraph"
    assert filtered[4]["type"] == "paragraph"
    # Paragraph content references the chart_id
    text2 = filtered[2]["paragraph"]["rich_text"][0]["text"]["content"]
    text4 = filtered[4]["paragraph"]["rich_text"][0]["text"]["content"]
    assert "radar_7dim" in text2
    assert "tier_donut" in text4
    assert "Chart" in text2 and "Chart" in text4


def test_filter_image_blocks_preserves_non_image_blocks():
    blocks = _sample_blocks()
    filtered, _manifest = notion_publisher.filter_image_blocks(blocks)
    # Non-image positions (0, 1, 3) pass through identically
    assert filtered[0] == blocks[0]
    assert filtered[1] == blocks[1]
    assert filtered[3] == blocks[3]


def test_filter_image_blocks_emits_manifest():
    blocks = _sample_blocks()
    _filtered, manifest = notion_publisher.filter_image_blocks(blocks)
    assert len(manifest) == 2
    # First image entry
    assert manifest[0]["chart_id"] == "radar_7dim"
    assert manifest[0]["filename"] == "chart1.png"
    assert manifest[0]["local_path"] == "/tmp/chart1.png"  # file:// stripped
    # Second image entry
    assert manifest[1]["chart_id"] == "tier_donut"
    assert manifest[1]["filename"] == "chart2.png"
    assert manifest[1]["local_path"] == "/tmp/chart2.png"


def test_publish_raises_when_notion_target_missing():
    cfg = _config(notion_parent_page_id=None)
    blocks = _sample_blocks()
    with pytest.raises(NotionPublishError) as excinfo:
        notion_publisher.publish(
            blocks=blocks,
            config=cfg,
            page_title="Test | Diagnostics & Action Plan | 2026-02-08 – 2026-05-08",
            create_page_fn=lambda **kw: {"url": "x"},
        )
    msg = str(excinfo.value)
    assert "testclient" in msg  # references the slug
    assert "clients/testclient.json" in msg  # references the file path to fix


def test_publish_calls_create_page_fn_with_filtered_blocks():
    cfg = _config(notion_parent_page_id="abc123")
    blocks = _sample_blocks()
    captured: dict = {}

    def fake_create_page(**kwargs):
        captured.update(kwargs)
        return {"url": "https://notion.so/page-xyz"}

    title = "Test | Diagnostics & Action Plan | 2026-02-08 – 2026-05-08"
    notion_publisher.publish(
        blocks=blocks, config=cfg, page_title=title, create_page_fn=fake_create_page,
    )

    assert captured["parent_page_id"] == "abc123"
    assert captured["title"] == title
    children = captured["children"]
    assert len(children) == len(blocks)
    # The 2 image positions should now be paragraphs (filtering applied)
    assert children[2]["type"] == "paragraph"
    assert children[4]["type"] == "paragraph"
    # No image blocks present in children
    assert all(b.get("type") != "image" for b in children)


def test_publish_returns_notion_page_url_and_manifest():
    cfg = _config(notion_parent_page_id="abc123")
    blocks = _sample_blocks()

    result = notion_publisher.publish(
        blocks=blocks,
        config=cfg,
        page_title="Test | Diagnostics & Action Plan | 2026-02-08 – 2026-05-08",
        create_page_fn=lambda **kw: {"url": "https://notion.so/abc"},
    )

    assert result["notion_page_url"] == "https://notion.so/abc"
    assert isinstance(result["charts_manifest"], list)
    assert len(result["charts_manifest"]) == 2
    assert result["charts_manifest"][0]["chart_id"] == "radar_7dim"
    assert result["charts_manifest"][1]["chart_id"] == "tier_donut"


def test_publish_raises_when_create_page_fn_missing():
    cfg = _config(notion_parent_page_id="abc123")
    blocks = _sample_blocks()
    with pytest.raises(NotionPublishError):
        notion_publisher.publish(
            blocks=blocks,
            config=cfg,
            page_title="Test | Diagnostics & Action Plan | 2026-02-08 – 2026-05-08",
            create_page_fn=None,
        )
