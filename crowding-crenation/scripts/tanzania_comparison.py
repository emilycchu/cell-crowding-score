"""Compare two crowding-scoring approaches against manual density/overlap labels for
the Tanzania slide KTR-72502948 (324 FOVs, all from one slide) -- both a naive
(marginal) correlation and a partial correlation controlling for the fact that
density and overlap are themselves highly correlated in this slide's manual labels
(Spearman rho ~0.75; see data/results/tanzania-073026/tanzania-comparison/README.md).

Two approaches, each feature tested SEPARATELY against each label axis (never
combined into one severity score -- that conflation is what made earlier analyses
unable to say which feature maps to which axis):

  ai-first  -- raw per-FOV metrics from scripts/ai-first/score_new_slide.py
               (data/new/KTR-72502948/fov_scores.csv)
  four-step -- the four src/features/ techniques, run fresh over the same 324
               images (scripts/four-step/run_four_step_tanzania.py ->
               data/new/KTR-72502948/four_step_scores.csv)

For each feature x {density, overlap}:
  - marginal Spearman rho (naive)
  - partial Spearman rho controlling for the other axis, via the standard
    3-variable partial-correlation formula on Spearman rhos:
        rho_xy.z = (rho_xy - rho_xz*rho_yz) / sqrt((1-rho_xz^2)(1-rho_yz^2))

Usage:
    python scripts/tanzania_comparison.py
"""
import csv
import random
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import viridis
from matplotlib.lines import Line2D
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from compare_tanzania_labels import DENSITY_ORDER, ROULEAUX_ORDER, load_manual  # noqa: E402

MANUAL_CSV = ROOT / "data" / "labels" / "tanzania-073026" / "KTR-72502948-annotated.csv"
AI_FIRST_CSV = ROOT / "data" / "new" / "KTR-72502948" / "fov_scores.csv"
FOUR_STEP_CSV = ROOT / "data" / "new" / "KTR-72502948" / "four_step_scores.csv"
OUT_DIR = ROOT / "data" / "results" / "tanzania-073026" / "tanzania-comparison"

JITTER_SEED = 7

# same palette as compare_tanzania_labels.py (references/palette.md)
COLOR_MINE = "#2a78d6"
COLOR_GRID = "#e1e0d9"
COLOR_AXIS = "#c3c2b7"
COLOR_MUTED = "#898781"
COLOR_PRIMARY = "#0b0b0b"
COLOR_SECONDARY = "#52514e"
COLOR_SURFACE = "#fcfcfb"

AI_FIRST_FEATURES = [
    ("coverage_fraction", "Coverage fraction"),
    ("rouleaux_fraction", "Rouleaux fraction"),
    ("crenation_fraction", "Crenation fraction"),
    ("n_cells", "N cells"),
    ("median_area", "Median cell area"),
    ("area_cv", "Cell-area CV"),
]

FOUR_STEP_FEATURES = [
    ("coverage", "Otsu coverage"),
    ("edge_density_masked", "Edge density (masked)"),
    ("edge_density_unmasked", "Edge density (unmasked)"),
    ("glcm_contrast", "GLCM contrast"),
    ("lbp_entropy", "LBP entropy"),
]


def load_scores_csv(path):
    rows = list(csv.DictReader(open(path)))
    return {int(r["idx"]): {k: float(v) for k, v in r.items() if k != "idx"} for r in rows}


def partial_spearman(rho_xy, rho_xz, rho_yz):
    denom = np.sqrt((1 - rho_xz ** 2) * (1 - rho_yz ** 2))
    if denom < 1e-9:
        return float("nan")
    return float((rho_xy - rho_xz * rho_yz) / denom)


def build_dataset():
    manual = load_manual(MANUAL_CSV)
    ai_first = load_scores_csv(AI_FIRST_CSV)
    four_step = load_scores_csv(FOUR_STEP_CSV)

    common = sorted(set(manual) & set(ai_first) & set(four_step))
    if len(common) != len(manual):
        print(f"warning: manual has {len(manual)} FOVs, {len(common)} in common across all three sources")

    density_rank = np.array([DENSITY_ORDER.index(manual[i]["density"]) for i in common])
    overlap_rank = np.array([ROULEAUX_ORDER.index(manual[i]["rouleaux"]) for i in common])

    return common, manual, ai_first, four_step, density_rank, overlap_rank


def compute_correlations(common, features_by_source, ai_first, four_step, density_rank, overlap_rank):
    rho_do, _ = spearmanr(density_rank, overlap_rank)
    results = []
    for approach, feature_list, source in [("ai-first", AI_FIRST_FEATURES, ai_first), ("four-step", FOUR_STEP_FEATURES, four_step)]:
        for key, label in feature_list:
            values = np.array([source[i][key] for i in common])
            rho_fd, _ = spearmanr(values, density_rank)
            rho_fo, _ = spearmanr(values, overlap_rank)
            partial_fd = partial_spearman(rho_fd, rho_fo, rho_do)
            partial_fo = partial_spearman(rho_fo, rho_fd, rho_do)
            results.append({
                "approach": approach, "feature": key, "label": label,
                "marginal_density": rho_fd, "partial_density": partial_fd,
                "marginal_overlap": rho_fo, "partial_overlap": partial_fo,
            })
        features_by_source[approach] = (feature_list, source)
    return results, rho_do


def jitter_x(rank_array, n, rng, spread=0.16):
    return rank_array + np.array([rng.uniform(-spread, spread) for _ in range(n)])


def draw_box(ax, values_by_rank, order, color):
    data = [values_by_rank.get(i, []) for i in range(len(order))]
    bp = ax.boxplot(
        data, positions=range(len(order)), widths=0.5, patch_artist=True,
        showfliers=False, zorder=2,
    )
    for box in bp["boxes"]:
        box.set(facecolor="none", edgecolor=color, linewidth=1.3)
    for element in ("whiskers", "caps", "medians"):
        for artist in bp[element]:
            artist.set(color=color, linewidth=1.3)


def style_axis(ax, order, tick_labels, ylabel):
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(tick_labels, rotation=20, ha="right", fontsize=8)
    ax.set_xlim(-0.6, len(order) - 0.4)
    ax.tick_params(colors=COLOR_MUTED, labelsize=8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(COLOR_AXIS)
    ax.grid(True, axis="y", color=COLOR_GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    ax.set_ylabel(ylabel, color=COLOR_SECONDARY, fontsize=8)


def plot_naive_grid(approach, feature_list, source, common, density_rank, overlap_rank, results_by_feature, out_path):
    n_rows = len(feature_list)
    fig, axes = plt.subplots(n_rows, 2, figsize=(11, 2.6 * n_rows), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    rng = random.Random(JITTER_SEED)

    for row, (key, label) in enumerate(feature_list):
        values = np.array([source[i][key] for i in common])
        r = results_by_feature[key]

        for col, (rank_arr, order, tick_labels, target_name, marginal_rho) in enumerate([
            (density_rank, DENSITY_ORDER, [l.capitalize() for l in DENSITY_ORDER], "density", r["marginal_density"]),
            (overlap_rank, ROULEAUX_ORDER, [l.capitalize() for l in ROULEAUX_ORDER], "overlap", r["marginal_overlap"]),
        ]):
            ax = axes[row, col]
            ax.set_facecolor(COLOR_SURFACE)
            xs = jitter_x(rank_arr, len(rank_arr), rng)
            ax.scatter(xs, values, s=14, color=COLOR_MINE, alpha=0.45, linewidths=0, zorder=3)

            values_by_rank = {}
            for rk, v in zip(rank_arr, values):
                values_by_rank.setdefault(int(rk), []).append(v)
            draw_box(ax, values_by_rank, order, COLOR_PRIMARY)

            style_axis(ax, order, tick_labels, label if col == 0 else "")
            ax.set_title(f"{label} vs. {target_name}  (rho={marginal_rho:.2f})", loc="left",
                         color=COLOR_PRIMARY, fontsize=9, fontweight="bold")

    fig.suptitle(
        f"{approach} -- naive (marginal) correlation, n={len(common)} FOVs",
        x=0.01, y=0.995, ha="left", color=COLOR_PRIMARY, fontsize=13, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


def plot_partial_grid(approach, feature_list, source, common, density_rank, overlap_rank, results_by_feature, out_path):
    n_rows = len(feature_list)
    fig, axes = plt.subplots(n_rows, 2, figsize=(12, 2.9 * n_rows), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    rng = random.Random(JITTER_SEED)

    for row, (key, label) in enumerate(feature_list):
        values = np.array([source[i][key] for i in common])
        r = results_by_feature[key]

        panels = [
            (density_rank, overlap_rank, DENSITY_ORDER, ROULEAUX_ORDER, "density", "overlap",
             r["marginal_density"], r["partial_density"]),
            (overlap_rank, density_rank, ROULEAUX_ORDER, DENSITY_ORDER, "overlap", "density",
             r["marginal_overlap"], r["partial_overlap"]),
        ]
        for col, (rank_arr, confound_arr, order, confound_order, target_name, confound_name,
                  marginal_rho, partial_rho) in enumerate(panels):
            ax = axes[row, col]
            ax.set_facecolor(COLOR_SURFACE)
            xs = jitter_x(rank_arr, len(rank_arr), rng)
            colors = viridis(confound_arr / max(len(confound_order) - 1, 1))
            ax.scatter(xs, values, s=16, c=colors, alpha=0.65, linewidths=0, zorder=3)

            values_by_rank = {}
            for rk, v in zip(rank_arr, values):
                values_by_rank.setdefault(int(rk), []).append(v)
            draw_box(ax, values_by_rank, order, COLOR_PRIMARY)

            tick_labels = [l.capitalize() for l in order]
            style_axis(ax, order, tick_labels, label if col == 0 else "")
            ax.set_title(
                f"{label} vs. {target_name}\n(marginal rho={marginal_rho:.2f}, partial rho|{confound_name}={partial_rho:.2f})",
                loc="left", color=COLOR_PRIMARY, fontsize=8.5, fontweight="bold",
            )

    fig.suptitle(
        f"{approach} -- partial correlation controlling for the other axis, n={len(common)} FOVs",
        x=0.01, y=0.995, ha="left", color=COLOR_PRIMARY, fontsize=13, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.965), h_pad=2.2)

    cbar_ax = fig.add_axes((0.3, 0.012, 0.4, 0.012))
    sm = plt.cm.ScalarMappable(cmap=viridis, norm=plt.Normalize(0, 1))
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label("point color = the OTHER axis's level (dark=low, light=high)", color=COLOR_SECONDARY, fontsize=9)
    cbar.outline.set_visible(False)

    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


def plot_annotation_distribution(manual, common, out_path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)

    panels = [("Density", DENSITY_ORDER, "density"), ("Overlap (rouleaux)", ROULEAUX_ORDER, "rouleaux")]
    for ax, (title, order, key) in zip(axes, panels):
        ax.set_facecolor(COLOR_SURFACE)
        counts = [sum(1 for i in common if manual[i][key] == k) for k in order]
        bars = ax.bar(range(len(order)), counts, color=COLOR_MINE, zorder=3, width=0.6)
        for b in bars:
            ax.annotate(str(int(b.get_height())), (b.get_x() + b.get_width() / 2, b.get_height()),
                        xytext=(0, 3), textcoords="offset points", ha="center", fontsize=9, color=COLOR_SECONDARY)
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([l.capitalize() for l in order], rotation=20, ha="right", fontsize=9)
        ax.tick_params(colors=COLOR_MUTED, labelsize=9)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(COLOR_AXIS)
        ax.grid(True, axis="y", color=COLOR_GRID, linewidth=1, zorder=0)
        ax.set_axisbelow(True)
        ax.set_title(title, loc="left", color=COLOR_PRIMARY, fontsize=12, fontweight="bold")
        ax.set_ylabel("FOV count", color=COLOR_SECONDARY, fontsize=9)

    fig.suptitle(
        f"KTR-72502948 (Tanzania) -- manual annotation distribution, n={len(common)} FOVs",
        x=0.015, y=0.99, ha="left", color=COLOR_PRIMARY, fontsize=13, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


def write_summary_csv(results, rho_do, out_path):
    fieldnames = ["approach", "feature", "label", "marginal_density", "partial_density",
                  "marginal_overlap", "partial_overlap"]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    print(f"manual density-vs-overlap confound: rho={rho_do:.3f}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    common, manual, ai_first, four_step, density_rank, overlap_rank = build_dataset()

    features_by_source = {}
    results, rho_do = compute_correlations(common, features_by_source, ai_first, four_step, density_rank, overlap_rank)

    plot_annotation_distribution(manual, common, OUT_DIR / "manual-annotation-distribution.png")

    for approach, (feature_list, source) in features_by_source.items():
        results_by_feature = {r["feature"]: r for r in results if r["approach"] == approach}
        plot_naive_grid(approach, feature_list, source, common, density_rank, overlap_rank,
                         results_by_feature, OUT_DIR / f"{approach}-naive.png")
        plot_partial_grid(approach, feature_list, source, common, density_rank, overlap_rank,
                           results_by_feature, OUT_DIR / f"{approach}-partial.png")
        print(f"wrote {approach} plots")

    write_summary_csv(results, rho_do, OUT_DIR / "correlation-summary.csv")
    print(f"n = {len(common)} FOVs")
    print(f"Wrote all outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
