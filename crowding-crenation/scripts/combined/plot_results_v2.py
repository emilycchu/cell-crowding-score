"""Plots for the v2 calibration: density-only, Rouleaux-only, and a density-vs-Rouleaux
comparison scatter -- one point per FOV, jittered against the manual category where
applicable. Reuses the jittered-scatter-plus-box helpers and dataviz palette already
established in scripts/tanzania_comparison.py rather than reinventing them.

Usage:
    python scripts/combined/plot_results_v2.py [--features-csv PATH] [--params-json PATH]
        [--out-dir DIR]
"""
import argparse
import json
import random
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import viridis

from _v2_common import (
    COLOR_AXIS,
    COLOR_GRID,
    COLOR_MINE,
    COLOR_MUTED,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_SURFACE,
    DENSITY_LEVELS,
    FEATURES_CSV,
    JITTER_SEED,
    OVERLAP_LEVELS,
    PARAMS_JSON,
    PLOTS_DIR,
    ROOT,
    display_level,
    read_csv_dicts,
)

sys.path.insert(0, str(ROOT / "scripts"))
from tanzania_comparison import draw_box, jitter_x, style_axis  # noqa: E402

sys.path.insert(0, str(ROOT))
from src.composite_v2 import weighted_composite  # noqa: E402


def load_rows(features_csv, params):
    rows = read_csv_dicts(features_csv)
    all_feature_names = set(params["density"]["feature_names"]) | set(params["overlap"]["feature_names"])
    for r in rows:
        r["density_ord"] = int(r["density_ord"])
        r["overlap_ord"] = int(r["overlap_ord"])
        for name in all_feature_names:
            r[name] = float(r[name])
    return rows


def score_axis(rows, axis_params):
    weights = axis_params["weights"]
    ranges = {n: (v["min"], v["max"]) for n, v in axis_params["normalization"].items()}
    return np.array([weighted_composite(r, weights, ranges) for r in rows])


def plot_axis_only(rank_arr, scores, levels, axis_label, out_path):
    rng = random.Random(JITTER_SEED)
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    xs = jitter_x(rank_arr, len(rank_arr), rng)
    ax.scatter(xs, scores, s=16, color=COLOR_MINE, alpha=0.5, linewidths=0, zorder=3)

    values_by_rank = {}
    for rk, v in zip(rank_arr, scores):
        values_by_rank.setdefault(int(rk), []).append(v)
    draw_box(ax, values_by_rank, levels, COLOR_PRIMARY)

    tick_labels = [display_level(l) for l in levels]
    style_axis(ax, levels, tick_labels, f"{axis_label} composite score")
    ax.set_xlabel(f"Manual {axis_label.lower()} label", color=COLOR_SECONDARY, fontsize=10)
    fig.suptitle(f"{axis_label} -- fitted composite score vs. manual label, n={len(rank_arr)} FOVs",
                 x=0.02, y=0.98, ha="left", color=COLOR_PRIMARY, fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


def plot_comparison(density_scores, overlap_scores, density_rank, overlap_rank, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)

    panels = [
        (density_rank, len(DENSITY_LEVELS), "density", axes[0]),
        (overlap_rank, len(OVERLAP_LEVELS), "Rouleaux", axes[1]),
    ]
    for confound_rank, n_levels, confound_label, ax in panels:
        ax.set_facecolor(COLOR_SURFACE)
        colors = viridis(confound_rank / max(n_levels - 1, 1))
        ax.scatter(density_scores, overlap_scores, s=18, c=colors, alpha=0.7, linewidths=0, zorder=3)
        ax.set_xlabel("Density composite score", color=COLOR_SECONDARY, fontsize=10)
        ax.set_ylabel("Rouleaux composite score", color=COLOR_SECONDARY, fontsize=10)
        ax.tick_params(colors=COLOR_MUTED, labelsize=9)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(COLOR_AXIS)
        ax.grid(True, color=COLOR_GRID, linewidth=1, zorder=0)
        ax.set_axisbelow(True)
        ax.set_title(f"colored by manual {confound_label} level", loc="left",
                     color=COLOR_PRIMARY, fontsize=10, fontweight="bold")

    fig.suptitle("Density vs. Rouleaux composite scores, one point per FOV",
                 x=0.02, y=0.97, ha="left", color=COLOR_PRIMARY, fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0.14, 1, 0.92))

    cbar_ax = fig.add_axes((0.3, 0.07, 0.4, 0.02))
    sm = plt.cm.ScalarMappable(cmap=viridis, norm=plt.Normalize(0, 1))
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.ax.tick_params(colors=COLOR_MUTED, labelsize=8)
    cbar.set_label("point color = manual level for that panel's axis (dark=low, light=high)",
                   color=COLOR_SECONDARY, fontsize=9)
    cbar.outline.set_visible(False)

    fig.savefig(out_path, facecolor=COLOR_SURFACE, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Generate v2 density/Rouleaux plots.")
    parser.add_argument("--features-csv", default=str(FEATURES_CSV))
    parser.add_argument("--params-json", default=str(PARAMS_JSON))
    parser.add_argument("--out-dir", default=str(PLOTS_DIR))
    parser.add_argument("--suffix", default="v2", help="Output filename suffix, e.g. 'v2.1' for a recalibration run.")
    args = parser.parse_args()

    with open(args.params_json) as f:
        params = json.load(f)
    rows = load_rows(args.features_csv, params)

    density_rank = np.array([r["density_ord"] for r in rows])
    overlap_rank = np.array([r["overlap_ord"] for r in rows])
    density_scores = score_axis(rows, params["density"])
    overlap_scores = score_axis(rows, params["overlap"])

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    plot_axis_only(density_rank, density_scores, DENSITY_LEVELS, "Density", out_dir / f"density-{args.suffix}.png")
    plot_axis_only(overlap_rank, overlap_scores, OVERLAP_LEVELS, "Rouleaux", out_dir / f"overlap-{args.suffix}.png")
    plot_comparison(density_scores, overlap_scores, density_rank, overlap_rank, out_dir / f"density-vs-overlap-{args.suffix}.png")

    print(f"wrote plots to {out_dir}")


if __name__ == "__main__":
    main()
