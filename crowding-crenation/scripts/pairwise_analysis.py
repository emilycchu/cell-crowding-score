"""4x4 pairwise comparison of the 4 image-processing techniques against each other
(not against the manual severity labels). For every technique pair, plots one
technique's raw output against the other's across the initial-dataset FOVs, and
summarizes all pairwise comparisons in one 4x4 grid image.

Usage:
    python scripts/pairwise_analysis.py
"""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATASET = "initial-dataset-071626"
LABELS_DIR = Path(f"data/labels/{DATASET}")
RESULTS_DIR = Path(f"data/results/{DATASET}")
OUT_DIR = RESULTS_DIR / "pairwise-analysis"
INDIVIDUAL_DIR = OUT_DIR / "individual"

# name, csv file, column, unit ("%" or "")
TECHNIQUES = [
    ("Otsu coverage", "otsu.csv", "coverage_pct", "%"),
    ("Edge density", "edge-density.csv", "edge_density_unmasked_pct", "%"),
    ("GLCM contrast", "glcm-contrast.csv", "glcm_contrast", ""),
    ("LBP entropy", "lbp-entropy.csv", "lbp_entropy", ""),
]

# dataviz reference palette (references/palette.md), matching generate_report.py
COLOR_POINT = "#2a78d6"
COLOR_TREND = "#2a78d6"
COLOR_GRID = "#e1e0d9"
COLOR_AXIS = "#c3c2b7"
COLOR_MUTED = "#898781"
COLOR_PRIMARY = "#0b0b0b"
COLOR_SECONDARY = "#52514e"
COLOR_SURFACE = "#fcfcfb"
COLOR_DIAGONAL = "#e1e0d9"


def load_fovs():
    with open(LABELS_DIR / "fovs.csv", newline="") as f:
        return list(csv.DictReader(f))


def load_metric_csv(filename):
    with open(RESULTS_DIR / filename, newline="") as f:
        return {row["filename"]: row for row in csv.DictReader(f)}


def slug(name):
    return name.lower().replace(" ", "-")


def build_series(fovs, csv_file, column):
    metric_rows = load_metric_csv(csv_file)
    fov_ids, values = [], []
    for row in fovs:
        metric_row = metric_rows.get(row["filename"])
        if metric_row is None:
            raise ValueError(f"No result for {row['filename']} in {csv_file}")
        fov_ids.append(row["fov"])
        values.append(float(metric_row[column]))
    return fov_ids, np.array(values, dtype=float)


def pairwise_stats(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    r = np.corrcoef(x, y)[0, 1]
    rho = spearmanr(x, y).statistic
    return slope, intercept, r, rho


def style_axes(ax):
    ax.tick_params(colors=COLOR_MUTED, labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(COLOR_AXIS)
    ax.grid(True, color=COLOR_GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)


def plot_individual(name_x, unit_x, x, name_y, unit_y, y, fov_ids, slope, intercept, r, rho, out_path):
    fig, ax = plt.subplots(figsize=(7, 5.5), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    xs = np.array([x.min(), x.max()])
    pad = (xs[1] - xs[0]) * 0.08 or 1.0
    xs_line = np.array([xs[0] - pad, xs[1] + pad])
    ax.plot(xs_line, slope * xs_line + intercept, color=COLOR_TREND, alpha=0.35, linewidth=2, zorder=1)

    ax.scatter(x, y, s=70, color=COLOR_POINT, edgecolors=COLOR_SURFACE, linewidths=1.5, zorder=2)
    for xi, yi, fov in zip(x, y, fov_ids):
        ax.annotate(
            f"FOV {fov}",
            (xi, yi),
            textcoords="offset points",
            xytext=(8, 6),
            fontsize=8,
            color=COLOR_MUTED,
        )

    fig.suptitle(f"{name_x} vs {name_y}", x=0.015, y=0.995, ha="left", color=COLOR_PRIMARY, fontsize=14, fontweight="bold")
    ax.set_title(
        f"r = {r:.2f}  ·  r² = {r ** 2:.2f}  ·  ρ = {rho:.2f}",
        color=COLOR_SECONDARY,
        fontsize=10,
        loc="left",
        pad=10,
    )
    ax.set_xlabel(f"{name_x} ({unit_x.strip() or 'raw value'})", color=COLOR_SECONDARY, fontsize=10)
    ax.set_ylabel(f"{name_y} ({unit_y.strip() or 'raw value'})", color=COLOR_SECONDARY, fontsize=10)
    style_axes(ax)

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


def plot_grid(series, stats_by_pair, out_path):
    n = len(TECHNIQUES)
    fig = plt.figure(figsize=(16, 16), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    outer = fig.add_gridspec(n, n, wspace=0.35, hspace=0.35, left=0.06, right=0.98, top=0.89, bottom=0.05)

    fig.suptitle(
        "Pairwise comparison of the 4 image-processing techniques (initial dataset, 13 FOVs)",
        x=0.03,
        y=0.995,
        ha="left",
        va="top",
        color=COLOR_PRIMARY,
        fontsize=16,
        fontweight="bold",
    )

    for row in range(n):
        for col in range(n):
            name_row, _, _, unit_row = TECHNIQUES[row]
            name_col, _, _, unit_col = TECHNIQUES[col]

            if row == col:
                ax = fig.add_subplot(outer[row, col])
                ax.set_facecolor(COLOR_DIAGONAL)
                ax.text(
                    0.5, 0.5, name_row,
                    ha="center", va="center", fontsize=12, fontweight="bold",
                    color=COLOR_SECONDARY, wrap=True, transform=ax.transAxes,
                )
                ax.set_xticks([])
                ax.set_yticks([])
                for spine in ax.spines.values():
                    spine.set_visible(False)
                continue

            inner = outer[row, col].subgridspec(1, 2, width_ratios=[3, 2], wspace=0.08)
            ax_plot = fig.add_subplot(inner[0, 0])
            ax_text = fig.add_subplot(inner[0, 1])
            ax_plot.set_facecolor(COLOR_SURFACE)
            ax_text.axis("off")

            x = series[name_col]
            y = series[name_row]
            pair_key = frozenset((name_row, name_col))
            slope, intercept, r, rho = stats_by_pair[pair_key]

            xs = np.array([x.min(), x.max()])
            pad = (xs[1] - xs[0]) * 0.08 or 1.0
            xs_line = np.array([xs[0] - pad, xs[1] + pad])
            ax_plot.plot(xs_line, slope * xs_line + intercept, color=COLOR_TREND, alpha=0.35, linewidth=1.5, zorder=1)
            ax_plot.scatter(x, y, s=28, color=COLOR_POINT, edgecolors=COLOR_SURFACE, linewidths=0.8, zorder=2)
            ax_plot.set_xticks([])
            ax_plot.set_yticks([])
            for spine in ("top", "right"):
                ax_plot.spines[spine].set_visible(False)
            for spine in ("left", "bottom"):
                ax_plot.spines[spine].set_color(COLOR_AXIS)

            ax_text.text(
                0.0, 0.5,
                f"r = {r:.2f}\nr² = {r ** 2:.2f}\nρ = {rho:.2f}",
                ha="left", va="center", fontsize=13, color=COLOR_PRIMARY,
                transform=ax_text.transAxes, linespacing=1.8,
            )

    for col in range(n):
        name_col = TECHNIQUES[col][0]
        pos = outer[0, col].get_position(fig)
        fig.text((pos.x0 + pos.x1) / 2, 0.94, name_col, ha="center", va="bottom", fontsize=11, color=COLOR_MUTED)

    for row in range(n):
        name_row = TECHNIQUES[row][0]
        pos = outer[row, 0].get_position(fig)
        fig.text(0.015, (pos.y0 + pos.y1) / 2, name_row, ha="left", va="center", rotation=90, fontsize=11, color=COLOR_MUTED)

    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


def main():
    fovs = load_fovs()
    INDIVIDUAL_DIR.mkdir(parents=True, exist_ok=True)

    series = {}
    fov_ids = None
    for name, csv_file, column, unit in TECHNIQUES:
        ids, values = build_series(fovs, csv_file, column)
        fov_ids = ids
        series[name] = values

    stats_by_pair = {}
    for i in range(len(TECHNIQUES)):
        for j in range(i + 1, len(TECHNIQUES)):
            name_x, _, _, unit_x = TECHNIQUES[i]
            name_y, _, _, unit_y = TECHNIQUES[j]
            x, y = series[name_x], series[name_y]
            slope, intercept, r, rho = pairwise_stats(x, y)
            stats_by_pair[frozenset((name_x, name_y))] = (slope, intercept, r, rho)

            out_path = INDIVIDUAL_DIR / f"{slug(name_x)}_vs_{slug(name_y)}.png"
            plot_individual(name_x, unit_x, x, name_y, unit_y, y, fov_ids, slope, intercept, r, rho, out_path)
            print(f"Wrote {out_path}")

    grid_path = OUT_DIR / "pairwise-grid.png"
    plot_grid(series, stats_by_pair, grid_path)
    print(f"Wrote {grid_path}")


if __name__ == "__main__":
    main()
