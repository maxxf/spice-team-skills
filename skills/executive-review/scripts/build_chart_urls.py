#!/usr/bin/env python3
"""
QuickChart URL builders for the Executive Review skill.

All charts use consistent styling:
- 700x400 px, white background
- 4px line widths, 6px point markers
- 18pt titles, 14pt axis labels
- Spice color palette (red/teal/navy/orange/gray)

Usage:
    from build_chart_urls import line_chart, bar_chart, dual_line_chart

    url = line_chart(
        title="Weekly Total Marketing Spend ($K) .  Jan 5 to May 11",
        labels=["Jan 5", "Jan 26", "Feb 16", "Mar 9", "Mar 30", "Apr 20", "May 11"],
        data=[129, 104, 75, 86, 79, 84, 72],
        y_min=60, y_max=140,
        y_label="$K",
        color="red",  # use Spice palette name
    )
"""

import json
import urllib.parse

# Spice color palette
COLORS = {
    "red":   {"border": "#E63946", "bg": "rgba(230, 57, 70, 0.1)",  "border_dark": "#A8202D"},
    "teal":  {"border": "#2A9D8F", "bg": "rgba(42, 157, 143, 0.15)", "border_dark": "#0D7561"},
    "navy":  {"border": "#264653", "bg": "rgba(38, 70, 83, 0.1)",   "border_dark": "#1A2F38"},
    "orange":{"border": "#F4A261", "bg": "rgba(244, 162, 97, 0.15)", "border_dark": "#C77325"},
    "gray":  {"border": "#94A3B8", "bg": "rgba(148, 163, 184, 0.2)", "border_dark": "#475569"},
}


def _build_url(config: dict) -> str:
    """Encode a Chart.js config as a QuickChart URL."""
    encoded = urllib.parse.quote(json.dumps(config, separators=(",", ":")))
    return f"https://quickchart.io/chart?bkg=white&w=700&h=400&c={encoded}"


def line_chart(
    title: str,
    labels: list,
    data: list,
    y_min: float | None = None,
    y_max: float | None = None,
    y_label: str | None = None,
    color: str = "teal",
    series_label: str | None = None,
) -> str:
    """Build a single-line chart URL.

    color: one of 'red' (spend / down is good), 'teal' (ROAS / growth),
           'navy' (neutral), 'orange' (ratings), 'gray' (baseline).
    """
    palette = COLORS.get(color, COLORS["teal"])
    y_ticks = {"fontSize": 14}
    if y_min is not None:
        y_ticks["min"] = y_min
    if y_max is not None:
        y_ticks["max"] = y_max

    y_axis = {"ticks": y_ticks}
    if y_label:
        y_axis["scaleLabel"] = {"display": True, "labelString": y_label, "fontSize": 14}

    config = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": series_label or title,
                "data": data,
                "borderColor": palette["border"],
                "backgroundColor": palette["bg"],
                "borderWidth": 4,
                "pointRadius": 6,
                "pointBackgroundColor": palette["border"],
                "fill": True,
                "tension": 0.3,
            }],
        },
        "options": {
            "title": {"display": True, "text": title, "fontSize": 18},
            "legend": {"display": False},
            "scales": {"yAxes": [y_axis], "xAxes": [{"ticks": {"fontSize": 14}}]},
        },
    }
    return _build_url(config)


def dual_line_chart(
    title: str,
    labels: list,
    series1: dict,  # {"label": "...", "data": [...], "color": "navy"}
    series2: dict,  # same structure
    y_min: float | None = None,
    y_max: float | None = None,
    y_label: str | None = None,
) -> str:
    """Build a two-line chart (e.g., SJ + Pasadena weekly sales).

    Each series dict needs: label (str), data (list), color (palette name).
    """
    def _ds(s, default_color):
        c = COLORS.get(s.get("color", default_color), COLORS[default_color])
        return {
            "label": s["label"],
            "data": s["data"],
            "borderColor": c["border"],
            "backgroundColor": c["bg"],
            "borderWidth": 4,
            "pointRadius": 6,
            "pointBackgroundColor": c["border"],
            "fill": False,
            "tension": 0.3,
        }

    y_ticks = {"fontSize": 14}
    if y_min is not None: y_ticks["min"] = y_min
    if y_max is not None: y_ticks["max"] = y_max
    y_axis = {"ticks": y_ticks}
    if y_label:
        y_axis["scaleLabel"] = {"display": True, "labelString": y_label, "fontSize": 14}

    config = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [
                _ds(series1, "red"),
                _ds(series2, "navy"),
            ],
        },
        "options": {
            "title": {"display": True, "text": title, "fontSize": 18},
            "legend": {"display": True, "position": "top", "labels": {"fontSize": 14}},
            "scales": {"yAxes": [y_axis], "xAxes": [{"ticks": {"fontSize": 14}}]},
        },
    }
    return _build_url(config)


def bar_chart(
    title: str,
    labels: list,
    data: list,
    colors: list | None = None,
    y_min: float | None = None,
    y_max: float | None = None,
    y_label: str | None = None,
) -> str:
    """Build a bar chart (before/after, per-location comparison).

    colors: list of palette names, one per bar. If None, defaults to alternating gray/teal.
    """
    if colors is None:
        # Default: gray for "before" / odd bars, teal for "after" / even bars
        colors = ["gray" if i % 2 == 0 else "teal" for i in range(len(labels))]

    bg_colors = [COLORS[c]["border"] for c in colors]
    border_colors = [COLORS[c]["border_dark"] for c in colors]

    y_ticks = {"fontSize": 14}
    if y_min is not None: y_ticks["min"] = y_min
    if y_max is not None: y_ticks["max"] = y_max
    y_axis = {"ticks": y_ticks}
    if y_label:
        y_axis["scaleLabel"] = {"display": True, "labelString": y_label, "fontSize": 14}

    config = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": title,
                "data": data,
                "backgroundColor": bg_colors,
                "borderColor": border_colors,
                "borderWidth": 2,
            }],
        },
        "options": {
            "title": {"display": True, "text": title, "fontSize": 18},
            "legend": {"display": False},
            "scales": {"yAxes": [y_axis], "xAxes": [{"ticks": {"fontSize": 14}}]},
        },
    }
    return _build_url(config)


def notion_image_md(alt: str, url: str) -> str:
    """Wrap a chart URL as a Notion-compatible markdown image."""
    return f"![{alt}]({url})"


if __name__ == "__main__":
    # Example usage / smoke test
    url = line_chart(
        title="Weekly Total Marketing Spend ($K) .  Jan 5 to May 11",
        labels=["Jan 5", "Jan 26", "Feb 16", "Mar 9", "Mar 30", "Apr 20", "May 11"],
        data=[129, 104, 75, 86, 79, 84, 72],
        y_min=60, y_max=140,
        y_label="$K",
        color="red",
    )
    print(notion_image_md("Weekly TMI", url))
