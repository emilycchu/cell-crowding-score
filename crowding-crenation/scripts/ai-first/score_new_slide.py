"""From-scratch crowding/density/crenation scoring for a slide's raw DPC images.

Deliberately does not use any precomputed model output (e.g. the Cellpose
segmentation masks or detection_results/ already sitting in the GCS bucket) —
this is meant to be a pre-model triage step that works on raw pixels alone.
Segmentation here is classical CV (gradient texture-energy + distance-transform
watershed), not a pretrained network.
"""
import argparse
import csv
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.measure import regionprops_table
from skimage.segmentation import watershed

BG_SIGMA = 40          # gaussian sigma for flat-field background subtraction
ENERGY_KSIZE = 9       # box filter size for local gradient-energy
MIN_DISTANCE = 9       # min peak spacing for watershed markers (~typical cell radius)
INLINE_COS_THRESHOLD = -0.7   # neighbor-pair angle cosine below this = "in a line"
CRENATION_SOLIDITY_THRESHOLD = 0.75
FRAGMENT_AREA_RATIO = 0.35    # below this * reference cell area => segmentation noise, not a cell
MERGED_AREA_RATIO = 1.6       # above this * reference cell area => likely an unsplit doublet/clump


def segment(gray):
    """Binary cell-foreground mask + split-instance label image, from raw pixels only."""
    gray_f = gray.astype(np.float32)
    background = cv2.GaussianBlur(gray_f, (0, 0), sigmaX=BG_SIGMA)
    detail = gray_f - background

    grad_x = cv2.Sobel(detail, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(detail, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = cv2.magnitude(grad_x, grad_y)
    energy = np.sqrt(cv2.boxFilter(grad_mag * grad_mag, -1, (ENERGY_KSIZE, ENERGY_KSIZE)))
    energy_u8 = cv2.normalize(energy, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    _, mask = cv2.threshold(energy_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = mask > 0
    mask = ndi.binary_closing(mask, structure=np.ones((3, 3)))
    mask = ndi.binary_opening(mask, structure=np.ones((3, 3)))
    mask = ndi.binary_fill_holes(mask)

    dist = ndi.distance_transform_edt(mask)
    coords = peak_local_max(dist, min_distance=MIN_DISTANCE, labels=mask)
    peak_mask = np.zeros(dist.shape, dtype=bool)
    peak_mask[tuple(coords.T)] = True
    markers, _ = ndi.label(peak_mask)
    labels = watershed(-dist, markers, mask=mask)
    return mask, labels


def touching_pairs(labels):
    """Unique pairs of instance labels whose regions share a border (8-connectivity).

    Each shift (dy, dx) with dy in {0, 1} and dx in {-1, 0, 1} covers all 8
    neighbor directions exactly once (the opposite shift just swaps a/b).
    """
    H, W = labels.shape
    pairs = set()
    shifts = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dy, dx in shifts:
        row_a = slice(0, H - dy) if dy > 0 else slice(0, H)
        row_b = slice(dy, H)
        if dx >= 0:
            col_a = slice(0, W - dx) if dx > 0 else slice(0, W)
            col_b = slice(dx, W)
        else:
            col_a = slice(-dx, W)
            col_b = slice(0, W + dx)

        a = labels[row_a, col_a]
        b = labels[row_b, col_b]
        valid = (a != 0) & (b != 0) & (a != b)
        lo = np.minimum(a[valid], b[valid])
        hi = np.maximum(a[valid], b[valid])
        keys = (lo.astype(np.int64) << 32) | hi.astype(np.int64)
        for k in np.unique(keys):
            pairs.add((int(k >> 32), int(k & 0xFFFFFFFF)))
    return pairs


def score_fov(path):
    gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    mask, labels_raw = segment(gray)
    coverage_fraction = float(mask.mean())

    raw_props = regionprops_table(labels_raw, properties=("label", "area"))
    if len(raw_props["label"]) == 0:
        return {
            "n_cells": 0, "coverage_fraction": coverage_fraction,
            "rouleaux_fraction": 0.0, "n_isolated": 0, "crenation_fraction": 0.0,
            "median_area": 0.0, "area_cv": 0.0,
        }

    # reference cell size from the upper part of the area distribution: small
    # fragments (watershed noise) are numerous but tiny, so they drag the low
    # percentiles down without representing real cells.
    reference_area = np.percentile(raw_props["area"], 75)
    fragment_floor = FRAGMENT_AREA_RATIO * reference_area
    merged_ceiling = MERGED_AREA_RATIO * reference_area

    keep_labels = raw_props["label"][raw_props["area"] >= fragment_floor]
    labels = np.where(np.isin(labels_raw, keep_labels), labels_raw, 0)

    props = regionprops_table(
        labels, properties=("label", "area", "centroid")
    )
    n_cells = len(props["label"])
    if n_cells == 0:
        return {
            "n_cells": 0, "coverage_fraction": coverage_fraction,
            "rouleaux_fraction": 0.0, "n_isolated": 0, "crenation_fraction": 0.0,
            "median_area": 0.0, "area_cv": 0.0,
        }

    label_to_idx = {lab: i for i, lab in enumerate(props["label"])}
    centroids = np.stack([props["centroid-0"], props["centroid-1"]], axis=1)
    areas = np.array(props["area"], dtype=np.float64)

    neighbors = defaultdict(list)
    for a, b in touching_pairs(labels):
        neighbors[a].append(b)
        neighbors[b].append(a)

    n_inline = 0
    degree = np.zeros(n_cells, dtype=np.int32)
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
                n_inline += 1
    rouleaux_fraction = n_inline / n_cells

    # crenation is only meaningful for cleanly isolated, single-cell-sized blobs:
    # touching cells have contours artificially cut by their neighbor, and
    # oversized blobs are likely unsplit doublets, not one crenated cell.
    single_sized = areas <= merged_ceiling
    isolated_single = (degree == 0) & single_sized
    n_isolated = int(isolated_single.sum())
    if n_isolated > 0:
        # solidity needs a convex-hull per region, which dominates runtime if computed
        # for every cell (~30s/FOV) — restrict it to just the isolated candidates (~1000).
        candidate_labels = props["label"][isolated_single]
        labels_for_solidity = np.where(np.isin(labels, candidate_labels), labels, 0)
        solidity_props = regionprops_table(labels_for_solidity, properties=("label", "solidity"))
        solidity_by_label = dict(zip(solidity_props["label"], solidity_props["solidity"]))
        solidity = np.array([solidity_by_label[lab] for lab in candidate_labels])
        crenation_fraction = float((solidity < CRENATION_SOLIDITY_THRESHOLD).mean())
    else:
        crenation_fraction = 0.0

    median_area = float(np.median(areas))
    area_cv = float(areas.std() / areas.mean()) if areas.mean() > 0 else 0.0

    return {
        "n_cells": n_cells,
        "coverage_fraction": coverage_fraction,
        "rouleaux_fraction": rouleaux_fraction,
        "n_isolated": n_isolated,
        "crenation_fraction": crenation_fraction,
        "median_area": median_area,
        "area_cv": area_cv,
    }


def _score_one(args):
    idx, path = args
    row = score_fov(path)
    row["idx"] = idx
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dpc_dir", type=Path)
    parser.add_argument("out_csv", type=Path)
    parser.add_argument("--slide-id", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    paths = sorted(args.dpc_dir.glob(f"dpc-*-{args.slide_id}.png"))
    if args.limit:
        paths = paths[: args.limit]

    def idx_of(p):
        return int(p.name.split("-")[1])

    jobs = [(idx_of(p), p) for p in paths]

    with Pool(args.workers) as pool:
        rows = pool.map(_score_one, jobs)
    rows.sort(key=lambda r: r["idx"])

    fieldnames = ["idx", "n_cells", "coverage_fraction", "rouleaux_fraction",
                  "n_isolated", "crenation_fraction", "median_area", "area_cv"]
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {args.out_csv}")


if __name__ == "__main__":
    main()
