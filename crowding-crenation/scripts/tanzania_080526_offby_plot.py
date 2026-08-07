"""Off-by-level error plot for the v2.2 (recalibrated) scoring of KTR-72502946
(tanzania-080526): for each FOV, x = the model's measured continuous severity score,
y = signed off-by amount (model's predicted ordinal level minus the manual ordinal level)
-- how far off from the annotation the model landed, and whether that error trends with
measured severity. One plot for density, one for Rouleaux, side by side in one figure.

Usage:
    python scripts/tanzania_080526_offby_plot.py
"""
import csv
import random
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "combined"))

from _v2_common import (  # noqa: E402
    COLOR_AXIS,
    COLOR_GRID,
    COLOR_MUTED,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_SURFACE,
    JITTER_SEED,
    density_ordinal,
    overlap_ordinal,
)

COLOR_V22 = "#3a9b6f"  # matches tanzania_080526_combined_plot.py's v2.2 color

OUT_DIR = ROOT / "data" / "results" / "tanzania-080526"
MERGED_CSV = OUT_DIR / "merged-results-calibrated.csv"


def load_records(path):
    rows = list(csv.DictReader(open(path)))
    out = []
    for r in rows:
        out.append({
            "fov_id": int(r["fov_id"]),
            "manual_density_ord": density_ordinal(r["manual_density"]),
            "model_density_ord": density_ordinal(r["model_density_label"]),
            "model_density_score": float(r["model_density_score"]),
            "manual_overlap_ord": overlap_ordinal(r["manual_overlap"]),
            "model_overlap_ord": overlap_ordinal(r["model_overlap_label"]),
            "model_overlap_score": float(r["model_overlap_score"]),
        })
    return out


def plot_axis(ax, records, score_key, model_ord_key, manual_ord_key, title, rng):
    scores = [r[score_key] for r in records]
    off_by = [r[model_ord_key] - r[manual_ord_key] for r in records]
    ys = [d + rng.uniform(-0.08, 0.08) for d in off_by]

    ax.set_facecolor(COLOR_SURFACE)
    ax.axhline(0, color=COLOR_AXIS, linewidth=1.3, zorder=2)
    for d in range(1, max(abs(min(off_by)), abs(max(off_by))) + 1):
        ax.axhline(d, color=COLOR_GRID, linewidth=0.8, zorder=0)
        ax.axhline(-d, color=COLOR_GRID, linewidth=0.8, zorder=0)
    ax.scatter(scores, ys, s=22, color=COLOR_V22, alpha=0.5, linewidths=0, zorder=3)

    n = len(records)
    exact = sum(1 for d in off_by if d == 0) / n
    off1 = sum(1 for d in off_by if abs(d) <= 1) / n
    ax.set_title(
        f"{title}  (exact={exact:.1%}, off-by-one={off1:.1%})",
        loc="left", color=COLOR_PRIMARY, fontsize=11, fontweight="bold", pad=10,
    )
    ax.set_xlabel("Measured severity (v2.2 composite score)", color=COLOR_SECONDARY, fontsize=10)
    ax.set_ylabel("Off-by amount (model level - manual level)", color=COLOR_SECONDARY, fontsize=10)
    ax.tick_params(colors=COLOR_MUTED, labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(COLOR_AXIS)
    ax.set_axisbelow(True)


def main():
    records = load_records(MERGED_CSV)
    rng = random.Random(JITTER_SEED)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)

    plot_axis(axes[0], records, "model_overlap_score", "model_overlap_ord", "manual_overlap_ord",
              "Rouleaux", rng)
    plot_axis(axes[1], records, "model_density_score", "model_density_ord", "manual_density_ord",
              "Density", rng)

    fig.suptitle(
        "KTR-72502946 (Tanzania) -- v2.2 off-by-level error vs. measured severity",
        x=0.015, y=0.99, ha="left", color=COLOR_PRIMARY, fontsize=14, fontweight="bold",
    )
    fig.text(0.015, 0.935, f"n = {len(records)} FOVs each, y jittered slightly to reduce overplotting",
             color=COLOR_SECONDARY, fontsize=9)

    fig.tight_layout(rect=(0, 0, 1, 0.91))
    out_path = OUT_DIR / "offby-vs-severity-v2.2.png"
    fig.savefig(out_path, facecolor=COLOR_SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
