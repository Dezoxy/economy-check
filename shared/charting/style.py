#!/usr/bin/env python3
"""Consistent chart look for all economy-check reports.

The MA color semantics MATCH THE PROSE (style-guide.md narrates "piros 50 / kék 100 /
zöld 150 / fekete 200 napi") — chart and text must never disagree on what a color means.

matplotlib is the one non-stdlib dependency in this repo (charts only, step D/E):
    python3 -m pip install matplotlib
Fetchers/hooks/delivery stay stdlib-only so the pipeline core runs anywhere.
"""

# Moving-average colors — the vocabulary the reports narrate in
MA_COLORS = {
    "ma50d": "#d62728",    # piros (red)    — 50 napi
    "ma100d": "#1f77b4",   # kék (blue)     — 100 napi
    "ma150d": "#2ca02c",   # zöld (green)   — 150 napi
    "ma200d": "#000000",   # fekete (black) — 200 napi
    "ma200w": "#7f0dbe",   # lila           — 200 heti (cycle line)
}

PALETTE = {
    "price": "#222222",
    "volume": "#b0b0b0",
    "bull": "#2ca02c",
    "bear": "#d62728",
    "band": "#9ecae1",
    "accent": "#ff7f0e",
    "grid": "#dddddd",
    "background": "#ffffff",
    "annotation": "#555555",
}

FIGSIZE = (11, 6)
DPI = 144
WATERMARK = "economy-check"


def apply(plt):
    """Apply the house style to a matplotlib.pyplot module."""
    plt.rcParams.update({
        "figure.figsize": FIGSIZE,
        "figure.dpi": DPI,
        "figure.facecolor": PALETTE["background"],
        "axes.facecolor": PALETTE["background"],
        "axes.grid": True,
        "grid.color": PALETTE["grid"],
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "legend.frameon": False,
    })


def new_chart(title, src_tag):
    """Standard chart scaffold. src_tag e.g. 'src:binance/2026-07-20' — MANDATORY:
    every chart carries its source stamp, mirroring the [src:...] rule in prose."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise SystemExit(
            "matplotlib missing — charts need it: python3 -m pip install matplotlib"
        ) from e
    apply(plt)
    fig, ax = plt.subplots()
    ax.set_title(title, loc="left")
    fig.text(0.99, 0.01, "[%s]" % src_tag, ha="right", va="bottom",
             fontsize=8, color=PALETTE["annotation"])
    fig.text(0.01, 0.01, WATERMARK, ha="left", va="bottom",
             fontsize=8, color=PALETTE["grid"])
    return fig, ax


def save(fig, path):
    fig.savefig(path, bbox_inches="tight", facecolor=PALETTE["background"])
    return path
