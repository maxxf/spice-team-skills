"""Canonical chart generator for the client-diagnostics report.

ONE chart module. Reads ``metrics.json`` from a run directory and writes
PNGs into ``<run_dir>/charts/`` that ``build_report.py`` base64-inlines.

Canonical charts:
  - radar_7dim.png       0-10 scale, target ring, overall = mean of MEASURED
                         axes only. A pending axis (current is None / has
                         "pending": true) renders at 0 with a "(pending)"
                         tick and is EXCLUDED from the overall.
  - tier_donut.png       performance-tier donut. If metrics.tiers.by_store is
                         present, one wedge per store coloured by its
                         Green/Yellow/Red/New tier; else falls back to
                         aggregate tier counts.
  - top15_green_bar.png  stores ranked by the supplied size metric
                         (gmv or payout), coloured by tier.

Deliberately skipped when the data isn't real (printed honestly, never
fabricated):
  - trend_overlay.png    when metrics.trend_weekly is absent
  - daypart_heatmap.png  when metrics.daypart is absent

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


def top15_green_bar(m: dict, charts: Path) -> Path | None:
    stores = m.get("top15_green", [])
    if not stores:
        return None
    size_key = "gmv" if "gmv" in stores[0] else "payout"
    names = [s["name"] for s in stores][::-1]
    vals = [s.get(size_key, 0) for s in stores][::-1]
    tiers = [s.get("tier", "New") for s in stores][::-1]
    colors = [TIER_COLOR.get(t, SPICE["gray"]) for t in tiers]

    fig, ax = plt.subplots(figsize=(8, max(4.6, len(names) * 0.42)))
    ax.barh(names, vals, color=colors, edgecolor="white", linewidth=1)
    for i, p in enumerate(vals):
        ax.text(p + max(vals) * 0.01, i, f"${p:,.0f}", va="center",
                fontsize=10, color=SPICE["charcoal"])
    ax.set_xticks([])
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(SPICE["gray"])
    ax.set_title("Stores · 90-day blended GMV (coloured by tier)",
                 loc="left", color=SPICE["charcoal"])
    ax.set_xlim(0, max(vals) * 1.20)
    present = [t for t in ["Green", "Yellow", "Red", "New"] if t in set(tiers)]
    handles = [plt.Rectangle((0, 0), 1, 1, color=TIER_COLOR[t]) for t in present]
    ax.legend(handles, present, loc="lower right", frameon=False, fontsize=10)
    out = charts / "top15_green_bar.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def generate(run_dir: Path) -> list[Path]:
    m = json.loads((run_dir / "metrics.json").read_text())
    charts = run_dir / "charts"
    charts.mkdir(exist_ok=True)
    made = [radar_7dim(m, charts), tier_donut(m, charts)]
    bar = top15_green_bar(m, charts)
    if bar:
        made.append(bar)
    skipped = []
    if not m.get("trend_weekly"):
        skipped.append("trend_overlay.png (no weekly series in parsed data)")
    if not m.get("daypart"):
        skipped.append("daypart_heatmap.png (no hour×day matrix in parsed data)")
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
