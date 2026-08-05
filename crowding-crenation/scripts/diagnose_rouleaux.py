"""Diagnose why score_new_slide.py's rouleaux_fraction shows no positive relationship
with manual overlap labels (see data/results/tanzania-073026/tanzania-comparison/README.md).

Visualizes score_new_slide.py's exact watershed/segmentation/degree logic on FOVs
manually tagged "heavy rouleaux", each paired with a "no rouleaux" FOV matched on
coverage_fraction (so density isn't a confound in the visual comparison) -- this
isolates whether the current heuristic (count cells with exactly 2 touching
neighbors positioned roughly opposite each other, INLINE_COS_THRESHOLD=-0.7) is
actually picking up the visual pattern the manual "rouleaux" tag refers to.

Per-cell categories drawn:
  cyan   -- ordinary segmented cell (not flagged, not oversized)
  red    -- flagged as "inline" (counts toward rouleaux_fraction)
  orange -- oversized/merged blob (area > MERGED_AREA_RATIO * reference_area) --
            a likely watershed under-segmentation artifact in crowded fields

Usage:
    python scripts/diagnose_rouleaux.py
"""
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from skimage.measure import regionprops_table

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "ai-first"))
from compare_tanzania_labels import MANUAL_CSV, load_manual  # noqa: E402
from score_new_slide import FRAGMENT_AREA_RATIO, INLINE_COS_THRESHOLD, MERGED_AREA_RATIO, segment, touching_pairs  # noqa: E402
from tanzania_comparison import AI_FIRST_CSV, load_scores_csv  # noqa: E402

DPC_DIR = ROOT / "data" / "new" / "KTR-72502948" / "dpc"
OUT_DIR = ROOT / "data" / "results" / "tanzania-073026" / "rouleaux-diagnostic"

COLOR_NORMAL = "#2a78d6"
COLOR_INLINE = "#d62a2a"
COLOR_MERGED = "#eb9c34"
COLOR_SURFACE = "#fcfcfb"
COLOR_PRIMARY = "#0b0b0b"
COLOR_SECONDARY = "#52514e"

TARGET_HEAVY_ROULEAUX = [205, 206, 210, 215]  # spread across this group's coverage_fraction range


def analyze(idx):
    path = DPC_DIR / f"dpc-{idx:03d}-KTR-72502948.png"
    gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    mask, labels_raw = segment(gray)
    coverage_fraction = float(mask.mean())

    raw_props = regionprops_table(labels_raw, properties=("label", "area"))
    reference_area = np.percentile(raw_props["area"], 75)
    fragment_floor = FRAGMENT_AREA_RATIO * reference_area
    merged_ceiling = MERGED_AREA_RATIO * reference_area

    keep_labels = raw_props["label"][raw_props["area"] >= fragment_floor]
    labels = np.where(np.isin(labels_raw, keep_labels), labels_raw, 0)

    props = regionprops_table(labels, properties=("label", "area", "centroid"))
    n_cells = len(props["label"])
    label_to_idx = {lab: i for i, lab in enumerate(props["label"])}
    centroids = np.stack([props["centroid-0"], props["centroid-1"]], axis=1)
    areas = np.array(props["area"], dtype=np.float64)

    neighbors = defaultdict(list)
    for a, b in touching_pairs(labels):
        neighbors[a].append(b)
        neighbors[b].append(a)

    degree = np.zeros(n_cells, dtype=np.int32)
    inline_flag = np.zeros(n_cells, dtype=bool)
    for lab, i in label_to_idx.items():
        nbrs = neighbors.get(lab, [])
        degree[i] = len(nbrs)
        if len(nbrs) == 2:
            c = centroids[i]
            n1 = centroids[label_to_idx[nbrs[0]]]
            n2 = centroids[label_to_idx[nbrs[1]]]
            v1, v2 = n1 - c, n2 - c
            denom = (np.linalg.norm(v1) * np.linalg.norm(v2)) or 1.0
            cos_angle = float(np.dot(v1, v2) / denom)
            if cos_angle < INLINE_COS_THRESHOLD:
                inline_flag[i] = True

    n_inline = int(inline_flag.sum())
    n_merged = int((areas > merged_ceiling).sum())
    rouleaux_fraction = n_inline / n_cells if n_cells else 0.0

    category = np.zeros(labels.shape, dtype=np.uint8)  # 0=bg, 1=normal, 2=inline, 3=merged
    for lab, i in label_to_idx.items():
        region = labels == lab
        if inline_flag[i]:
            category[region] = 2
        elif areas[i] > merged_ceiling:
            category[region] = 3
        else:
            category[region] = 1

    return {
        "gray": gray, "category": category, "n_cells": n_cells, "n_inline": n_inline,
        "n_merged": n_merged, "rouleaux_fraction": rouleaux_fraction,
        "coverage_fraction": coverage_fraction,
    }


def overlay_color(ax, selection, color, alpha=0.55):
    rgba = np.zeros((*selection.shape, 4))
    rgba[selection] = mcolors.to_rgba(color, alpha)
    ax.imshow(rgba)


def draw_panel(ax, result, title):
    ax.imshow(result["gray"], cmap="gray")
    overlay_color(ax, result["category"] == 1, COLOR_NORMAL)
    overlay_color(ax, result["category"] == 2, COLOR_INLINE)
    overlay_color(ax, result["category"] == 3, COLOR_MERGED)
    ax.axis("off")
    ax.set_title(title, loc="left", color=COLOR_PRIMARY, fontsize=10, fontweight="bold")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manual = load_manual(MANUAL_CSV)
    ai_first = load_scores_csv(AI_FIRST_CSV)
    no_rouleaux_ids = [i for i in manual if manual[i]["rouleaux"] == "no rouleaux"]

    pairs = []
    for heavy_idx in TARGET_HEAVY_ROULEAUX:
        cov = ai_first[heavy_idx]["coverage_fraction"]
        control_idx = min(no_rouleaux_ids, key=lambda i: abs(ai_first[i]["coverage_fraction"] - cov))
        pairs.append((heavy_idx, control_idx))

    fig, axes = plt.subplots(len(pairs), 2, figsize=(11, 5.6 * len(pairs)), dpi=130)
    fig.patch.set_facecolor(COLOR_SURFACE)

    summary_rows = []
    for row, (heavy_idx, control_idx) in enumerate(pairs):
        for col, idx in enumerate((heavy_idx, control_idx)):
            r = analyze(idx)
            tag = manual[idx]["rouleaux"]
            title = (
                f"FOV {idx} -- manual: {tag}\n"
                f"coverage={r['coverage_fraction']:.3f}  rouleaux_fraction={r['rouleaux_fraction']:.3f}\n"
                f"n_cells={r['n_cells']}  n_inline(red)={r['n_inline']}  n_merged(orange)={r['n_merged']}"
            )
            draw_panel(axes[row, col], r, title)
            summary_rows.append({
                "pair": row, "idx": idx, "manual_rouleaux": tag,
                "coverage_fraction": r["coverage_fraction"], "rouleaux_fraction": r["rouleaux_fraction"],
                "n_cells": r["n_cells"], "n_inline": r["n_inline"], "n_merged": r["n_merged"],
            })
        print(f"pair {row}: heavy={heavy_idx} control={control_idx}")

    legend_elements = [
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=COLOR_NORMAL, markersize=12, label="ordinary cell"),
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=COLOR_INLINE, markersize=12, label="flagged inline (counts as rouleaux)"),
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=COLOR_MERGED, markersize=12, label="oversized/merged blob"),
    ]
    fig.legend(handles=legend_elements, loc="upper right", frameon=False, fontsize=10)
    fig.suptitle(
        "Heavy rouleaux (left) vs. coverage-matched no-rouleaux (right) -- score_new_slide.py's own segmentation",
        x=0.01, y=0.998, ha="left", color=COLOR_PRIMARY, fontsize=13, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out_path = OUT_DIR / "heavy-rouleaux-vs-control.png"
    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)
    print(f"wrote {out_path}")

    import csv
    csv_path = OUT_DIR / "diagnostic-summary.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
