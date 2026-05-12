"""
Diagnostic chart generator for the client-diagnostics skill.

NOTE (Wk 3): This file is preserved as a backup / legacy reference. The
canonical chart functions used by the orchestrator + sub-skills now live at
`orchestrator/chart_helpers.py`. Keep this file intact — it doubles as the
documented JSON metrics schema for chart inputs.

Reads a metrics JSON describing one client's 90-day diagnostic and writes
all PNGs to the output directory. Charts produced match the spec in
references/diagnostic-framework.md (Chart Library section).

Usage:
    python generate_diagnostic_charts.py metrics.json ./out/

metrics.json schema (minimum required fields):
{
  "client": "Tiff's Treats",
  "window": {"start": "2026-02-04", "end": "2026-05-04"},
  "radar": {
    "AOV": {"current": 6, "target": 8},
    "Re-order Rate": {"current": 5, "target": 8},
    "Conversion": {"current": 6, "target": 8},
    "Marketing Efficiency": {"current": 3, "target": 8},
    "Operations": {"current": 5, "target": 9},
    "Traffic": {"current": 4, "target": 8},
    "Campaigns / ROAS": {"current": 6, "target": 8}
  },
  "trend_weekly": {
    "weeks": ["W1", "W2", ..., "W13"],
    "gmv":    [120000, 118000, ...],
    "orders": [4100, 4050, ...],
    "aov":    [29.2, 29.5, ...]
  },
  "tiers": {"Green": 46, "Yellow": 55, "Red": 54, "New": 25,
            "payout_share": {"Green": 0.62, "Yellow": 0.24, "Red": 0.10, "New": 0.04}},
  "funnel_ue": {"Impressions": 19_300_000, "Storefront Views": 1_430_000,
                "Menu Views": 720_000, "Orders": 140_000},
  "top_skus": [{"name": "1 Dozen Cookies", "revenue": 559000}, ...],
  "campaigns": [{"name": "DD DashPass", "spend": 12000, "roas": 9.8,
                 "orders": 3200, "platform": "DD"}, ...],
  "daypart": {"days": ["Mon",...,"Sun"], "hours": [0,...,23],
              "matrix": [[orders_mon_h0, ...], ...]},
  "top15_green": [{"name": "Store X", "payout": 32000, "tier": "Green"}, ...]
}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # noqa: E402
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FuncFormatter

SPICE = {
    "red":      "#B91C1C",
    "charcoal": "#1F2937",
    "sage":     "#84CC16",
    "cream":    "#FEF3C7",
    "amber":    "#F59E0B",
    "blue":     "#2563EB",
    "gray":     "#9CA3AF",
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
    "axes.labelweight": "regular",
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "figure.facecolor": "white",
})


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------

def radar_7dim(metrics: dict, out: Path) -> Path:
    radar = metrics["radar"]
    labels = list(radar.keys())
    current = [radar[k]["current"] for k in labels]
    target = [radar[k]["target"] for k in labels]
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()

    # close polygon
    current_c = current + [current[0]]
    target_c = target + [target[0]]
    angles_c = angles + [angles[0]]

    fig = plt.figure(figsize=(6.5, 6.5))
    ax = fig.add_subplot(111, polar=True)

    ax.fill(angles_c, target_c, color=SPICE["sage"], alpha=0.18, label="Target")
    ax.plot(angles_c, target_c, color=SPICE["sage"], linewidth=1.5,
            linestyle="--", label="_target")

    ax.fill(angles_c, current_c, color=SPICE["red"], alpha=0.4, label="Current")
    ax.plot(angles_c, current_c, color=SPICE["red"], linewidth=2.0)

    ax.set_xticks(angles)
    ax.set_xticklabels(
        [f"{lbl}\n{val}/10" for lbl, val in zip(labels, current)],
        fontsize=10, color=SPICE["charcoal"], fontweight="bold",
    )
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], color=SPICE["gray"], fontsize=8)
    ax.set_ylim(0, 10)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.spines["polar"].set_color(SPICE["gray"])
    ax.grid(color=SPICE["gray"], alpha=0.3)

    overall = round(sum(current) / len(current), 1)
    ax.set_title(f"Brand Health  ·  Overall {overall}/10", pad=24,
                 color=SPICE["charcoal"], fontsize=14)

    # legend
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.10), frameon=False)

    path = out / "radar_7dim.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def sparklines_gmv_orders(metrics: dict, out: Path) -> Path:
    trend = metrics["trend_weekly"]
    weeks = trend["weeks"]
    n = len(weeks)
    last4_start = max(0, n - 4)

    # (name, values, formatter, aggregator) — sum for cumulative metrics, mean for rates
    # AOV intentionally omitted from sparklines: it lives in the hero stat strip.
    series = [
        ("GMV", trend["gmv"], lambda v: f"${v/1000:.0f}K", "sum"),
        ("Orders", trend["orders"], lambda v: f"{v:,.0f}", "sum"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(7.5, 2.2))

    def agg(vals_slice, mode):
        if not vals_slice:
            return 0
        return sum(vals_slice) if mode == "sum" else sum(vals_slice) / len(vals_slice)

    for ax, (name, vals, fmt, mode) in zip(axes, series):
        x = np.arange(n)
        # shaded last 4 weeks
        ax.axvspan(last4_start, n - 1, color=SPICE["cream"], alpha=0.7, zorder=0)
        ax.plot(x, vals, color=SPICE["red"], linewidth=2)
        ax.fill_between(x, vals, min(vals), color=SPICE["red"], alpha=0.15)

        # delta last4 vs prior4
        prior = agg(vals[max(0, n-8):max(0, n-4)], mode) or 1
        last = agg(vals[max(0, n-4):n], mode)
        delta_pct = (last - prior) / prior * 100
        delta_color = SPICE["sage"] if delta_pct >= 0 else SPICE["red"]
        delta_str = f"{delta_pct:+.1f}%"

        ax.set_title(f"{name}  ·  {fmt(last)}", fontsize=11,
                     color=SPICE["charcoal"], loc="left")
        ax.text(0.99, 0.95, delta_str, transform=ax.transAxes,
                ha="right", va="top", color=delta_color, fontweight="bold",
                fontsize=11)

        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)

    fig.suptitle("90-Day Trend  ·  last 4 weeks shaded", y=1.05,
                 fontsize=10, color=SPICE["gray"])
    path = out / "sparklines_gmv_orders.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def tier_donut(metrics: dict, out: Path) -> Path:
    t = metrics["tiers"]
    order = ["Green", "Yellow", "Red", "New"]
    counts = [t.get(k, 0) for k in order]
    payout = t.get("payout_share", {})
    total = sum(counts) or 1

    color_map = {"Green": SPICE["sage"], "Yellow": SPICE["amber"],
                 "Red": SPICE["red"], "New": SPICE["blue"]}
    colors = [color_map[k] for k in order]

    fig, ax = plt.subplots(figsize=(5, 5))
    wedges, _ = ax.pie(counts, colors=colors, startangle=90,
                       wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2))

    ax.text(0, 0.05, f"{total}", ha="center", va="center",
            fontsize=28, fontweight="bold", color=SPICE["charcoal"])
    ax.text(0, -0.18, "stores", ha="center", va="center",
            fontsize=11, color=SPICE["gray"])

    legend_labels = []
    for k, c in zip(order, counts):
        share = payout.get(k, 0) * 100
        legend_labels.append(f"{k}: {c} stores · {share:.0f}% of payout")
    ax.legend(wedges, legend_labels, loc="center left",
              bbox_to_anchor=(1.05, 0.5), frameon=False, fontsize=10)

    ax.set_title("Location Tier Health", color=SPICE["charcoal"], pad=18)
    path = out / "tier_donut.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def funnel_ue(metrics: dict, out: Path) -> Path:
    f = metrics["funnel_ue"]
    stages = list(f.keys())
    vals = list(f.values())
    n = len(stages)

    fig, ax = plt.subplots(figsize=(8, 4))
    y = np.arange(n)[::-1]

    # bars normalized to widest = 1
    widest = max(vals)
    widths = [v / widest for v in vals]

    for i, (stage, val, w) in enumerate(zip(stages, vals, widths)):
        yi = y[i]
        ax.barh(yi, w, height=0.65, color=SPICE["red"], alpha=0.85,
                edgecolor="white", linewidth=1.5)
        ax.text(w + 0.02, yi, f"{val:,.0f}", va="center", fontsize=11,
                color=SPICE["charcoal"], fontweight="bold")
        if i > 0:
            prev = vals[i - 1]
            keep = val / prev * 100 if prev else 0
            drop = 100 - keep
            ax.text(0.5, yi + 0.5, f"↓ {drop:.1f}% drop  ·  {keep:.1f}% kept",
                    ha="center", va="center", fontsize=9, color=SPICE["gray"])

    ax.set_yticks(y)
    ax.set_yticklabels(stages, fontsize=11)
    ax.set_xticks([])
    ax.set_xlim(0, 1.25)
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(SPICE["gray"])
    ax.set_title("UE Conversion Funnel · 90 days", loc="left",
                 color=SPICE["charcoal"])
    path = out / "funnel_ue.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def top_skus_bar(metrics: dict, out: Path) -> Path:
    skus = metrics["top_skus"][:10]
    names = [s["name"] for s in skus][::-1]
    rev = [s["revenue"] for s in skus][::-1]
    total = sum(rev) or 1

    fig, ax = plt.subplots(figsize=(7, 5))
    # gradient charcoal -> red by share
    shares = [r / max(rev) for r in rev]
    cmap_colors = [
        (1 - sh) * np.array([0.12, 0.16, 0.22]) + sh * np.array([0.73, 0.11, 0.11])
        for sh in shares
    ]

    ax.barh(names, rev, color=cmap_colors, edgecolor="white", linewidth=1)
    for i, (n, r) in enumerate(zip(names, rev)):
        pct = r / total * 100
        ax.text(r + max(rev) * 0.01, i, f"${r/1000:.0f}K  ·  {pct:.0f}%",
                va="center", fontsize=10, color=SPICE["charcoal"])

    ax.set_xticks([])
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(SPICE["gray"])
    ax.set_title("Top 10 SKUs · 90-day combined revenue", loc="left",
                 color=SPICE["charcoal"])
    ax.set_xlim(0, max(rev) * 1.25)
    path = out / "top_skus_bar.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def campaign_2x2(metrics: dict, out: Path) -> Path:
    camps = metrics["campaigns"]
    fig, ax = plt.subplots(figsize=(8, 6))

    platform_color = {"UE": SPICE["sage"], "DD": SPICE["red"], "GH": SPICE["blue"]}

    spends = [c["spend"] for c in camps]
    roas = [c["roas"] for c in camps]
    orders = [c["orders"] for c in camps]
    colors = [platform_color.get(c.get("platform", ""), SPICE["gray"]) for c in camps]
    sizes = [max(60, o / max(orders) * 1200) for o in orders] if orders else [60] * len(camps)

    ax.scatter(spends, roas, s=sizes, c=colors, alpha=0.6, edgecolor="white",
               linewidth=1.5)

    median_spend = float(np.median(spends)) if spends else 0
    ax.axhline(3.5, color=SPICE["gray"], linewidth=1, linestyle="--", alpha=0.6)
    ax.axvline(median_spend, color=SPICE["gray"], linewidth=1, linestyle="--", alpha=0.6)

    # quadrant labels
    xmax = max(spends) * 1.1 if spends else 1
    ymax = max(roas) * 1.1 if roas else 5
    ax.text(0.02, 0.97, "INVEST MORE", transform=ax.transAxes, ha="left", va="top",
            fontsize=10, color=SPICE["sage"], fontweight="bold", alpha=0.7)
    ax.text(0.98, 0.97, "SCALE", transform=ax.transAxes, ha="right", va="top",
            fontsize=10, color=SPICE["sage"], fontweight="bold", alpha=0.7)
    ax.text(0.02, 0.04, "FIX OR KILL", transform=ax.transAxes, ha="left", va="bottom",
            fontsize=10, color=SPICE["red"], fontweight="bold", alpha=0.7)
    ax.text(0.98, 0.04, "OVER-SPEND", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=10, color=SPICE["amber"], fontweight="bold", alpha=0.7)

    for c in camps:
        ax.annotate(c["name"], (c["spend"], c["roas"]),
                    xytext=(5, 5), textcoords="offset points",
                    fontsize=8, color=SPICE["charcoal"])

    ax.set_xlabel("Spend ($)")
    ax.set_ylabel("ROAS (x)")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v/1000:.0f}K"))
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.set_title("Campaign Efficiency  ·  ROAS × Spend (bubble = orders)",
                 loc="left", color=SPICE["charcoal"])

    # platform legend
    handles = [plt.scatter([], [], s=80, color=col, label=p)
               for p, col in platform_color.items()]
    ax.legend(handles=handles, loc="upper left", frameon=False,
              bbox_to_anchor=(0, 0.94))

    path = out / "campaign_2x2.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def daypart_heatmap(metrics: dict, out: Path) -> Path:
    dp = metrics["daypart"]
    days = dp["days"]
    hours = dp["hours"]
    matrix = np.array(dp["matrix"], dtype=float)

    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "spice_heat", [SPICE["cream"], SPICE["red"]], N=256)

    fig, ax = plt.subplots(figsize=(12, 4))
    im = ax.imshow(matrix, cmap=cmap, aspect="auto")

    ax.set_xticks(range(len(hours)))
    ax.set_xticklabels(hours)
    ax.set_yticks(range(len(days)))
    ax.set_yticklabels(days)

    # annotate each cell when matrix small enough
    if matrix.size <= 24 * 7:
        vmax = matrix.max() or 1
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                v = matrix[i, j]
                if v <= 0:
                    continue
                color = "white" if v > vmax * 0.55 else SPICE["charcoal"]
                ax.text(j, i, f"{int(v)}", ha="center", va="center",
                        fontsize=7, color=color)

    ax.set_title("Order Density by Daypart · UE + DD blended (90d)", loc="left",
                 color=SPICE["charcoal"])
    ax.set_xlabel("Hour")
    fig.colorbar(im, ax=ax, label="Orders")

    path = out / "daypart_heatmap.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def top15_green_bar(metrics: dict, out: Path) -> Path:
    stores = metrics.get("top15_green", [])[:15]
    if not stores:
        return None  # type: ignore
    names = [s["name"] for s in stores][::-1]
    payouts = [s["payout"] for s in stores][::-1]
    tiers = [s.get("tier", "Green") for s in stores][::-1]

    color_map = {"Green": SPICE["sage"], "Yellow": SPICE["amber"]}
    colors = [color_map.get(t, SPICE["sage"]) for t in tiers]

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(names, payouts, color=colors, edgecolor="white", linewidth=1)
    for i, p in enumerate(payouts):
        ax.text(p + max(payouts) * 0.01, i, f"${p/1000:,.0f}K",
                va="center", fontsize=10, color=SPICE["charcoal"])

    ax.set_xticks([])
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(SPICE["gray"])
    ax.set_title("Top 15 Green Stores · 90-day net payout", loc="left",
                 color=SPICE["charcoal"])
    ax.set_xlim(0, max(payouts) * 1.18)

    path = out / "top15_green_bar.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------

CHART_BUILDERS = [
    ("radar_7dim", radar_7dim),
    ("sparklines_gmv_orders", sparklines_gmv_orders),
    ("tier_donut", tier_donut),
    ("funnel_ue", funnel_ue),
    ("top_skus_bar", top_skus_bar),
    ("campaign_2x2", campaign_2x2),
    ("daypart_heatmap", daypart_heatmap),
    ("top15_green_bar", top15_green_bar),
]


def main(metrics_path: str, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(metrics_path) as f:
        metrics = json.load(f)

    written = []
    for name, fn in CHART_BUILDERS:
        try:
            p = fn(metrics, out)
            if p is not None:
                written.append(str(p))
                print(f"[ok] {name} -> {p}")
        except KeyError as e:
            print(f"[skip] {name}: missing key {e}")
        except Exception as e:
            print(f"[error] {name}: {e}")

    print(f"\nWrote {len(written)} chart(s) to {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: generate_diagnostic_charts.py <metrics.json> <out_dir>")
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
