"""Canonical chart generator for the client-diagnostics report.

ONE chart module. Reads ``metrics.json`` from a run directory and writes
PNGs into ``<run_dir>/charts/`` that ``build_report.py`` base64-inlines.

Canonical charts:
  - radar_7dim.png       0-10 scale, target ring, overall = mean of MEASURED
                         axes only. A pending axis (current is None / has
                         "pending": true) renders at 0 with a "(pending)"
                         tick and is EXCLUDED from the overall.
  - tier_donut.png       per-store performance wedges coloured by their
                         Green/Yellow/Red/New tier ("Baseline Location Tiers
                         (pre-Spice)"); falls back to aggregate tier counts
                         when metrics.tiers.by_store is absent.
  - top15_green_bar.png  stores ranked by the supplied size metric
                         (gmv or payout), with the tier badge rendered
                         inside each bar end ("Blended 90-Day GMV by Store").

Optional charts (rendered only when their metrics key is present; no-op
cleanly when absent, exactly like trend/daypart):
  - funnel_ue.png        stepped conversion funnel from metrics.funnel
                         (stages/values), with stage-to-stage drop-off %.
  - storefront_audit.png score/100 bar from metrics.storefront_audit
                         (listings + portfolio_avg), coloured by grade.

Deliberately skipped when the data isn't real (printed honestly, never
fabricated):
  - trend_overlay.png    when metrics.trend_weekly is absent
  - daypart_heatmap.png  when metrics.daypart is absent
  - funnel_ue.png        when metrics.funnel is absent
  - storefront_audit.png when metrics.storefront_audit is absent

Every caption / callout string is sourced from metrics.json — there are
ZERO per-client literals in this module (enforced by
tests/test_report_conformance.py).

Usage:
    python make_charts.py [RUN_DIR]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# Spice brand palette — canonical across all diagnostic charts.
SPICE = {
    "orange": "#FF4A1C",
    "red": "#B91C1C",
    "yellow": "#EAB308",
    "green": "#84CC16",
    "blue": "#2563EB",
    "charcoal": "#1F2937",
    "cream": "#FEF3C7",
    "gray": "#9CA3AF",
}
TIER_COLOR = {
    "Red": SPICE["red"],
    "Yellow": SPICE["yellow"],
    "Green": SPICE["green"],
    "New": SPICE["blue"],
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelcolor": SPICE["charcoal"],
    "xtick.color": SPICE["charcoal"],
    "ytick.color": SPICE["charcoal"],
    "axes.edgecolor": SPICE["charcoal"],
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "figure.facecolor": "white",
})


def radar_7dim(m: dict, charts: Path) -> Path:
    radar = m["radar"]
    labels = list(radar.keys())
    measured = [radar[k]["current"] for k in labels
                if radar[k].get("current") is not None
                and not radar[k].get("pending")]
    current = [(radar[k]["current"] if radar[k].get("current") is not None
                else 0.0) for k in labels]
    target = [radar[k]["target"] for k in labels]
    pending = [radar[k].get("current") is None or radar[k].get("pending", False)
               for k in labels]
    n = len(labels)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    cur_c, tgt_c, ang_c = current + [current[0]], target + [target[0]], ang + [ang[0]]

    fig = plt.figure(figsize=(6.5, 6.5))
    ax = fig.add_subplot(111, polar=True)
    ax.fill(ang_c, tgt_c, color=SPICE["green"], alpha=0.18, label="Target")
    ax.plot(ang_c, tgt_c, color=SPICE["green"], lw=1.5, ls="--")
    ax.fill(ang_c, cur_c, color=SPICE["red"], alpha=0.40, label="Current")
    ax.plot(ang_c, cur_c, color=SPICE["red"], lw=2.0)

    tick_labels = []
    for lab, val, pend in zip(labels, current, pending):
        tick_labels.append(f"{lab}\n(pending)" if pend else f"{lab}\n{val:g}/10")
    ax.set_xticks(ang)
    ax.set_xticklabels(tick_labels, fontsize=9.5,
                       color=SPICE["charcoal"], fontweight="bold")
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"],
                       color=SPICE["gray"], fontsize=8)
    ax.set_ylim(0, 10)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.spines["polar"].set_color(SPICE["gray"])
    ax.grid(color=SPICE["gray"], alpha=0.3)
    overall = round(sum(measured) / len(measured), 1) if measured else 0.0
    ax.set_title(f"Brand Health  ·  Overall {overall}/10", pad=24,
                 color=SPICE["charcoal"], fontsize=14)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.10), frameon=False)
    out = charts / "radar_7dim.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def tier_donut(m: dict, charts: Path) -> Path:
    t = m.get("tiers", {})
    by_store = list(t.get("by_store", {}).items())
    fig, ax = plt.subplots(figsize=(5.4, 5))
    if by_store:
        total = len(by_store)
        wedges, _ = ax.pie(
            [1] * len(by_store),
            colors=[TIER_COLOR.get(tr, SPICE["gray"]) for _, tr in by_store],
            startangle=90,
            wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
        )
        legend = [f"{s} → {tr}" for s, tr in by_store]
        ax.legend(wedges, legend, loc="center left",
                  bbox_to_anchor=(1.05, 0.5), frameon=False, fontsize=10)
    else:
        order = ["Green", "Yellow", "Red", "New"]
        counts = [(k, t.get(k, 0)) for k in order if t.get(k, 0)]
        total = sum(c for _, c in counts) or 1
        wedges, _ = ax.pie(
            [c for _, c in counts],
            colors=[TIER_COLOR[k] for k, _ in counts],
            startangle=90,
            wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
        )
        ax.legend(wedges, [f"{k}: {c}" for k, c in counts],
                  loc="center left", bbox_to_anchor=(1.05, 0.5),
                  frameon=False, fontsize=10)
    ax.text(0, 0.05, f"{total}", ha="center", va="center",
            fontsize=28, fontweight="bold", color=SPICE["charcoal"])
    ax.text(0, -0.18, "stores", ha="center", va="center",
            fontsize=11, color=SPICE["gray"])
    ax.set_title("Baseline Location Tiers (pre-Spice)",
                 color=SPICE["charcoal"], pad=18)
    out = charts / "tier_donut.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def top15_green_bar(m: dict, charts: Path) -> "Path | None":
    """Stores ranked by the supplied size metric. Each bar carries its own
    tier badge inside the bar end — no separate legend, no 'underlying tier'
    language. Title/subtitle are metrics-driven (fall back to neutral
    defaults); there are no per-client literals here."""
    stores = m.get("top15_green", [])
    if not stores:
        return None
    size_key = "gmv" if "gmv" in stores[0] else "payout"
    cfg = m.get("top15_green_meta", {})
    title = cfg.get("title", "Blended 90-Day GMV by Store")
    subtitle = cfg.get("subtitle",
                        "Bar colour = baseline performance tier (pre-Spice)")
    # rank desc; barh plots bottom-up so sort asc for top-down visual order
    stores = sorted(stores, key=lambda s: s.get(size_key, 0))
    names = [s["name"] for s in stores]
    vals = [s.get(size_key, 0) for s in stores]
    tiers = [s.get("tier", "") for s in stores]
    colors = [TIER_COLOR.get(t, SPICE["gray"]) for t in tiers]
    vmax = max(vals) if vals else 1

    fig, ax = plt.subplots(figsize=(8.4, 0.95 * len(stores) + 1.6))
    bars = ax.barh(names, vals, color=colors, height=0.62,
                   edgecolor="none", zorder=3)
    ax.bar_label(bars, labels=[f"${v:,.0f}" for v in vals], padding=10,
                 fontsize=12, fontweight="bold", color=SPICE["charcoal"])
    for i, (v, t) in enumerate(zip(vals, tiers)):
        if not t:
            continue
        ax.text(v - vmax * 0.012, i, str(t).upper(), va="center", ha="right",
                fontsize=9.5, fontweight="bold", color="white", zorder=4)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=12, color=SPICE["charcoal"])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlim(0, vmax * 1.18)
    ax.set_ylim(-0.6, len(stores) - 0.4)
    ax.set_title(title, loc="left", color=SPICE["charcoal"], fontsize=14,
                 fontweight="bold", pad=14)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=10,
            color=SPICE["gray"])
    fig.tight_layout()
    out = charts / "top15_green_bar.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def funnel_ue(m: dict, charts: Path) -> "Path | None":
    """Stepped conversion funnel from metrics.funnel. Stage-to-stage
    conversion % auto-computed. An optional metrics.funnel.caption string
    (data-supplied, never hardcoded) renders below the funnel. No-ops
    cleanly when metrics.funnel is absent."""
    f = m.get("funnel")
    if not f or not f.get("stages") or not f.get("values"):
        return None
    stages, vals = f["stages"], f["values"]
    title = f.get("title", "Conversion Funnel — 90d blended")
    caption = f.get("caption", "")
    vmax = vals[0] or 1
    band = ["#FDBA74", "#FB923C", SPICE["orange"], SPICE["red"]]
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    for i, (s, v) in enumerate(zip(stages, vals)):
        w = (v / vmax) if vmax else 0
        ax.barh(len(stages) - 1 - i, w, height=0.62, left=(1 - w) / 2,
                color=band[i % len(band)], edgecolor="none", zorder=3)
        ax.text(0.5, len(stages) - 1 - i, f"{s}   {v:,}",
                ha="center", va="center", color="white",
                fontsize=12, fontweight="bold", zorder=4)
        if i and vals[i - 1]:
            rate = vals[i] / vals[i - 1] * 100
            ax.text(1.02, len(stages) - 1 - i + 0.5, f"↓ {rate:.1f}%",
                    ha="left", va="center", fontsize=10, color=SPICE["gray"])
    ax.set_xlim(-0.05, 1.18)
    ax.set_ylim(-0.5, len(stages) - 0.4)
    ax.axis("off")
    ax.set_title(title, loc="left", color=SPICE["charcoal"],
                 fontsize=14, pad=12)
    if caption:
        ax.text(-0.05, -0.42, caption, transform=ax.transAxes,
                fontsize=9.5, color=SPICE["gray"], wrap=True)
    out = charts / "funnel_ue.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def storefront_audit(m: dict, charts: Path) -> "Path | None":
    """Listings scored /100 from metrics.storefront_audit, coloured by
    grade, with a portfolio-average reference line. Subtitle is
    data-supplied (no per-client literals). No-ops cleanly when
    metrics.storefront_audit is absent."""
    sa = m.get("storefront_audit")
    if not sa or not sa.get("listings"):
        return None
    rows = sorted(sa["listings"], key=lambda r: r[1])  # worst at bottom-up
    names = [r[0] for r in rows]
    scores = [r[1] for r in rows]
    grade_c = {"Good": SPICE["green"], "Fair": SPICE["yellow"],
               "Poor": SPICE["red"]}
    colors = [grade_c.get(r[2] if len(r) > 2 else "", SPICE["gray"])
              for r in rows]
    title = sa.get("title", "Storefront Audit — score / 100")
    subtitle = sa.get("subtitle",
                       "Green = Good · Amber = Fair · Red = Poor")
    fig, ax = plt.subplots(figsize=(8.6, max(3.2, 0.7 * len(names) + 1.6)))
    bars = ax.barh(names, scores, color=colors, height=0.6, zorder=3)
    ax.bar_label(
        bars,
        labels=[f"{s}  ·  {r[2] if len(r) > 2 else ''}"
                for s, r in zip(scores, rows)],
        padding=8, fontsize=11, fontweight="bold", color=SPICE["charcoal"])
    avg = sa.get("portfolio_avg")
    if avg is not None:
        ax.axvline(avg, color=SPICE["charcoal"], ls="--", lw=1.2, zorder=2)
        ax.text(avg + 0.6, len(names) - 0.35, f"portfolio avg {avg}",
                fontsize=9.5, color=SPICE["charcoal"])
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis="y", length=0)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.set_title(title, loc="left", color=SPICE["charcoal"],
                 fontsize=14, pad=12)
    ax.text(0, 1.04, subtitle, transform=ax.transAxes,
            fontsize=9.5, color=SPICE["gray"])
    out = charts / "storefront_audit.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def generate(run_dir: Path) -> list[Path]:
    m = json.loads((run_dir / "metrics.json").read_text())
    charts = run_dir / "charts"
    charts.mkdir(exist_ok=True)
    made = [radar_7dim(m, charts), tier_donut(m, charts)]
    for fn in (top15_green_bar, funnel_ue, storefront_audit):
        p = fn(m, charts)
        if p:
            made.append(p)
    skipped = []
    if not m.get("trend_weekly"):
        skipped.append("trend_overlay.png (no weekly series in parsed data)")
    if not m.get("daypart"):
        skipped.append("daypart_heatmap.png (no hour×day matrix in parsed data)")
    if not m.get("funnel"):
        skipped.append("funnel_ue.png (no conversion funnel in parsed data)")
    if not m.get("storefront_audit"):
        skipped.append(
            "storefront_audit.png (no storefront audit in parsed data)")
    print(f"charts written to {charts}")
    for s in skipped:
        print(f"  skipped (honest, not fabricated): {s}")
    return made


def main(argv) -> int:
    run_dir = Path(argv[1]).resolve() if len(argv) > 1 \
        else Path(__file__).parent
    generate(run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
