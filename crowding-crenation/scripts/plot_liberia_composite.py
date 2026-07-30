"""Box + jittered-point plot of composite crowding scores from score_liberia_sample.py,
color-coded by slide.

Usage:
    python scripts/plot_liberia_composite.py negatives
    python scripts/plot_liberia_composite.py positives
"""
import argparse
import csv
import random
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from liberia_groups import GROUPS, slide_colors

JITTER_SEED = 7

# dataviz reference palette (references/palette.md), matching pairwise_analysis.py
COLOR_GRID = "#e1e0d9"
COLOR_AXIS = "#c3c2b7"
COLOR_MUTED = "#898781"
COLOR_PRIMARY = "#0b0b0b"
COLOR_SECONDARY = "#52514e"
COLOR_SURFACE = "#fcfcfb"


def load_scores(in_csv, slide_order):
    with open(in_csv, newline="") as f:
        rows = list(csv.DictReader(f))
    by_slide = {slide: [] for slide in slide_order}
    for row in rows:
        by_slide[row["slide"]].append((float(row["composite_score"]), row["fov"]))
    return by_slide


def outlier_mask(values):
    """Standard 1.5x-IQR box-plot rule, matching matplotlib's own flier definition."""
    values = np.asarray(values)
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return (values < lower) | (values > upper)


def plot(by_slide, slide_order, colors, subtitle, out_path):
    rng = random.Random(JITTER_SEED)
    positions = range(1, len(slide_order) + 1)

    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    box_data = [[v for v, _ in by_slide[slide]] for slide in slide_order]
    bp = ax.boxplot(
        box_data,
        positions=positions,
        widths=0.5,
        showfliers=False,
        patch_artist=True,
        medianprops={"color": COLOR_PRIMARY, "linewidth": 2},
        whiskerprops={"color": COLOR_AXIS, "linewidth": 1.5},
        capprops={"color": COLOR_AXIS, "linewidth": 1.5},
    )
    for box, slide in zip(bp["boxes"], slide_order):
        color = colors[slide]
        box.set_facecolor(color)
        box.set_alpha(0.12)
        box.set_edgecolor(color)
        box.set_linewidth(1.5)

    for pos, slide in zip(positions, slide_order):
        values = [v for v, _ in by_slide[slide]]
        fovs = [f for _, f in by_slide[slide]]
        xs = [pos + rng.uniform(-0.15, 0.15) for _ in values]
        ax.scatter(
            xs,
            values,
            s=32,
            color=colors[slide],
            edgecolors=COLOR_SURFACE,
            linewidths=0.8,
            alpha=0.85,
            zorder=3,
        )

        label_count = 0
        for x, y, fov, is_outlier in zip(xs, values, fovs, outlier_mask(values)):
            if is_outlier:
                ax.annotate(
                    Path(fov).stem,
                    (x, y),
                    xytext=(5, 3 + label_count * 9),
                    textcoords="offset points",
                    fontsize=7,
                    color=COLOR_SECONDARY,
                    zorder=4,
                )
                label_count += 1

    ax.set_xticks(list(positions))
    ax.set_xticklabels(slide_order)
    ax.tick_params(colors=COLOR_MUTED, labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(COLOR_AXIS)
    ax.grid(True, axis="y", color=COLOR_GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)

    ax.set_ylim(0, 1)
    ax.set_xlabel("Slide (specimen barcode)", color=COLOR_SECONDARY, fontsize=10)
    ax.set_ylabel("Composite crowding score", color=COLOR_SECONDARY, fontsize=10)
    fig.suptitle(
        "Composite crowding score by slide",
        x=0.015,
        y=0.98,
        ha="left",
        color=COLOR_PRIMARY,
        fontsize=14,
        fontweight="bold",
    )
    n = len(next(iter(by_slide.values())))
    ax.set_title(
        f"{subtitle} — random sample of {n} FOVs/slide",
        loc="left",
        color=COLOR_SECONDARY,
        fontsize=10,
        pad=10,
    )

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot composite crowding scores for a Liberia slide group.")
    parser.add_argument("group", choices=sorted(GROUPS))
    args = parser.parse_args()

    group = GROUPS[args.group]
    slide_order = list(group["slides"])
    by_slide = load_scores(group["results_dir"] / "composite-scores.csv", slide_order)
    out_png = group["results_dir"] / "composite-score-boxplot.png"
    plot(by_slide, slide_order, slide_colors(args.group), group["subtitle"], out_png)
    print(f"Wrote {out_png}")
