"""Single-command runner for diagnostics. GM-facing.

Usage:
    python scripts/run_diagnostic.py --client dailys --inputs-dir ~/Downloads/dailys-q1
    python scripts/run_diagnostic.py --client dailys --inputs-dir ~/Downloads/dailys-q1 --publish

The --publish flag actually creates the Notion page; without it, only artifacts are written
to /tmp/diagnostic-runs/<client>/<timestamp>/ for manual review.
"""
from __future__ import annotations
import argparse
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Make orchestrator importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import client_config, entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--inputs-dir", required=True, type=Path)
    ap.add_argument("--window-start", default=None, help="YYYY-MM-DD; default = 90 days ago")
    ap.add_argument("--window-end", default=None, help="YYYY-MM-DD; default = today")
    ap.add_argument("--publish", action="store_true", help="Publish to Notion (requires notion_parent_page_id in client config)")
    args = ap.parse_args()

    cfg = client_config.load(args.client)

    # Default window: trailing 90d
    end = datetime.fromisoformat(args.window_end) if args.window_end else datetime.now()
    if args.window_start is not None:
        start = datetime.fromisoformat(args.window_start)
    else:
        start = end - timedelta(days=90)

    print(f"Running diagnostic for {cfg.display_name} ({cfg.slug})")
    print(f"  window: {start.date()} – {end.date()}")
    print(f"  inputs: {args.inputs_dir}")

    result = entry.run(
        client=cfg.slug,
        window_start=start.date().isoformat(),
        window_end=end.date().isoformat(),
        inputs_dir=args.inputs_dir,
        when=end,
    )

    print(f"\nArtifacts written to: {result.layout.root}")
    print(f"  notion_page.md (paste into Notion or use --publish next time)")
    print(f"  notion_blocks.json (Notion API blocks)")
    print(f"  charts in cross_cutting/ + per-sub-skill charts/ subdirs")

    if args.publish:
        if not cfg.notion_parent_page_id:
            print(f"\n⚠️  Cannot publish: clients/{cfg.slug}.json has notion_parent_page_id=null. Fill it in and re-run.")
            sys.exit(1)
        print(f"\nPublishing to Notion under page {cfg.notion_parent_page_id}...")
        print(f"  (Wk 4: image blocks become text placeholders; upload PNGs manually after page creation.)")
        # The actual notion-create-pages MCP call happens here.
        # For Wk 4: this script runs in a Claude context with MCP available.
        # The Claude session calling this script directly invokes the MCP tool with the filtered blocks.
        # Print the inputs needed for the MCP call:
        from orchestrator import notion_publisher
        blocks = json.loads((result.layout.root / "notion_blocks.json").read_text())
        filtered, manifest = notion_publisher.filter_image_blocks(blocks)
        manifest_path = result.layout.root / "charts_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"\n--- Notion publish payload (call notion-create-pages with this) ---")
        print(f"parent_page_id: {cfg.notion_parent_page_id}")
        print(f"title: {cfg.display_name} | Diagnostics & Action Plan | {start.date()} – {end.date()}")
        print(f"children: <{len(filtered)} blocks, written to {result.layout.root / 'publish_blocks.json'}>")
        print(f"charts to upload manually: {len(manifest)}, see {manifest_path}")
        (result.layout.root / "publish_blocks.json").write_text(json.dumps(filtered, indent=2))
    else:
        print(f"\nNo --publish flag. To publish: re-run with --publish (after notion_parent_page_id is set in clients/{cfg.slug}.json).")


if __name__ == "__main__":
    main()
