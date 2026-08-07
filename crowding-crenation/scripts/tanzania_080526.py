"""Run the (already-calibrated, no recalibration) v2 density/Rouleaux scorer and the
fluorescence project's overexposure ("fluorescent spot") detector against slide
KTR-72502946 (Tanzania), streaming both the dpc and fluorescent images directly from
GCS (gs://tanzania_02032026/TZ2025-Box5/KTR-72502946/) -- nothing is downloaded to disk.

Produces a jittered density x Rouleaux grid (see plot_bucket_comparison_v2.py, which this
extends) with two point groups -- manual annotation ("Mine") vs. v2 model prediction -- and
marks whichever of those points belong to a FOV the fluorescence detector calls positive
with a star instead of a circle.

The fluorescence detector (fluorescence/src/overexposure.py) is imported directly from its
sibling project rather than duplicated -- see fluorescence/README.md for what it detects.
It has no relative imports of its own (just cv2/numpy), so a plain file-path import avoids
the `src`-package-name collision that would happen if all three sibling projects' `src`
packages ended up in sys.modules under the same name.

Usage:
    python scripts/tanzania_080526.py
"""
import csv
import importlib.util
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import matplotlib
import numpy as np

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
    parse_tanzania_tags,
)
from score_fov_v2 import load_params, score_image_v2  # noqa: E402
from src.pipeline import GCSPath, _gcs_client  # noqa: E402

COLOR_MODEL = "#eb6834"  # matches plot_bucket_comparison_v2.py / compare_tanzania_labels.py

BUCKET = "tanzania_02032026"
SLIDE_PREFIX = "TZ2025-Box5/KTR-72502946"
SLIDE_ID = "KTR-72502946"
N_FOVS = 324

MANUAL_CSV = ROOT / "data" / "labels" / "tanzania-080526" / "KTR-72502946-annotated.csv"
V2_PARAMS = ROOT / "data" / "results" / "density-rouleaux-v2" / "density_overlap_v2.1_params.json"
OUT_DIR = ROOT / "data" / "results" / "tanzania-080526"

FLUORESCENCE_ROOT = ROOT.parent / "fluorescence"


def _load_overexposure_detector():
    spec = importlib.util.spec_from_file_location(
        "fluorescence_overexposure", FLUORESCENCE_ROOT / "src" / "overexposure.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.detect_overexposure


detect_overexposure = _load_overexposure_detector()


def load_manual(path):
    rows = list(csv.DictReader(open(path)))
    out = {}
    for r in rows:
        density_label, overlap_label = parse_tanzania_tags(r["tags"])
        out[int(r["fov_id"])] = (density_label, overlap_label)
    return out


def load_fluorescent_bgr(fov_id):
    blob_name = f"{SLIDE_PREFIX}/fluorescent-{fov_id:03d}-{SLIDE_ID}.png"
    data = _gcs_client().bucket(BUCKET).blob(blob_name).download_as_bytes()
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not decode image: gs://{BUCKET}/{blob_name}")
    return image, blob_name


def process_fov(fov_id, v2_params):
    dpc_blob = f"{SLIDE_PREFIX}/dpc-{fov_id:03d}-{SLIDE_ID}.png"
    v2_result = score_image_v2(GCSPath(BUCKET, dpc_blob), v2_params)

    fluor_image, fluor_blob = load_fluorescent_bgr(fov_id)
    overexposure = detect_overexposure(fluor_image)

    return {
        "fov_id": fov_id,
        "dpc_path": f"gs://{BUCKET}/{dpc_blob}",
        "fluorescent_path": f"gs://{BUCKET}/{fluor_blob}",
        "model_density_label": v2_result["density_label"],
        "model_overlap_label": v2_result["overlap_label"],
        "model_density_score": v2_result["density_score"],
        "model_overlap_score": v2_result["overlap_score"],
        "fluorescent_present": overexposure.present,
        "fluorescent_confidence": overexposure.confidence,
        "fluorescent_contrast_ratio": overexposure.contrast_ratio,
    }


def run_pipeline():
    v2_params = load_params(V2_PARAMS)

    results = {}
    errors = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {pool.submit(process_fov, fov_id, v2_params): fov_id for fov_id in range(1, N_FOVS + 1)}
        for i, future in enumerate(futures, 1):
            fov_id = futures[future]
            try:
                results[fov_id] = future.result()
            except Exception as e:
                errors.append((fov_id, str(e)))
            if i % 50 == 0 or i == len(futures):
                print(f"  {i}/{len(futures)} FOVs processed")

    if errors:
        print(f"warning: {len(errors)} FOVs failed: {errors}")

    return results


def write_merged_csv(results, manual, out_path):
    fieldnames = [
        "fov_id", "manual_density", "manual_overlap",
        "model_density_label", "model_overlap_label", "model_density_score", "model_overlap_score",
        "fluorescent_present", "fluorescent_confidence", "fluorescent_contrast_ratio",
        "dpc_path", "fluorescent_path",
    ]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for fov_id in sorted(results):
            r = results[fov_id]
            manual_density, manual_overlap = manual[fov_id]
            writer.writerow({
                "fov_id": fov_id,
                "manual_density": manual_density,
                "manual_overlap": manual_overlap,
                **{k: r[k] for k in fieldnames if k in r},
            })


def plot_jitter_grid(records, out_path, model_label="score_fov_v2 (model)"):
    """Density x Rouleaux grid, jittered scatter per cell, mine vs. model, fluorescent-positive
    FOVs starred instead of circled. Mirrors scripts/ai-first/plot_bucket_comparison_v2.py.
    """
    rng = random.Random(JITTER_SEED)
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    def scatter_group(points, color, x_shift, marker, label, fov_ids=None):
        if not points:
            return
        xs = [ov + x_shift + rng.uniform(-0.14, 0.14) for _, ov in points]
        ys = [dn + rng.uniform(-0.16, 0.16) for dn, _ in points]
        size = 60 if marker == "*" else 24
        ax.scatter(xs, ys, s=size, marker=marker, color=color, alpha=0.6 if marker == "*" else 0.5,
                   linewidths=0, zorder=4 if marker == "*" else 3, label=label)
        if fov_ids:
            for x, y, fov_id in zip(xs, ys, fov_ids):
                ax.annotate(str(fov_id), (x, y), xytext=(4, 4), textcoords="offset points",
                            fontsize=6, color=COLOR_SECONDARY, zorder=5)

    mine_pts = [(density_ordinal(r["manual_density"]), overlap_ordinal(r["manual_overlap"])) for r in records]
    model_pts = [(density_ordinal(r["model_density_label"]), overlap_ordinal(r["model_overlap_label"])) for r in records]
    is_fluor = [r["fluorescent_present"] for r in records]
    fov_ids_all = [r["fov_id"] for r in records]

    mine_plain = [p for p, f in zip(mine_pts, is_fluor) if not f]
    mine_star = [p for p, f in zip(mine_pts, is_fluor) if f]
    model_plain = [p for p, f in zip(model_pts, is_fluor) if not f]
    model_star = [p for p, f in zip(model_pts, is_fluor) if f]
    star_fov_ids = [fid for fid, f in zip(fov_ids_all, is_fluor) if f]

    scatter_group(mine_plain, COLOR_MINE, -0.15, "o", "Mine (manual annotation)")
    scatter_group(model_plain, COLOR_MODEL, 0.15, "o", model_label)
    scatter_group(mine_star, COLOR_MINE, -0.15, "*", "Mine, fluorescent-positive", fov_ids=star_fov_ids)
    scatter_group(model_star, COLOR_MODEL, 0.15, "*", "Model, fluorescent-positive", fov_ids=star_fov_ids)

    ax.set_xticks(range(len(OVERLAP_LEVELS)))
    ax.set_xticklabels([display_level(l) for l in OVERLAP_LEVELS], fontsize=10, rotation=15, ha="right")
    ax.set_xlim(-0.5, len(OVERLAP_LEVELS) - 0.5)
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
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLOR_MODEL, markersize=8, label=model_label),
        Line2D([0], [0], marker="*", color="none", markerfacecolor=COLOR_MUTED, markersize=12, label="Fluorescent-spot positive"),
    ]
    ax.legend(handles=legend_handles, loc="upper right", frameon=False, fontsize=9)

    n_fluor = sum(is_fluor)
    fig.suptitle(
        f"KTR-72502946 (Tanzania) -- manual annotations vs. {model_label} predictions",
        x=0.02, y=0.98, ha="left", color=COLOR_PRIMARY, fontsize=14, fontweight="bold",
    )
    ax.set_title(
        f"n = {len(records)} FOVs each, jittered within each grid cell; "
        f"{n_fluor} FOVs ({n_fluor / len(records):.1%}) fluorescent-spot positive",
        loc="left", color=COLOR_SECONDARY, fontsize=10, pad=10,
    )

    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out_path, facecolor=COLOR_SURFACE, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manual = load_manual(MANUAL_CSV)

    print(f"Scoring {N_FOVS} FOVs from gs://{BUCKET}/{SLIDE_PREFIX}/ (dpc via score_fov_v2, fluorescent via overexposure detector)...")
    results = run_pipeline()

    common = sorted(set(results) & set(manual))
    if len(common) != N_FOVS:
        print(f"warning: expected {N_FOVS} FOVs, got {len(common)} in common (manual={len(manual)}, scored={len(results)})")

    merged_csv = OUT_DIR / "merged-results.csv"
    write_merged_csv(results, manual, merged_csv)
    print(f"wrote {merged_csv}")

    records = []
    for fov_id in common:
        manual_density, manual_overlap = manual[fov_id]
        records.append({**results[fov_id], "manual_density": manual_density, "manual_overlap": manual_overlap})

    plot_path = OUT_DIR / "jitter-bucket-comparison.png"
    plot_jitter_grid(records, plot_path, model_label="score_fov_v2 (v2.1)")
    print(f"wrote {plot_path}")

    exact_density = sum(1 for r in records if r["manual_density"] == r["model_density_label"]) / len(records)
    exact_overlap = sum(1 for r in records if r["manual_overlap"] == r["model_overlap_label"]) / len(records)
    n_fluor = sum(1 for r in records if r["fluorescent_present"])
    print(f"n={len(records)}, density exact-match={exact_density:.1%}, Rouleaux exact-match={exact_overlap:.1%}")
    print(f"fluorescent-spot positive: {n_fluor}/{len(records)} ({n_fluor / len(records):.1%})")


if __name__ == "__main__":
    main()
