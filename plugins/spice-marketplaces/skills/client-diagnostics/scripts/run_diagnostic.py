"""Single-command runner for diagnostics. GM-facing.

Usage:
    python scripts/run_diagnostic.py --client dailys --inputs-dir ~/Downloads/dailys-q1
    python scripts/run_diagnostic.py --client dailys --inputs-dir ~/Downloads/dailys-q1 --publish
    # One Cowork command → finished client-ready PDF in a stable folder:
    python scripts/run_diagnostic.py --client dailys --inputs-dir ~/Downloads/dailys-q1 \
        --pdf --out ~/Desktop/dailys-report

--publish creates the Notion page. --pdf renders report.pdf via headless Chrome
(implies --html). --out copies the final report.html/.pdf to a stable directory.
Without flags, artifacts are written to /tmp/diagnostic-runs/<client>/<ts>/.
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


def preflight_completeness(inputs_dir, will_produce_visual: bool):
    """Inventory the inputs vs the full-depth set and print a DEPTH assessment BEFORE
    anything is produced — so a partial run is never mistaken for a complete one (the gap
    that made Brasa's diagnostic far shallower than Virgil's reference run). Returns
    (depth_label, missing_categories). Heuristic, by filename/subfolder keywords."""
    import glob
    import os
    files = [p.lower() for p in glob.glob(str(inputs_dir) + "/**/*", recursive=True) if os.path.isfile(p)]

    def has(*kw):
        return any(any(k in f for k in kw) for f in files)

    cats = {
        "Topline financials": has("financ", "transaction", "orders", "sales", "performance", "payout"),
        "Ops (accuracy/quality/ratings)": has("accuracy", "operation", "quality", "rating", "review", "downtime", "uptime", "cancel"),
        "Conversion funnel": has("funnel", "conversion"),
        "Repeat / frequent customers": has("repeat", "frequent"),
        "Campaigns (ads/offers)": has("ads", "sponsored", "offer", "promo", "campaign"),
        "Storefront screenshots": any("screenshot" in f for f in files) or has(".png", ".jpg", ".jpeg"),
        "Prior-year (YoY)": has("prior", "yoy", "cycle0", "cycle-0", "baseline", "lastyear", "last-year", "_py", "py_"),
    }
    loss = {
        "Topline financials": "no hero stats / platform economics / tiers",
        "Ops (accuracy/quality/ratings)": "no ops detail or foundation gate",
        "Conversion funnel": "no menu-CVR funnel or 'conversion > spend' analysis",
        "Repeat / frequent customers": "radar Re-order dimension suppressed",
        "Campaigns (ads/offers)": "no campaign ROAS / spend-efficiency analysis",
        "Storefront screenshots": "no storefront audit visuals",
        "Prior-year (YoY)": "no year-over-year conversion/sales comparison",
    }
    core = cats["Topline financials"] and cats["Ops (accuracy/quality/ratings)"]
    deep = cats["Conversion funnel"] and cats["Repeat / frequent customers"] and cats["Campaigns (ads/offers)"]
    if core and deep and cats["Storefront screenshots"]:
        depth = "FULL"
    elif core and (cats["Conversion funnel"] or cats["Storefront screenshots"]):
        depth = "STANDARD"
    elif core:
        depth = "PARTIAL"
    elif cats["Topline financials"]:
        depth = "TOPLINE-ONLY"
    else:
        depth = "INSUFFICIENT"

    print("\n=== Completeness preflight (depth check BEFORE producing) ===")
    for k, present in cats.items():
        print(f"  {'OK ' if present else 'XX '} {k}" + ("" if present else f"   -> {loss[k]}"))
    if not will_produce_visual:
        print("  XX  Visual deliverable   -> text-only; no charts/PDF. Run with --pdf or --publish. "
              "The reference diagnostic's depth is largely its chart/PDF layer.")
    missing = [k for k, present in cats.items() if not present]
    print(f"  -> DEPTH: {depth}" + (f"  (missing: {', '.join(missing)})" if missing else "  — all inputs present"))
    if depth not in ("FULL", "STANDARD"):
        print("  !! This will NOT match a full-depth diagnostic. Pull the XX items above for parity with the reference,")
        print("     and stamp the page header with this DEPTH label so reviewers know it's partial.")
    return depth, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--inputs-dir", required=True, type=Path)
    ap.add_argument("--window-start", default=None, help="YYYY-MM-DD; default = 90 days ago")
    ap.add_argument("--window-end", default=None, help="YYYY-MM-DD; default = today")
    ap.add_argument("--publish", action="store_true", help="Publish to Notion (requires notion_parent_page_id in client config)")
    ap.add_argument("--html", action="store_true", help="Also write a styled self-contained report.html (PDF source / portable share)")
    ap.add_argument("--pdf", action="store_true", help="Also render report.pdf via headless Chrome (implies --html)")
    ap.add_argument("--out", default=None, type=Path, help="Stable output directory for the final report.html / report.pdf (default: the run dir)")
    ap.add_argument("--require-full", action="store_true", help="Abort if the completeness preflight isn't FULL/STANDARD depth (use for marquee client runs)")
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

    depth, missing = preflight_completeness(args.inputs_dir, will_produce_visual=(args.pdf or args.publish))
    if args.require_full and depth not in ("FULL", "STANDARD"):
        print(f"\nXX --require-full set and depth is {depth}. Aborting — add the missing inputs above, or drop --require-full.")
        sys.exit(2)

    # --publish implies html+pdf: the Notion page links to the exact-format PDF.
    want_html = args.html or args.pdf or args.out is not None or args.publish
    want_pdf = args.pdf or args.publish
    result = entry.run(
        client=cfg.slug,
        window_start=start.date().isoformat(),
        window_end=end.date().isoformat(),
        inputs_dir=args.inputs_dir,
        when=end,
        export_html=want_html,
    )

    print(f"\nArtifacts written to: {result.layout.root}")
    print(f"  notion_page.md (paste into Notion or use --publish next time)")
    print(f"  notion_blocks.json (Notion API blocks)")
    print(f"  charts in cross_cutting/ + per-sub-skill charts/ subdirs")

    # Stable deliverables: copy report.html (and render report.pdf) to --out
    # (or leave in the run dir). One command → finished files a GM can hand off.
    final_pdf = None
    if want_html:
        import shutil
        from orchestrator import pdf_export

        src_html = result.layout.root / "report.html"
        out_dir = (args.out or result.layout.root)
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{cfg.slug}-diagnostic"
        final_html = out_dir / f"{stem}.html"
        if src_html.exists() and src_html.resolve() != final_html.resolve():
            shutil.copy(src_html, final_html)
        print(f"\nDeliverables:")
        print(f"  {final_html}  (self-contained — opens in any browser)")
        if want_pdf:
            cand = out_dir / f"{stem}.pdf"
            if pdf_export.render_pdf(final_html, cand):
                final_pdf = cand
                print(f"  {cand}  (client-ready PDF — exact layout)")
            else:
                print(f"  ⚠️  PDF skipped: no headless Chrome/Chromium found. "
                      f"Open {final_html} and Print → Save as PDF, or install Chrome.")

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
        pdf_entries = [m for m in manifest if m.get("kind") == "pdf"]
        if pdf_entries:
            print("\n--- PDF attachment (keeps exact format in Notion) ---")
            if final_pdf:
                print(f"  1. Upload {final_pdf} to the Drive cycle folder, set link-viewable.")
                print(f"  2. Replace the '📄 PDF placeholder' paragraph in publish_blocks.json")
                print(f"     with a Notion bookmark/file block to that Drive URL before create-pages.")
            else:
                print("  PDF not rendered (no Chrome). Generate it (--pdf) or "
                      "print report.html, then upload + substitute as above.")
    else:
        print(f"\nNo --publish flag. To publish: re-run with --publish (after notion_parent_page_id is set in clients/{cfg.slug}.json).")


if __name__ == "__main__":
    main()
