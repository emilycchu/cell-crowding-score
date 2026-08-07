"""Run the full overexposure-detection pipeline (ratio gate -> anisotropy-fft demotion ->
diffuse-fov sustained-footprint check) against data/labels/overexposure-diverse-080726.csv,
streaming every FOV directly from GCS (no local disk cache).

Ground truth in this label set is the annotator's "spot" column: whether a genuine
fluorescent spot (real parasite signal) is present, independent of whether the FOV also
looks overexposed. `detect_overexposure()`'s `present` flag means "the overexposed-halo
ARTIFACT is present" -- per fluorescence/README.md this is "a preprocessing/triage step
before any downstream model (e.g. spot/RBC detection) sees the image", i.e. present=True is
meant to gate a FOV OUT before a spot detector ever runs. So the natural predicted label for
this dataset's ground truth is the complement: predicted_spot_present = not present. Under
that mapping, a false negative (spot_truth=yes, predicted=no) is the costly error: the
triage step wrongly discarding a real spot as an artifact.

The diffuse-fov step (diffuse_candidate/diffuse_halo_flag) is advisory-only in
src/overexposure.py -- never changes `present`. This script computes it for every row either
way, and additionally reports what `present` would become if that step's flag WERE folded
into the decision (present_folded = present_base or diffuse_halo_flag), for comparison. See
data/results/overexposed-diverse-080726/README.md for the resulting confusion matrices.

For rows where the diffuse-fov step's flag depends on neighbor context (diffuse_candidate ==
True), this fetches the 2 immediately-preceding fov_ids from GCS (same sample_id/country) to
run diffuse_halo_flag's neighbor-trend check, exactly as scripts/scan_diffuse_candidates.py
does for a sequential scan walk.

Usage:
    python scripts/run_overexposed_diverse_test.py
    python scripts/run_overexposed_diverse_test.py --limit 5
"""
import argparse
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from src.gcs_fov_multi import load_fov_image
from src.overexposure import (
    ANISOTROPY_THRESHOLD,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    HIGH_PERCENTILE,
    LOW_PERCENTILE,
    MASK_FRAC,
    RATIO_THRESHOLD,
    _largest_component,
    _region_anisotropy,
    _small_and_illumination,
    _sustained_footprint,
    detect_overexposure,
    diffuse_candidate,
    diffuse_halo_flag,
)

LABELS_CSV = Path(__file__).resolve().parent.parent / "data" / "labels" / "overexposure-diverse-080726.csv"
OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "results" / "overexposed-diverse-080726" / "results.csv"
NEIGHBOR_WINDOW = 2  # matches scripts/scan_diffuse_candidates.py


def timed_stages(image_bgr):
    """Re-run detect_overexposure()'s exact stage sequence (same private helpers, same
    branching) purely to measure per-stage wall time. Never used as the source of truth for
    present/confidence/etc. -- that's always detect_overexposure()'s own return value -- so a
    timing-only duplicate can't skew the reported detection results.
    """
    t0 = time.perf_counter()
    small, illumination = _small_and_illumination(image_bgr)
    baseline = float(np.percentile(illumination, LOW_PERCENTILE))
    peak = float(np.percentile(illumination, HIGH_PERCENTILE))
    contrast_ratio = peak / max(baseline, 1e-3)
    mask_thresh = baseline + MASK_FRAC * (peak - baseline)
    mask = (illumination > mask_thresh).astype(np.uint8)
    contour, bbox = _largest_component(mask)
    present = contrast_ratio >= RATIO_THRESHOLD
    t1 = time.perf_counter()

    if present and contour is not None:
        _region_anisotropy(small, bbox)
    t2 = time.perf_counter()

    _sustained_footprint(illumination, baseline)
    t3 = time.perf_counter()

    return {
        "initial_test_s": t1 - t0,
        "anisotropy_s": t2 - t1,  # 0.0 when the ratio gate already failed (branch never runs)
        "diffuse_fov_s": t3 - t2,
    }


def try_fetch_neighbor(sample_id, fov_id, country):
    """Best-effort load of a neighboring fov_id for the diffuse-halo neighbor-trend check.
    Returns None (rather than raising) if the neighbor is out of range or missing -- the
    caller then simply has one fewer neighbor reading to compare against, same as
    scan_diffuse_candidates.py would if it started mid-scan.
    """
    if fov_id < 1:
        return None
    try:
        image, _ = load_fov_image(sample_id, fov_id, country)
    except Exception as exc:
        print(f"    [neighbor fov={fov_id} unavailable: {exc}]")
        return None
    return detect_overexposure(image)


def process_row(row):
    sample_id, fov_id, country = row["sample_id"], int(row["fov_id"]), row["country"]

    t0 = time.perf_counter()
    image, blob_uri = load_fov_image(sample_id, fov_id, country)
    fetch_s = time.perf_counter() - t0

    result = detect_overexposure(image)
    stage_timings = timed_stages(image)

    present_folded = result.present
    diffuse_flagged = False
    neighbor_fetch_s = 0.0
    if diffuse_candidate(result):
        t_n0 = time.perf_counter()
        neighbors = [
            n for n in (
                try_fetch_neighbor(sample_id, fov_id - delta, country)
                for delta in range(1, NEIGHBOR_WINDOW + 1)
            )
            if n is not None
        ]
        neighbor_fetch_s = time.perf_counter() - t_n0
        diffuse_flagged = diffuse_halo_flag(result, neighbors)
        present_folded = result.present or diffuse_flagged

    return {
        "sample_id": sample_id,
        "fov_id": fov_id,
        "country": country,
        "spot_truth": row["spot"].strip().lower(),
        "notes": (row.get("notes") or "").strip().lower(),
        "tags": row["tags"],
        "present_base": result.present,
        "present_folded": present_folded,
        "diffuse_halo_flag": diffuse_flagged,
        "predicted_spot_base": not result.present,
        "predicted_spot_folded": not present_folded,
        "confidence": result.confidence,
        "contrast_ratio": result.contrast_ratio,
        "baseline": result.baseline,
        "peak": result.peak,
        "area_fraction": result.area_fraction,
        "solidity": result.solidity,
        "anisotropy": result.anisotropy,
        "diffuse_radius": result.diffuse_radius,
        "diffuse_circularity": result.diffuse_circularity,
        "diffuse_centroid_x": result.diffuse_centroid_x,
        "diffuse_centroid_y": result.diffuse_centroid_y,
        "gcs_fetch_s": round(fetch_s, 4),
        "time_initial_test_s": round(stage_timings["initial_test_s"], 4),
        "time_anisotropy_s": round(stage_timings["anisotropy_s"], 4),
        "time_diffuse_fov_s": round(stage_timings["diffuse_fov_s"], 4),
        "neighbor_fetch_s": round(neighbor_fetch_s, 4),
        "blob_uri": blob_uri,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels-csv", type=Path, default=LABELS_CSV)
    parser.add_argument("--out-csv", type=Path, default=OUT_CSV)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.labels_csv)))
    if args.limit:
        rows = rows[: args.limit]

    out_rows = []
    for i, row in enumerate(rows):
        print(f"[{i + 1}/{len(rows)}] {row['sample_id']} fov={row['fov_id']} ({row['country']})", flush=True)
        try:
            out_rows.append(process_row(row))
        except Exception as exc:
            print(f"  [ERROR] {exc}", flush=True)
            out_rows.append({
                "sample_id": row["sample_id"], "fov_id": row["fov_id"], "country": row["country"],
                "spot_truth": row["spot"].strip().lower(), "notes": (row.get("notes") or "").strip().lower(),
                "tags": row["tags"], "error": str(exc),
            })

    fieldnames = sorted({k for r in out_rows for k in r.keys()},
                        key=lambda k: (k != "sample_id", k != "fov_id", k != "country", k))
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    n_errors = sum(1 for r in out_rows if "error" in r)
    print(f"\nWrote {len(out_rows)} rows ({n_errors} errors) to {args.out_csv}")


if __name__ == "__main__":
    main()
