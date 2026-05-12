# Diagnostics Orchestrator Wk 4 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development. TDD per task. Wk 1/2/3 plans are reference implementations.

**Goal:** Make the diagnostic usable for Daily's and Virgil's next week. Build the seam between real client data and the working pipeline; build the seam between the pipeline output and the client's Notion workspace.

**Success criteria:** Maxx + Ro can run the diagnostic against Daily's data, get a Notion page in Daily's workspace, attach charts manually, share with the client. Same for Virgil's. No more synthetic CSVs in the loop.

**State coming in:** 99 tests passing across 6 skills. End-to-end pipeline produces `notion_page.md`, `notion_blocks.json`, and 4 chart PNGs per run. Synthetic data only.

**Spec:** `specs/2026-05-08-orchestrator-redesign.md`
**Wk 1/2/3 plans (reference):** `plans/2026-05-08-*.md`

**Constraints (same as prior weeks):**
- Cowork is NOT in git — no commit steps
- Python 3.9 — `from __future__ import annotations` first line for any new `.py` using modern type hints
- `.venv/bin/pytest` always (no activation)
- Don't modify Wk 1/2/3 work outside the listed files per chunk
- After tests pass each chunk, deploy via `rsync` to `/Users/maxx/Desktop/spice-team-skills/skills/`
- **Notion MCP tool: `mcp__f34fcb36-bc14-4569-bc45-beaff552d0f7__notion-create-pages`** — already available; no auth setup needed

**Wk 4 explicitly does NOT cover (deferred to Wk 5):**
- Auto image upload to Notion (Wk 4 = manual chart upload by GM after page is published; PNGs delivered in `<run-dir>/cross_cutting/` and `<run-dir>/<sub-skill>/charts/`)
- Native UE/DD/GH platform CSV extraction (Wk 4 = GM produces a unified CSV from their existing weekly-reporting outputs or manual transcription; Wk 5 wires real extractors)
- Deliverable trigger auto-firing (kanban triggers stay as JSON for manual GM dispatch)
- Onboarding integration (`client-onboarding` skill auto-invoking diagnostic at kickoff)
- Deferred charts (sparklines/funnel/top_skus/daypart) — still need richer inputs
- v0.2 deprecation / migration

---

## File Structure

| Action | Path | Responsibility |
|---|---|---|
| Create | `Cowork/Skills/client-diagnostics/orchestrator/input_schema.py` | Validate the unified diagnostic input CSV; helpful errors |
| Create | `Cowork/Skills/client-diagnostics/references/input-csv-schema.md` | GM-facing doc: column reference + example row + how-to-fill from platform exports |
| Create | `Cowork/Skills/client-diagnostics/references/diagnostic-input-template.csv` | Empty template GM downloads + fills |
| Create | `Cowork/Skills/client-diagnostics/orchestrator/client_config.py` | Per-client config loader + validator |
| Create | `Cowork/Skills/client-diagnostics/clients/_template.json` | Per-client config template |
| Create | `Cowork/Skills/client-diagnostics/clients/dailys.json` | Daily's stub config (Maxx fills Notion target) |
| Create | `Cowork/Skills/client-diagnostics/clients/virgils.json` | Virgil's stub config |
| Create | `Cowork/Skills/client-diagnostics/orchestrator/notion_publisher.py` | Filter image blocks → call notion-create-pages MCP |
| Create | `Cowork/Skills/client-diagnostics/scripts/run_diagnostic.py` | GM-facing CLI: takes `--client <slug>`, finds inputs, runs orchestrator, optionally publishes to Notion |
| Modify | `Cowork/Skills/client-diagnostics/orchestrator/entry.py` | Accept `client_config: ClientConfig` (optional); call input validator before dispatch; emit `charts_manifest.json` listing PNGs needing manual upload |
| Modify | `Cowork/Skills/client-diagnostics/SKILL.md` | Update with Wk 4 GM workflow (CSV input + run + publish + manual chart upload) |
| Create | `Cowork/Skills/client-diagnostics/tests/test_input_schema.py` | Validator tests |
| Create | `Cowork/Skills/client-diagnostics/tests/test_client_config.py` | Config loader tests |
| Create | `Cowork/Skills/client-diagnostics/tests/test_notion_publisher.py` | Block-filtering + MCP-call shape tests (mocked) |

---

## Chunk 1: Input schema + validator + GM-facing template

The pipeline's sub-skills consume a single unified DataFrame today (synthetic CSV). For Wk 4, Maxx + Ro produce that CSV from their existing data sources. We need to: document the schema, validate it on read, fail loudly with helpful errors when columns are missing.

### Tasks

**Task 1.1: `references/input-csv-schema.md`** — single source of truth for the input format.

Document the required columns grouped by sub-skill domain. For each: name, type, units, what to put when value is missing. Include a "filling from platform exports" section linking each column to the relevant platform field.

Key columns (from synthetic test fixture in `test_smoke_e2e_full.py::_synth_csv`):

| Column | Type | Used by | Source |
|---|---|---|---|
| store | string | all | location name (canonical) |
| week | int | topline | week number 1–13 (90-day window) |
| gross_sales | number | topline | sum across platforms for the week |
| orders | int | topline | total orders for the store/week |
| net_payout | number | topline | net payout for the store/week |
| menu_cvr_pct | number | menu | UE menu CVR (impressions → orders), 0–100 |
| photo_coverage_pct | number | menu | % of menu items with photos |
| hero_set | bool | menu | true/false — hero image present |
| categories_count | int | menu | total menu categories |
| categories_populated | int | menu | categories with ≥1 item |
| storefront_to_menu_ctr_pct | number | menu | UE storefront → menu CTR |
| rating | number | ops | platform rating, 0–5 |
| error_rate_pct | number | ops | order error rate, 0–100 |
| cancellation_pct | number | ops | order cancellation rate, 0–100 |
| uptime_pct | number | ops | store uptime, 0–100 |
| hours_accurate | bool | ops | listed hours match actual |
| platform | string | campaigns | UE / DD / GH (per-row) |
| spend | number | campaigns | weekly ad spend per row |
| attributed_sales | number | campaigns | attributed sales from ads |
| roas | number | campaigns | spend / attributed_sales |
| incremental_orders_per_week | number | campaigns | from ads |
| promo_count_active | int | campaigns | active promo count |

**Task 1.2: `references/diagnostic-input-template.csv`** — empty CSV with just the header row, ready for GM to fill.

**Task 1.3: `orchestrator/input_schema.py`** — validator with helpful errors.

```python
from __future__ import annotations
import pandas as pd

REQUIRED_COLUMNS = {
    "store", "week",
    # topline
    "gross_sales", "orders", "net_payout",
    # menu
    "menu_cvr_pct", "photo_coverage_pct", "hero_set",
    "categories_count", "categories_populated", "storefront_to_menu_ctr_pct",
    # ops
    "rating", "error_rate_pct", "cancellation_pct", "uptime_pct", "hours_accurate",
    # campaigns
    "platform", "spend", "attributed_sales", "roas",
    "incremental_orders_per_week", "promo_count_active",
}


class InputSchemaError(ValueError):
    pass


def validate(df: pd.DataFrame) -> None:
    """Raise InputSchemaError with actionable message if df is malformed."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise InputSchemaError(
            f"Diagnostic input CSV is missing required columns: {sorted(missing)}. "
            f"See references/input-csv-schema.md for the full schema. "
            f"Found columns: {sorted(df.columns)}"
        )
    if df.empty:
        raise InputSchemaError("Diagnostic input CSV has no rows. Need at least 1 store × 1 week × 1 platform.")
    # Spot-check a few hard requirements
    if not df["week"].between(1, 13).all():
        raise InputSchemaError("'week' column must be integers 1–13 (90-day window = 13 weeks).")
    if not df["rating"].between(0, 5).all():
        raise InputSchemaError(f"'rating' column has values outside 0–5: min={df['rating'].min()}, max={df['rating'].max()}")
    valid_platforms = {"UE", "DD", "GH"}
    bad_plats = set(df["platform"].unique()) - valid_platforms
    if bad_plats:
        raise InputSchemaError(f"'platform' column has invalid values: {bad_plats}. Must be UE / DD / GH.")
```

**Task 1.4: Wire validator into orchestrator** — `entry.py` calls `input_schema.validate(df)` BEFORE dispatching sub-skills. (Read the inputs CSV once at orchestrator level; pass df-or-path to dispatch helpers — already done via the inputs-dir / CSV-glob pattern.)

Currently each sub-skill subprocess re-reads CSVs from `inputs_dir`. Keep that pattern but add an early validation pass in orchestrator's Phase 1 (pre-flight):

```python
# In entry.run, before Phase 2:
import pandas as pd
from orchestrator import input_schema

csvs = sorted(inputs_dir.glob("*.csv"))
if not csvs:
    raise SystemExit(f"No CSV files found in {inputs_dir}. Drop the diagnostic input CSV here.")
df = pd.concat([pd.read_csv(c) for c in csvs], ignore_index=True)
input_schema.validate(df)  # raises InputSchemaError with actionable message
```

**Task 1.5: Tests** — `tests/test_input_schema.py`:
1. `test_valid_df_passes` — synthetic full-shape df → no exception
2. `test_missing_column_fails_with_named_columns` — drop `rating` → error mentions "rating" by name
3. `test_empty_df_fails`
4. `test_invalid_week_range_fails`
5. `test_invalid_rating_range_fails`
6. `test_invalid_platform_fails`
7. `test_orchestrator_short_circuits_on_invalid_input` — monkey-patch run with bad inputs → orchestrator raises InputSchemaError

**Checkpoint:** 7 new tests passing. Existing 99 still passing. Bad-input runs fail fast with named columns.

---

## Chunk 2: Per-client config registry

Each client has a `clients/<slug>.json` config: Notion target, brand info, threshold overrides, data quirks.

### Tasks

**Task 2.1: `clients/_template.json`**

```json
{
  "client_slug": "<slug>",
  "client_display_name": "<Display Name>",
  "notion": {
    "parent_page_id": "<32-char-uuid-with-dashes-or-without>",
    "_comment": "Find via notion-search; this is the page diagnostic pages get created under (typically the client's wiki/portal page)"
  },
  "brand": {
    "color_primary": null,
    "voice_notes": null
  },
  "thresholds_override": {
    "_comment": "Optional: override defaults from diagnostic-framework.md. Omit to use Spice defaults."
  },
  "data_quirks": [
    "_e.g.: 'No Grubhub presence — leave GH columns empty'"
  ]
}
```

**Task 2.2: `clients/dailys.json`** and **Task 2.3: `clients/virgils.json`**

Pre-populated with `client_slug`, `client_display_name`. Notion parent_page_id left as `null` with comment "FILL-IN: Maxx provides Notion target per client onboarding". Other fields default.

**Task 2.4: `orchestrator/client_config.py`**

```python
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
```

**Task 2.5: Tests** — `tests/test_client_config.py`:
1. `test_load_dailys_config` — config loads, slug="dailys", display_name correct
2. `test_load_virgils_config`
3. `test_load_unknown_client_lists_available` — `load("nonexistent")` → error message lists "dailys", "virgils"
4. `test_template_excluded_from_list_clients` — `_template` not in `list_clients()`
5. `test_notion_parent_page_id_is_null_for_unfilled_clients` — Daily's/Virgil's notion target is None until Maxx fills it

**Checkpoint:** 5 new tests passing. Daily's + Virgil's configs exist, ready for Notion targets.

---

## Chunk 3: Notion publisher (text-only for Wk 4)

Take `notion_blocks.json` + a `ClientConfig`. Filter image blocks (replace each with a paragraph block: `"📊 Chart: <id> — see attached PNG"`). Call `notion-create-pages` MCP to create the diagnostic page under the client's `notion_parent_page_id`. Emit `charts_manifest.json` listing the PNG files the GM needs to manually upload.

### Tasks

**Task 3.1: `orchestrator/notion_publisher.py`**

```python
from __future__ import annotations
import json
from pathlib import Path
from typing import Callable

from orchestrator.client_config import ClientConfig


class NotionPublishError(RuntimeError):
    pass


def filter_image_blocks(blocks: list[dict]) -> tuple[list[dict], list[dict]]:
    """Strip image blocks for text-only publish. Return (filtered_blocks, charts_manifest).

    Each image block becomes a paragraph: '📊 Chart: <id> — see attached PNG (<filename>)'.
    The manifest captures id + path so GM knows what to upload manually.
    """
    out_blocks = []
    manifest = []
    for blk in blocks:
        if blk.get("type") == "image":
            ext = blk.get("image", {}).get("external", {})
            url = ext.get("url", "")
            chart_id = blk.get("_chart_id", "chart")  # if you set this in notion_assembly
            filename = url.rsplit("/", 1)[-1] if url else "chart.png"
            out_blocks.append({
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"📊 Chart: {chart_id} — see attached PNG ({filename})"}}]},
            })
            manifest.append({"chart_id": chart_id, "local_path": url.replace("file://", "") if url.startswith("file://") else url, "filename": filename})
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
      NotionPublishError if config.notion_parent_page_id is None.
    """
    if not config.notion_parent_page_id:
        raise NotionPublishError(
            f"Client '{config.slug}' has no notion_parent_page_id set in clients/{config.slug}.json. "
            f"Run notion-search to find the client's wiki/portal page ID, then update the config."
        )
    filtered, manifest = filter_image_blocks(blocks)
    if create_page_fn is None:
        raise NotionPublishError("create_page_fn must be provided (or call this from an MCP-enabled context)")
    result = create_page_fn(
        parent_page_id=config.notion_parent_page_id,
        title=page_title,
        children=filtered,
    )
    return {"notion_page_url": result.get("url"), "charts_manifest": manifest}
```

**Task 3.2: Tests** — `tests/test_notion_publisher.py`:
1. `test_filter_image_blocks_replaces_with_paragraph` — input with 2 image blocks → output has 2 paragraphs
2. `test_filter_image_blocks_preserves_non_image_blocks` — paragraphs/headings/dividers unchanged
3. `test_filter_image_blocks_emits_manifest` — manifest entries have chart_id, local_path, filename
4. `test_publish_raises_when_notion_target_missing` — config with `notion_parent_page_id=None` → NotionPublishError with helpful message
5. `test_publish_calls_create_page_fn_with_filtered_blocks` — inject a mock create_page_fn; assert called with `parent_page_id=<id>`, `title=<correct>`, `children=<filtered>`
6. `test_publish_returns_notion_page_url_and_manifest` — mock returns `{"url": "https://notion.so/..."}` → result has both fields

**Task 3.3: Wire publisher into orchestrator entry** (optional CLI flag)

In `entry.run`, accept an optional `publish_to_notion: bool = False` flag. When set, after Phase 5 writes `notion_blocks.json`:

```python
if publish_to_notion:
    from orchestrator import notion_publisher
    blocks = json.loads((layout.root / "notion_blocks.json").read_text())
    page_title = f"{config.display_name} | Diagnostics & Action Plan | {window_start} – {window_end}"
    publish_result = notion_publisher.publish(
        blocks=blocks, config=config, page_title=page_title,
        create_page_fn=create_page_fn,  # passed in via DI
    )
    (layout.root / "publish_result.json").write_text(json.dumps(publish_result, indent=2))
```

NOTE: actual MCP wiring (the `create_page_fn` callable) happens in `scripts/run_diagnostic.py` (Chunk 4) where the MCP tool is callable. The orchestrator stays MCP-free for testability.

**Checkpoint:** 6 new publisher tests + ~2 entry tests passing. Total Wk 4 added: ~13 tests.

---

## Chunk 4: GM-facing CLI runner + Daily's/Virgil's smoke harness

Maxx + Ro need a single command they can run: `python run_diagnostic.py --client dailys --inputs-dir <path> [--publish]`. This wraps everything.

### Tasks

**Task 4.1: `scripts/run_diagnostic.py`**

```python
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
from datetime import datetime
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
    start = datetime.fromisoformat(args.window_start) if args.window_start else end.replace(day=end.day) # rough; refine
    # Use simple 90d window for now
    if args.window_start is None:
        from datetime import timedelta
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
```

(Why the script doesn't actually call `notion-create-pages`: Python scripts can't directly invoke MCP tools — those are exposed only inside the Claude session. The script writes the publish payload to disk and prints instructions for the calling Claude session to invoke the MCP. Wk 5 wraps this in a Claude command/skill that does invoke the MCP automatically.)

**Task 4.2: `clients/dailys.json` and `clients/virgils.json` are populated stubs (from Chunk 2)**

**Task 4.3: Smoke harness** — `tests/test_real_data_smoke.py`

```python
"""Real-data smoke tests for Wk 4. Skipped by default; run with REAL_DATA_DIR env var.

Usage:
    REAL_DATA_DIR=/path/to/dailys-q1-exports .venv/bin/pytest tests/test_real_data_smoke.py -v
"""
import os
import pytest
from pathlib import Path

REAL_DATA_DIR = os.environ.get("REAL_DATA_DIR")
SKIP_REASON = "set REAL_DATA_DIR env var to run real-data smoke"


@pytest.mark.skipif(not REAL_DATA_DIR, reason=SKIP_REASON)
def test_real_data_runs_full_pipeline():
    """Drop a directory of real diagnostic_input.csv files; verify pipeline produces all expected artifacts."""
    from orchestrator import entry, output_layout
    from datetime import datetime

    inputs = Path(REAL_DATA_DIR)
    assert inputs.is_dir(), f"REAL_DATA_DIR={inputs} doesn't exist"
    assert any(inputs.glob("*.csv")), f"No CSVs in {inputs}"

    result = entry.run(
        client=os.environ.get("REAL_DATA_CLIENT", "smoke-test"),
        window_start="2026-02-09",
        window_end="2026-05-09",
        inputs_dir=inputs,
        when=datetime.now(),
    )

    # All expected artifacts exist
    assert (result.layout.root / "notion_page.md").exists()
    assert (result.layout.root / "notion_blocks.json").exists()
    assert (result.layout.root / "cross_cutting" / "radar_7dim.png").exists()
    assert (result.layout.root / "cross_cutting" / "tier_donut.png").exists()
    assert (result.layout.root / "cross_cutting" / "top15_green_bar.png").exists()

    # Print path so user can inspect
    print(f"\n✅ Real-data smoke complete. Artifacts: {result.layout.root}")
```

**Task 4.4: Update SKILL.md** — orchestrator-dispatcher SKILL.md needs a "GM Workflow" section:

```markdown
## GM Workflow (Wk 4)

1. **Prepare input CSV.** Download the template at `references/diagnostic-input-template.csv`. Fill in one row per `(store, week, platform)` combo. Schema docs in `references/input-csv-schema.md`. Drop the filled CSV(s) in a directory.

2. **Ensure client config exists.** `clients/<slug>.json` should have `notion_parent_page_id` set to the client's wiki/portal page ID. Create config from `clients/_template.json` if needed.

3. **Run.**
   ```bash
   .venv/bin/python scripts/run_diagnostic.py --client <slug> --inputs-dir <path-to-csv-dir>
   ```
   Artifacts land in `/tmp/diagnostic-runs/<slug>/<timestamp>/`.

4. **Review.** Open `notion_page.md` to read the diagnostic. Check chart PNGs in `cross_cutting/` and per-sub-skill `charts/` subdirs.

5. **Publish to Notion.** Re-run with `--publish` to generate the Notion publish payload. Then in your Claude session, invoke `notion-create-pages` with the printed inputs. Upload chart PNGs manually to the created page.

6. **Hand to client.** Share the Notion page URL.
```

**Checkpoint:** Wk 4 added ~14 tests. Daily's + Virgil's stub configs exist. Smoke harness is parametric, ready for real data.

---

## Chunk 5: Wk 4 verification + deploy

### Verification

```bash
echo "=== Wk 4 full test suite ==="
for skill in client-diagnostics diagnostic-topline diagnostic-menu diagnostic-ops diagnostic-campaigns diagnostic-action-plan; do
  cd /Users/maxx/Desktop/Cowork/Skills/$skill && .venv/bin/pytest tests/ -q 2>&1 | tail -2
done

echo "=== Daily's/Virgil's config sanity ==="
cd /Users/maxx/Desktop/Cowork/Skills/client-diagnostics && .venv/bin/python -c "
from orchestrator import client_config
print('Available clients:', client_config.list_clients())
for c in ('dailys', 'virgils'):
    cfg = client_config.load(c)
    print(f'{c}: {cfg.display_name}, notion target = {cfg.notion_parent_page_id or \"(unset — Maxx fills)\"}')
"

echo "=== End-to-end with synthetic data via run_diagnostic.py ==="
# Sanity check the new CLI runner against synthetic CSV
cd /Users/maxx/Desktop/Cowork/Skills/client-diagnostics
mkdir -p /tmp/wk4-smoke-inputs
.venv/bin/python -c "
import pandas as pd
df = pd.DataFrame({
    'store': ['BeverlyHills']*5,
    'week': [1,2,3,4,5],
    'gross_sales': [12000]*5, 'orders': [240]*5, 'net_payout': [8000]*5,
    'menu_cvr_pct': [22.0]*5, 'photo_coverage_pct': [85]*5, 'hero_set': [True]*5,
    'categories_count': [6]*5, 'categories_populated': [6]*5, 'storefront_to_menu_ctr_pct': [10.0]*5,
    'rating': [4.6]*5, 'error_rate_pct': [1.5]*5, 'cancellation_pct': [1.0]*5, 'uptime_pct': [98.0]*5, 'hours_accurate': [True]*5,
    'platform': ['UE']*5, 'spend': [600]*5, 'attributed_sales': [3000]*5, 'roas': [5.0]*5, 'incremental_orders_per_week': [15]*5, 'promo_count_active': [2]*5,
})
df.to_csv('/tmp/wk4-smoke-inputs/test.csv', index=False)
"
.venv/bin/python scripts/run_diagnostic.py --client dailys --inputs-dir /tmp/wk4-smoke-inputs
```

### Deploy

```bash
for skill in client-diagnostics diagnostic-topline diagnostic-menu diagnostic-ops diagnostic-campaigns diagnostic-action-plan; do
  rsync -a --delete \
    --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
    "/Users/maxx/Desktop/Cowork/Skills/$skill/" \
    "/Users/maxx/Desktop/spice-team-skills/skills/$skill/"
done
```

### Checkpoint

- All ~113 tests passing (99 entering Wk 4 + ~14 added)
- `run_diagnostic.py --client dailys --inputs-dir <synthetic-dir>` produces a valid run
- Daily's + Virgil's stub configs ready for Maxx to fill in Notion targets
- All deployed to team-skills

---

## Critical Files

- This plan: `plans/2026-05-10-orchestrator-wk4-plan.md`
- Spec: `specs/2026-05-08-orchestrator-redesign.md`
- Wk 1/2/3 plans (reference): `plans/2026-05-08-*.md`
- New schema doc: `references/input-csv-schema.md`
- New config registry: `clients/`
- New GM CLI: `scripts/run_diagnostic.py`

---

## What Maxx + Ro need to do before next week's run

After Wk 4 ships:
1. Open `clients/dailys.json` and `clients/virgils.json`. Use `notion-search` to find each client's wiki/portal page ID. Fill `notion_parent_page_id` in each config.
2. Produce one diagnostic input CSV per client, following `references/input-csv-schema.md`. Sources: existing weekly-reporting outputs (transcribe per-store metrics into the unified schema), platform exports, manual storefront audit data.
3. Run `python scripts/run_diagnostic.py --client dailys --inputs-dir <path>` against the prepared CSV folder.
4. Review the markdown output, then re-run with `--publish` to get the Notion publish payload.
5. From the Claude session, invoke the printed `notion-create-pages` call with the payload.
6. Manually upload chart PNGs to the created Notion page (Wk 5 automates this).
