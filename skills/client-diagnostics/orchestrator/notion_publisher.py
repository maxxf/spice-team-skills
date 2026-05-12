from __future__ import annotations

"""Notion publisher (Wk 4 Chunk 3 — text-only).

Takes the notion_blocks.json payload + a ClientConfig, strips image blocks
(replaces each with a paragraph placeholder), captures a manifest of PNGs the
GM uploads manually, and dispatches via an injected `create_page_fn` callable
so the orchestrator stays MCP-free for testability.

Wk 5 will replace the manual upload step with auto image upload.
"""

from typing import Callable

from orchestrator.client_config import ClientConfig


class NotionPublishError(RuntimeError):
    pass


def filter_image_blocks(blocks: list[dict]) -> tuple[list[dict], list[dict]]:
    """Strip image blocks for text-only publish. Return (filtered_blocks, charts_manifest).

    Each image block becomes a paragraph: '📊 Chart: <id> — see attached PNG (<filename>)'.
    The manifest captures id + path so GM knows what to upload manually.
    """
    out_blocks: list[dict] = []
    manifest: list[dict] = []
    for blk in blocks:
        if blk.get("type") == "image":
            ext = blk.get("image", {}).get("external", {})
            url = ext.get("url", "")
            chart_id = blk.get("_chart_id", "chart")
            filename = url.rsplit("/", 1)[-1] if url else "chart.png"
            out_blocks.append({
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"📊 Chart: {chart_id} — see attached PNG ({filename})"
                            },
                        }
                    ]
                },
            })
            manifest.append({
                "chart_id": chart_id,
                "local_path": url.replace("file://", "") if url.startswith("file://") else url,
                "filename": filename,
            })
        else:
            out_blocks.append(blk)
    return out_blocks, manifest


def publish(
    *,
    blocks: list[dict],
    config: ClientConfig,
    page_title: str,
    create_page_fn: Callable[..., dict] | None = None,
) -> dict:
    """Publish the diagnostic page. Returns {'notion_page_url': ..., 'charts_manifest': [...]}.

    Args:
      blocks: notion_blocks.json content
      config: client config (must have notion_parent_page_id set)
      page_title: e.g. "{Client} | Diagnostics & Action Plan | <window>"
      create_page_fn: injectable for testing. If None, must be called from a context with the
                      Notion MCP tool available; the orchestrator wires the real callable.

    Raises:
      NotionPublishError if config.notion_parent_page_id is None or create_page_fn is missing.
    """
    if not config.notion_parent_page_id:
        raise NotionPublishError(
            f"Client '{config.slug}' has no notion_parent_page_id set in clients/{config.slug}.json. "
            f"Run notion-search to find the client's wiki/portal page ID, then update the config."
        )
    filtered, manifest = filter_image_blocks(blocks)
    if create_page_fn is None:
        raise NotionPublishError(
            "create_page_fn must be provided (or call this from an MCP-enabled context)"
        )
    result = create_page_fn(
        parent_page_id=config.notion_parent_page_id,
        title=page_title,
        children=filtered,
    )
    return {"notion_page_url": result.get("url"), "charts_manifest": manifest}
