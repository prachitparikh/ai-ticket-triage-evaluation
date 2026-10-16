"""Charts for the README and the one-page summary (needs matplotlib).

    python scripts/render_charts.py

Reads results/comparison_test.csv and results/business_case.json, writes
docs/images/*.png. Not part of CI: the PNGs are committed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from triage import RESULTS  # noqa: E402

OUT = ROOT / "docs" / "images"
NAMES = {"rules": "Today's rules", "ml": "In-house text model",
         "llm_claude-haiku-5-5": "Claude Haiku 5.5", "llm_claude-sonnet-5-5": "Claude Sonnet 5.5"}
ORDER = list(NAMES)

THEMES = {
    "light": {"bg": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#c9c7c0", "accent": "#2a78d6", "grid": "#e6e4de"},
    "dark": {"bg": "#1a1a19", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#55544f", "accent": "#3987e5", "grid": "#33322f"},
}


def comparison(theme: str, highlight: str) -> Path:
    t = THEMES[theme]
    df = pd.read_csv(RESULTS / "comparison_test.csv").set_index("method").reindex(ORDER).dropna(how="all")
    panels = [("team_accuracy", "Sent to the right team"), ("p1_recall", "P1 tickets rated P1"),
              ("security_to_trust", "Security reports sent to Trust")]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
    fig.patch.set_facecolor(t["bg"])
    labels = [NAMES[m] for m in df.index]
    for ax, (col, title) in zip(axes, panels):
        ax.set_facecolor(t["bg"])
        vals = (df[col] * 100).tolist()
        colors = [t["accent"] if m == highlight else t["muted"] for m in df.index]
        ys = range(len(vals))[::-1]
        ax.barh(list(ys), vals, color=colors, height=0.62, edgecolor=t["bg"], linewidth=2)
        for y, v in zip(ys, vals):
            label = f"{v:.1f}%" if 99 <= v < 100 else f"{v:.0f}%"  # 99.8% must not round up to 100%
            ax.text(v + 1.5, y, label, va="center", ha="left", fontsize=10, color=t["ink"])
        ax.set_xlim(0, 118)
        ax.set_title(title, fontsize=11, color=t["ink"], loc="left", pad=8)
        ax.set_xticks([0, 50, 100])
        ax.set_xticklabels(["0", "50", "100%"], color=t["ink2"], fontsize=9)
        ax.tick_params(axis="both", length=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(t["grid"])
        ax.xaxis.grid(True, color=t["grid"], linewidth=0.8)
        ax.set_axisbelow(True)
    axes[0].set_yticks(list(range(len(labels)))[::-1])
    axes[0].set_yticklabels(labels, color=t["ink"], fontsize=10)
    fig.text(0.01, 0.01, "500 held-out test tickets, Northstar Systems (fictional). Same tickets for every option.",
             color=t["ink2"], fontsize=8.5)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / ("comparison.png" if theme == "light" else "comparison_dark.png")
    fig.savefig(path, dpi=150, facecolor=t["bg"])
    plt.close(fig)
    return path


def main() -> None:
    bc = json.loads((RESULTS / "business_case.json").read_text())
    highlight = bc.get("recommended_method", "llm_claude-haiku-5-5")
    for theme in THEMES:
        print(comparison(theme, highlight))


if __name__ == "__main__":
    main()
