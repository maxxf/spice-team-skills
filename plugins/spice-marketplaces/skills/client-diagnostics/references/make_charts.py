"""Canonical chart generator for the client-diagnostics report.

ONE chart module. Reads ``metrics.json`` from a run directory and writes
PNGs into ``<run_dir>/charts/`` that ``build_report.py`` base64-inlines.

Canonical charts (always attempted):
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
                         inside each bar end.

Optional charts (rendered ONLY when their metrics key is present; every
one no-ops cleanly + honestly when its key is absent — nothing fabricated):
  - funnel_ue.png        from metrics.funnel (stages/values) — left-aligned
                         bars, counts/% OUTSIDE bars (survives big dynamic
                         range), stage-to-stage drop-off %.
  - storefront_audit.png score/100 bars from metrics.storefront_audit
                         (listings + portfolio_avg), coloured by grade.
  - trend_overlay.png    from metrics.trend_weekly — REAL weekly GMV bars +
                         orders line (twin axis). Derived upstream from
                         per-order DD/GH transaction exports.
  - daypart_heatmap.png  from metrics.daypart — REAL 7×24 order-count imshow
                         heatmap, peak cell ringed. Derived upstream from
                         per-order DD/GH transaction exports.

trend_overlay + daypart_heatmap are DERIVABLE whenever per-order
transaction exports exist (DoorDash financial transactions with a local
timestamp; Grubhub finance with order date + hour). They are only skipped
when the per-order series is genuinely absent — never marked "deferred"
when the source data is present.

Title / subtitle convention — STANDARDIZED across EVERY chart fn so the
title↔subtitle collision bug (hit 3× on the live run) cannot recur:
  * title  → ``fig.suptitle(text, x=0.02, ha="left", y=0.97)``
  * subtitle → ``fig.text(0.02, <margin_y>, text)``
  * room reserved via ``fig.subplots_adjust(top=...)``
NEVER ``ax.set_title`` + ``ax.text(transAxes, y≈1.0x)`` (that overlaps).

Every caption / callout / title string is sourced from metrics.json — there
are ZERO per-client literals in this module (enforced by
tests/test_report_conformance.py::test_no_per_client_literal_bleed_in_chart_source).

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


# --------------------------------------------------------------------------- #
# Shared title/subtitle helper — the ONE place the title pattern lives.        #
# Title in the figure margin via suptitle; subtitle via fig.text just below.   #
# Never ax.set_title + ax.text(transAxes) (that's the collision bug).          #
# --------------------------------------------------------------------------- #

def _titles(fig, title: str, subtitle: str = "",
            *, title_y: float = 0.97, sub_y: float = 0.885) -> None:
    if title:
        fig.suptitle(title, x=0.02, ha="left", y=title_y, fontsize=14,
                     fontweight="bold", color=SPICE["charcoal"])
    if subtitle:
        fig.text(0.02, sub_y, subtitle, fontsize=9.5, color=SPICE["gray"])


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
    overall = round(sum(measured) / len(measured), 1) if measured else 0.0

    fig = plt.figure(figsize=(6.5, 6.8))
    fig.subplots_adjust(top=0.84)
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
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.10), frameon=False)
    cfg = m.get("radar_meta", {})
    _titles(fig,
            cfg.get("title", f"Brand Health  ·  Overall {overall}/10"),
            cfg.get("subtitle", ""), title_y=0.965, sub_y=0.905)
    out = charts / "radar_7dim.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def tier_donut(m: dict, charts: Path) -> Path:
    t = m.get("tiers", {})
    by_store = list(t.get("by_store", {}).items())
    cfg = m.get("tier_donut_meta", {})
    fig, ax = plt.subplots(figsize=(5.4, 5.2))
    fig.subplots_adjust(top=0.80)
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
    _titles(fig, cfg.get("title", "Baseline Location Tiers (pre-Spice)"),
            cfg.get("subtitle", ""), title_y=0.965, sub_y=0.905)
    out = charts / "tier_donut.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def top15_green_bar(m: dict, charts: Path) -> "Path | None":
    """Stores ranked by the supplied size metric. Each bar carries its own
    tier badge inside the bar end — no separate legend. Title/subtitle are
    metrics-driven (neutral defaults); no per-client literals."""
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

    fig, ax = plt.subplots(figsize=(9.0, 0.95 * len(stores) + 2.0))
    fig.subplots_adjust(left=0.22, right=0.96, top=0.78, bottom=0.10)
    bars = ax.barh(names, vals, color=colors, height=0.58,
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
    ax.set_xlim(0, vmax * 1.20)
    ax.set_ylim(-0.6, len(stores) - 0.4)
    _titles(fig, title, subtitle, title_y=0.97, sub_y=0.88)
    out = charts / "top15_green_bar.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def funnel_ue(m: dict, charts: Path) -> "Path | None":
    """Conversion funnel from metrics.funnel. Left-aligned bars; stage
    labels are y-ticks and counts/percentages sit OUTSIDE the bars so a
    large dynamic range (e.g. a 100×+ collapse) stays readable.
    Stage-to-stage conversion % auto-computed. Optional data-supplied
    metrics.funnel.title/caption. No-ops cleanly when absent."""
    f = m.get("funnel")
    if not f or not f.get("stages") or not f.get("values"):
        return None
    stages, vals = f["stages"], f["values"]
    vmax = vals[0] or 1
    title = f.get("title", "Conversion Funnel — 90d blended")
    caption = f.get("caption", "")
    n = len(stages)
    band = ["#FDBA74", "#FB923C", SPICE["orange"], SPICE["red"]]
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    fig.subplots_adjust(left=0.20, right=0.96, top=0.82, bottom=0.22)
    ys = list(range(n))[::-1]  # stage 0 at top
    for i, (s, v, y) in enumerate(zip(stages, vals, ys)):
        ax.barh(y, v, height=0.58, color=band[i % len(band)],
                edgecolor="none", zorder=3)
        pct_of_top = v / vmax * 100
        ax.text(vmax * 1.01, y, f"{v:,}   ({pct_of_top:.1f}% of top)",
                ha="left", va="center", fontsize=11,
                fontweight="bold", color=SPICE["charcoal"], zorder=4)
        if i and vals[i - 1]:
            step = vals[i] / vals[i - 1] * 100
            ax.text(-vmax * 0.02, y + 0.5, f"↓ {step:.1f}%",
                    ha="right", va="center", fontsize=9.5,
                    color=SPICE["gray"])
    ax.set_yticks(ys)
    ax.set_yticklabels(stages, fontsize=11, fontweight="bold",
                       color=SPICE["charcoal"])
    ax.set_xlim(0, vmax * 1.34)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0)
    for sp in ("top", "right", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color(SPICE["gray"])
    _titles(fig, title, caption, title_y=0.97, sub_y=0.06)
    out = charts / "funnel_ue.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def storefront_audit(m: dict, charts: Path) -> "Path | None":
    """Listings scored /100 from metrics.storefront_audit, coloured by
    grade, with a portfolio-average reference marker labelled at the
    x-axis (no title collision). Subtitle is data-supplied. No-ops
    cleanly when absent."""
    sa = m.get("storefront_audit")
    if not sa or not sa.get("listings"):
        return None
    rows = sorted(sa["listings"], key=lambda r: r[1])  # worst at bottom
    names = [r[0] for r in rows]
    scores = [r[1] for r in rows]
    grade_c = {"Good": SPICE["green"], "Fair": SPICE["yellow"],
               "Poor": SPICE["red"]}
    colors = [grade_c.get(r[2] if len(r) > 2 else "", SPICE["gray"])
              for r in rows]
    title = sa.get("title", "Storefront Audit — score / 100")
    subtitle = sa.get("subtitle",
                       "Green = Good · Amber = Fair · Red = Poor")
    fig, ax = plt.subplots(figsize=(9.2, max(3.4, 0.7 * len(names) + 1.8)))
    fig.subplots_adjust(left=0.24, right=0.96, top=0.80, bottom=0.18)
    bars = ax.barh(names, scores, color=colors, height=0.58, zorder=3)
    ax.bar_label(
        bars,
        labels=[f"  {s} · {r[2] if len(r) > 2 else ''}"
                for s, r in zip(scores, rows)],
        padding=4, fontsize=11, fontweight="bold", color=SPICE["charcoal"])
    avg = sa.get("portfolio_avg")
    if avg is not None:
        ax.axvline(avg, color=SPICE["charcoal"], ls="--", lw=1.2, zorder=2)
        ax.annotate(f"portfolio avg {avg}", xy=(avg, -0.7),
                    xytext=(avg, -0.95), ha="center", fontsize=9.5,
                    color=SPICE["charcoal"], annotation_clip=False)
    ax.set_xlim(0, 105)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(-0.6, len(names) - 0.4)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    _titles(fig, title, subtitle, title_y=0.97, sub_y=0.88)
    out = charts / "storefront_audit.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def trend_overlay(m: dict, charts: Path) -> "Path | None":
    """REAL weekly GMV (bars) + orders (line, twin axis) across the window.
    Derived upstream from per-order DD/GH transaction exports. Every label
    string is data-supplied (metrics.trend_weekly). No-ops cleanly when the
    weekly series is absent — never fabricated."""
    t = m.get("trend_weekly")
    if not t or not t.get("weeks") or not t.get("gmv") or not t.get("orders"):
        return None
    weeks, gmv, orders = t["weeks"], t["gmv"], t["orders"]
    x = np.arange(len(weeks))
    fig, ax1 = plt.subplots(figsize=(9.2, 4.6))
    fig.subplots_adjust(left=0.10, right=0.90, top=0.80, bottom=0.18)
    ax1.bar(x, gmv, color=SPICE["orange"], width=0.62, zorder=3,
            label="Weekly GMV")
    ax1.set_ylabel("GMV ($)", color=SPICE["charcoal"])
    ax1.set_xticks(x)
    ax1.set_xticklabels(weeks, fontsize=9, color=SPICE["charcoal"])
    ax1.set_ylim(0, (max(gmv) or 1) * 1.25)
    for sp in ("top", "right"):
        ax1.spines[sp].set_visible(False)
    ax2 = ax1.twinx()
    ax2.plot(x, orders, color=SPICE["charcoal"], lw=2, marker="o",
             ms=4, zorder=4, label="Orders")
    ax2.set_ylabel("Orders", color=SPICE["charcoal"])
    ax2.set_ylim(0, (max(orders) or 1) * 1.35)
    ax2.spines["top"].set_visible(False)
    title = t.get("title", "Weekly Trend — GMV & Orders")
    subtitle = t.get("caption") or t.get("source", "")
    _titles(fig, title, subtitle, title_y=0.97, sub_y=0.05)
    out = charts / "trend_overlay.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def daypart_heatmap(m: dict, charts: Path) -> "Path | None":
    """REAL day×hour order-count heatmap with the peak cell ringed. Derived
    upstream from per-order DD/GH transaction exports. Caption is built from
    data-supplied metrics.daypart fields only. No-ops cleanly when the
    matrix is absent — never fabricated."""
    d = m.get("daypart")
    if not d or not d.get("matrix") or not d.get("days") or not d.get("hours"):
        return None
    days, hours, mat = d["days"], d["hours"], np.array(d["matrix"])
    fig, ax = plt.subplots(figsize=(10.2, 4.4))
    fig.subplots_adjust(left=0.08, right=0.99, top=0.80, bottom=0.18)
    im = ax.imshow(mat, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(hours)))
    ax.set_xticklabels([f"{h}" for h in hours], fontsize=8)
    ax.set_yticks(range(len(days)))
    ax.set_yticklabels(days, fontsize=10, fontweight="bold")
    ax.set_xlabel("Hour of day (store-local)", color=SPICE["charcoal"])
    pk = d.get("peak")
    if pk and pk.get("hour") in hours and pk.get("day") in days:
        pj, pi = hours.index(pk["hour"]), days.index(pk["day"])
        ax.add_patch(plt.Rectangle((pj - 0.5, pi - 0.5), 1, 1, fill=False,
                     edgecolor=SPICE["charcoal"], lw=2.2, zorder=5))
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
    cb.ax.tick_params(labelsize=8)
    title = d.get("title", "Order Daypart — orders by day × hour")
    cap = d.get("caption") or d.get("source", "")
    if pk and not d.get("caption"):
        cap = (f"{cap} Peak: {pk.get('day')} {pk.get('hour')}:00 "
               f"({pk.get('orders')} orders).").strip()
    if d.get("weakest_day") and not d.get("caption"):
        cap += f" Weakest day: {d['weakest_day']}."
    _titles(fig, title, cap, title_y=0.97, sub_y=0.04)
    out = charts / "daypart_heatmap.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def generate(run_dir: Path) -> list[Path]:
    m = json.loads((run_dir / "metrics.json").read_text())
    charts = run_dir / "charts"
    charts.mkdir(exist_ok=True)
    made = [radar_7dim(m, charts), tier_donut(m, charts)]
    optional = (top15_green_bar, funnel_ue, storefront_audit,
                trend_overlay, daypart_heatmap)
    for fn in optional:
        p = fn(m, charts)
        if p:
            made.append(p)
    skipped = []
    if not m.get("trend_weekly"):
        skipped.append("trend_overlay.png (no per-order weekly series "
                        "in parsed data)")
    if not m.get("daypart"):
        skipped.append("daypart_heatmap.png (no per-order hour×day matrix "
                        "in parsed data)")
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
