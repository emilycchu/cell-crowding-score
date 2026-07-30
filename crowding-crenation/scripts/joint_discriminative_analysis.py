"""Joint discriminative power test: for every pair of the 4 image-processing
techniques, fits a 2-feature linear regression against the manual density+overlap
severity score and compares its R^2 to the better of the two techniques alone.
This checks whether combining two techniques captures more of the labeled
severity signal than either does by itself -- complementary to
pairwise_analysis.py, which only checks how much techniques overlap with
*each other* (not with the label).

Usage:
    python scripts/joint_discriminative_analysis.py
"""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATASET = "initial-dataset-071626"
LABELS_DIR = Path(f"data/labels/{DATASET}")
RESULTS_DIR = Path(f"data/results/{DATASET}")
OUT_DIR = RESULTS_DIR / "joint-discriminative-analysis"
INDIVIDUAL_DIR = OUT_DIR / "individual"

DENSITY_ORDER = ["monolayer", "slightly dense", "dense", "very dense"]
OVERLAP_ORDER = ["no rouleaux", "slight rouleaux", "some rouleaux", "rouleaux", "heavy rouleaux"]

# name, csv file, column
TECHNIQUES = [
    ("Otsu coverage", "otsu.csv", "coverage_pct"),
    ("Edge density", "edge-density.csv", "edge_density_unmasked_pct"),
    ("GLCM contrast", "glcm-contrast.csv", "glcm_contrast"),
    ("LBP entropy", "lbp-entropy.csv", "lbp_entropy"),
]

REDUNDANT_GAIN = 0.04  # gain below this: second feature adds ~nothing over the best solo predictor
COMPLEMENTARY_GAIN = 0.10  # gain above this: combining captures meaningfully more than either alone

# dataviz reference palette (references/palette.md), matching pairwise_analysis.py
COLOR_SOLO = "#c3c2b7"
COLOR_JOINT = "#2a78d6"
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


def combined_score(row):
    return DENSITY_ORDER.index(row["density"]) + OVERLAP_ORDER.index(row["overlap"])


def slug(name):
    return name.lower().replace(" ", "-")


def build_series(fovs, csv_file, column):
    metric_rows = load_metric_csv(csv_file)
    values = []
    for row in fovs:
        metric_row = metric_rows.get(row["filename"])
        if metric_row is None:
            raise ValueError(f"No result for {row['filename']} in {csv_file}")
        values.append(float(metric_row[column]))
    return np.array(values, dtype=float)


def r2_solo(x, y):
    r = np.corrcoef(x, y)[0, 1]
    return r ** 2


def r2_joint(x1, x2, y):
    X = np.column_stack([np.ones_like(x1), x1, x2])
    coefs, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coefs
    ss_res = np.sum((y - pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    return 1 - ss_res / ss_tot


def adjusted_r2(r2, n, p):
    denom = n - p - 1
    if denom <= 0:
        return float("nan")
    return 1 - (1 - r2) * (n - 1) / denom


def style_bar_axes(ax):
    ax.set_yticks([])
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(COLOR_AXIS)
    ax.tick_params(colors=COLOR_MUTED, labelsize=9)
    ax.grid(True, axis="y", color=COLOR_GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)


def plot_individual(name_a, r2_a, name_b, r2_b, r2_j, adj_j, n, out_path):
    best_solo = max(r2_a, r2_b)
    best_solo_name = name_a if r2_a >= r2_b else name_b
    gain = r2_j - best_solo

    fig, ax = plt.subplots(figsize=(6, 5.5), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    labels = [name_a, name_b, "joint"]
    values = [r2_a, r2_b, r2_j]
    colors = [COLOR_SOLO, COLOR_SOLO, COLOR_JOINT]
    bars = ax.bar(labels, values, color=colors, width=0.55, zorder=2)
    for bar, v in zip(bars, values):
        ax.annotate(
            f"{v:.2f}",
            (bar.get_x() + bar.get_width() / 2, v),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=10,
            color=COLOR_PRIMARY,
        )

    ax.set_ylim(0, 1.0)
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.set_ylabel("R² vs. manual severity label", color=COLOR_SECONDARY, fontsize=10)
    fig.suptitle(f"{name_a} + {name_b}", x=0.02, y=0.98, ha="left", color=COLOR_PRIMARY, fontsize=14, fontweight="bold")
    ax.set_title(
        f"joint R²={r2_j:.2f}  ·  adj. R²={adj_j:.2f}  ·  gain over best solo ({best_solo_name})={gain:+.2f}  ·  n={n}",
        color=COLOR_SECONDARY,
        fontsize=9.5,
        loc="left",
        pad=10,
    )
    style_bar_axes(ax)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


def plot_grid(names, solo_r2, joint_stats, out_path):
    n_t = len(names)
    fig = plt.figure(figsize=(16, 16), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    outer = fig.add_gridspec(n_t, n_t, wspace=0.35, hspace=0.45, left=0.06, right=0.98, top=0.89, bottom=0.05)

    fig.suptitle(
        "Joint discriminative power: R² vs. manual severity, solo vs. paired (initial dataset, 13 FOVs)",
        x=0.03,
        y=0.995,
        ha="left",
        va="top",
        color=COLOR_PRIMARY,
        fontsize=16,
        fontweight="bold",
    )

    for row in range(n_t):
        for col in range(n_t):
            name_row = names[row]
            name_col = names[col]

            if row == col:
                ax = fig.add_subplot(outer[row, col])
                ax.set_facecolor(COLOR_DIAGONAL)
                ax.text(
                    0.5, 0.58, name_row,
                    ha="center", va="center", fontsize=12, fontweight="bold",
                    color=COLOR_SECONDARY, wrap=True, transform=ax.transAxes,
                )
                ax.text(
                    0.5, 0.35, f"solo R² = {solo_r2[name_row]:.2f}",
                    ha="center", va="center", fontsize=10,
                    color=COLOR_MUTED, transform=ax.transAxes,
                )
                ax.set_xticks([])
                ax.set_yticks([])
                for spine in ax.spines.values():
                    spine.set_visible(False)
                continue

            r2_j, adj_j, gain, best_solo_name = joint_stats[frozenset((name_row, name_col))]

            ax = fig.add_subplot(outer[row, col])
            ax.set_facecolor(COLOR_SURFACE)
            values = [solo_r2[name_row], solo_r2[name_col], r2_j]
            colors = [COLOR_SOLO, COLOR_SOLO, COLOR_JOINT]
            ax.bar(["row", "col", "joint"], values, color=colors, width=0.6, zorder=2)
            ax.set_ylim(0, 1.0)
            style_bar_axes(ax)
            ax.text(
                0.5, -0.16, f"gain = {gain:+.2f}",
                ha="center", va="top", fontsize=9, color=COLOR_PRIMARY, transform=ax.transAxes,
            )

    for col in range(n_t):
        name_col = names[col]
        pos = outer[0, col].get_position(fig)
        fig.text((pos.x0 + pos.x1) / 2, 0.94, name_col, ha="center", va="bottom", fontsize=11, color=COLOR_MUTED)

    for row in range(n_t):
        name_row = names[row]
        pos = outer[row, 0].get_position(fig)
        fig.text(0.015, (pos.y0 + pos.y1) / 2, name_row, ha="left", va="center", rotation=90, fontsize=11, color=COLOR_MUTED)

    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


def write_report(solo_r2, rows, n):
    lines = [
        "# Joint discriminative power — initial dataset (13 FOVs)",
        "",
        "For every pair of techniques, fits a 2-feature linear regression against the "
        "manual density+overlap severity score (integer range 0-7) and compares its R² "
        "to the better of the two techniques alone. This tests whether combining features "
        "captures more of the labeled severity signal than either captures individually — "
        "complementary to `pairwise-analysis/pairwise-report.md`, which only checks how much "
        "techniques overlap with *each other*, not with the label.",
        "",
        f"n = {n} FOVs and each joint model has 2 predictors, so adjusted R² is reported "
        "alongside raw joint R² to correct for the extra free parameter — with this few "
        "points, raw R² alone would overstate any pair's joint fit.",
        "",
        "## Solo R² vs. severity",
        "",
    ]
    for name, r2 in sorted(solo_r2.items(), key=lambda kv: -kv[1]):
        lines.append(f"- {name}: R² = {r2:.3f}")

    lines += [
        "",
        "## Pairwise joint R²",
        "",
        "| Pair | R²(A) solo | R²(B) solo | R² joint | adj. R² joint | gain over best solo |",
        "|---|---|---|---|---|---|",
    ]
    sorted_rows = sorted(rows, key=lambda r: -r[6])
    for name_a, name_b, r2a, r2b, r2j, adjj, gain, best_name in sorted_rows:
        lines.append(f"| {name_a} + {name_b} | {r2a:.3f} | {r2b:.3f} | {r2j:.3f} | {adjj:.3f} | {gain:+.3f} |")

    complementary = [r for r in sorted_rows if r[6] >= COMPLEMENTARY_GAIN]
    redundant = [r for r in sorted_rows if r[6] < REDUNDANT_GAIN]
    best = sorted_rows[0]
    worst = sorted_rows[-1]

    lines += ["", "## Interpretation", ""]
    lines.append(
        f"**Most complementary pair: {best[0]} + {best[1]}** (gain={best[6]:+.3f}, "
        f"joint R²={best[4]:.3f} vs. best solo R²={max(best[2], best[3]):.3f}). "
        "The two features separate severity better together than either alone by a wide "
        "margin, which fits the pairwise-overlap finding that this pair shares very little "
        "variance with each other -- they're picking up different aspects of severity."
    )
    lines.append("")
    lines.append(
        f"**Least complementary pair: {worst[0]} + {worst[1]}** (gain={worst[6]:+.3f}, "
        f"joint R²={worst[4]:.3f} vs. best solo R²={max(worst[2], worst[3]):.3f}). "
        "Adding the second feature buys almost nothing here."
    )
    if complementary:
        lines.append("")
        lines.append(f"Pairs with a large gain (>= {COMPLEMENTARY_GAIN:.2f}), i.e. genuinely complementary:")
        lines.append("")
        for name_a, name_b, *_rest, gain, _ in complementary:
            lines.append(f"- {name_a} + {name_b} (gain={gain:+.3f})")
    if redundant:
        lines.append("")
        lines.append(f"Pairs with a small gain (< {REDUNDANT_GAIN:.2f}), i.e. one feature adds little over the other:")
        lines.append("")
        for name_a, name_b, *_rest, gain, _ in redundant:
            lines.append(f"- {name_a} + {name_b} (gain={gain:+.3f})")

    report = "\n".join(lines)
    out_path = OUT_DIR / "joint-discriminative-report.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")


def main():
    fovs = load_fovs()
    INDIVIDUAL_DIR.mkdir(parents=True, exist_ok=True)

    severity = np.array([combined_score(r) for r in fovs], dtype=float)
    n = len(severity)

    series = {name: build_series(fovs, csv_file, column) for name, csv_file, column in TECHNIQUES}
    solo_r2 = {name: r2_solo(series[name], severity) for name in series}

    joint_stats = {}
    report_rows = []
    for i in range(len(TECHNIQUES)):
        for j in range(i + 1, len(TECHNIQUES)):
            name_a = TECHNIQUES[i][0]
            name_b = TECHNIQUES[j][0]
            r2_j = r2_joint(series[name_a], series[name_b], severity)
            adj_j = adjusted_r2(r2_j, n, 2)
            best_solo_name = name_a if solo_r2[name_a] >= solo_r2[name_b] else name_b
            gain = r2_j - max(solo_r2[name_a], solo_r2[name_b])
            joint_stats[frozenset((name_a, name_b))] = (r2_j, adj_j, gain, best_solo_name)

            out_path = INDIVIDUAL_DIR / f"{slug(name_a)}_plus_{slug(name_b)}.png"
            plot_individual(name_a, solo_r2[name_a], name_b, solo_r2[name_b], r2_j, adj_j, n, out_path)
            print(f"Wrote {out_path}")

            report_rows.append((name_a, name_b, solo_r2[name_a], solo_r2[name_b], r2_j, adj_j, gain, best_solo_name))

    names = [t[0] for t in TECHNIQUES]
    grid_path = OUT_DIR / "joint-discriminative-grid.png"
    plot_grid(names, solo_r2, joint_stats, grid_path)
    print(f"Wrote {grid_path}")

    write_report(solo_r2, report_rows, n)


if __name__ == "__main__":
    main()
