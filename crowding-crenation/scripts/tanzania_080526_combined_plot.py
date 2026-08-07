"""Combine the v2.1 and v2.2 KTR-72502946 results (scripts/tanzania_080526.py and
tanzania_080526_rescore.py) into one plot: three point-groups per density x Rouleaux grid
cell -- manual annotation, v2.1 prediction, v2.2 (recalibrated) prediction -- instead of the
two separate before/after plots. Fluorescent-spot-positive FOVs are starred in every group,
same as the individual plots.

Usage:
    python scripts/tanzania_080526_combined_plot.py
"""
import csv
import random
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "ai-first"))

from _v2_common import (  # noqa: E402
    COLOR_AXIS,
    COLOR_GRID,
    COLOR_MINE,
    COLOR_MUTED,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_SURFACE,
    DENSITY_LEVELS,
    JITTER_SEED,
    OVERLAP_LEVELS,
    density_ordinal,
    display_level,
    overlap_ordinal,
)

COLOR_V21 = "#eb6834"
COLOR_V22 = "#3a9b6f"  # third categorical slot, distinct from the existing blue/orange pair

OUT_DIR = ROOT / "data" / "results" / "tanzania-080526"


def load_rows(path):
    return list(csv.DictReader(open(path)))


def main():
    v21_rows = load_rows(OUT_DIR / "merged-results.csv")
    v22_rows = load_rows(OUT_DIR / "merged-results-calibrated.csv")
    v22_by_fov = {int(r["fov_id"]): r for r in v22_rows}

    records = []
    for r in v21_rows:
        fov_id = int(r["fov_id"])
        v22 = v22_by_fov[fov_id]
        records.append({
            "fov_id": fov_id,
            "manual": (density_ordinal(r["manual_density"]), overlap_ordinal(r["manual_overlap"])),
            "v21": (density_ordinal(r["model_density_label"]), overlap_ordinal(r["model_overlap_label"])),
            "v22": (density_ordinal(v22["model_density_label"]), overlap_ordinal(v22["model_overlap_label"])),
            "fluorescent_present": r["fluorescent_present"] == "True",
        })

    rng = random.Random(JITTER_SEED)
    fig, ax = plt.subplots(figsize=(11, 7), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    def scatter_group(points, color, x_shift, marker, label, fov_ids=None):
        if not points:
            return
        xs = [ov + x_shift + rng.uniform(-0.09, 0.09) for _, ov in points]
        ys = [dn + rng.uniform(-0.16, 0.16) for dn, _ in points]
        size = 70 if marker == "*" else 20
        ax.scatter(xs, ys, s=size, marker=marker, color=color, alpha=0.65 if marker == "*" else 0.5,
                   linewidths=0, zorder=4 if marker == "*" else 3, label=label)
        if fov_ids:
            for x, y, fov_id in zip(xs, ys, fov_ids):
                ax.annotate(str(fov_id), (x, y), xytext=(4, 4), textcoords="offset points",
                            fontsize=6, color=COLOR_SECONDARY, zorder=5)

    is_fluor = [r["fluorescent_present"] for r in records]
    fov_ids_all = [r["fov_id"] for r in records]
    star_fov_ids = [fid for fid, f in zip(fov_ids_all, is_fluor) if f]

    groups = [
        ("manual", COLOR_MINE, -0.22, "Mine (manual annotation)"),
        ("v21", COLOR_V21, 0.0, "score_fov_v2 (v2.1)"),
        ("v22", COLOR_V22, 0.22, "score_fov_v2 (v2.2 recalibrated)"),
    ]
    for key, color, x_shift, label in groups:
        pts = [r[key] for r in records]
        plain = [p for p, f in zip(pts, is_fluor) if not f]
        starred = [p for p, f in zip(pts, is_fluor) if f]
        scatter_group(plain, color, x_shift, "o", label)
        scatter_group(starred, color, x_shift, "*", f"{label}, fluorescent-positive", fov_ids=star_fov_ids)

    ax.set_xticks(range(len(OVERLAP_LEVELS)))
    ax.set_xticklabels([display_level(l) for l in OVERLAP_LEVELS], fontsize=10, rotation=15, ha="right")
    ax.set_xlim(-0.6, len(OVERLAP_LEVELS) - 0.4)
    for i in range(1, len(OVERLAP_LEVELS)):
        ax.axvline(i - 0.5, color=COLOR_GRID, linewidth=1, zorder=0)

    ax.set_yticks(range(len(DENSITY_LEVELS)))
    ax.set_yticklabels([display_level(l) for l in DENSITY_LEVELS], fontsize=10)
    ax.set_ylim(-0.5, len(DENSITY_LEVELS) - 0.5)
    for i in range(1, len(DENSITY_LEVELS)):
        ax.axhline(i - 0.5, color=COLOR_GRID, linewidth=1, zorder=0)

    ax.tick_params(colors=COLOR_MUTED)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(COLOR_AXIS)
    ax.set_axisbelow(True)

    ax.set_xlabel("Rouleaux level", color=COLOR_SECONDARY, fontsize=11)
    ax.set_ylabel("Density level", color=COLOR_SECONDARY, fontsize=11)

    legend_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLOR_MINE, markersize=8, label="Mine (manual annotation)"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLOR_V21, markersize=8, label="score_fov_v2 (v2.1)"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLOR_V22, markersize=8, label="score_fov_v2 (v2.2 recalibrated)"),
        Line2D([0], [0], marker="*", color="none", markerfacecolor=COLOR_MUTED, markersize=12, label="Fluorescent-spot positive"),
    ]
    ax.legend(handles=legend_handles, loc="upper right", frameon=False, fontsize=8.5)

    n_fluor = sum(is_fluor)
    fig.suptitle(
        "KTR-72502946 (Tanzania) -- manual annotation vs. v2.1 vs. v2.2 (recalibrated), combined",
        x=0.02, y=0.98, ha="left", color=COLOR_PRIMARY, fontsize=14, fontweight="bold",
    )
    ax.set_title(
        f"n = {len(records)} FOVs per group, jittered within each grid cell; "
        f"{n_fluor} FOVs ({n_fluor / len(records):.1%}) fluorescent-spot positive",
        loc="left", color=COLOR_SECONDARY, fontsize=10, pad=10,
    )

    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out_path = OUT_DIR / "jitter-bucket-comparison-combined.png"
    fig.savefig(out_path, facecolor=COLOR_SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
