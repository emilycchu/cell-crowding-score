"""Compute all candidate density/Rouleaux features for every FOV in the merged calibration
set (see merge_labels_v2.py), joined against its manual labels.

Usage:
    python scripts/ai-first/extract_features_v2.py [--labels-csv PATH] [--out PATH]
        [--workers N] [--limit N]
"""
import argparse
from multiprocessing import Pool

from _v2_common import FEATURES_CSV, MERGED_LABELS_CSV, compute_features, load_image, read_csv_dicts, write_csv_dicts

FEATURE_NAMES = [
    "coverage", "otsu_threshold", "otsu_separability", "saturation_score",
    "lbp_entropy", "glcm_contrast", "edge_density_unmasked",
    "tile_glcm_cv", "tile_glcm_patchiness",
]
LABEL_FIELDNAMES = ["fov_key", "dataset", "filename", "image_path", "density_label", "overlap_label",
                     "density_ord", "overlap_ord"]
FIELDNAMES = LABEL_FIELDNAMES + FEATURE_NAMES


def _score_one(row):
    image = load_image(row["image_path"])
    features = compute_features(image)
    return {**row, **features}


def main():
    parser = argparse.ArgumentParser(description="Extract candidate features for the merged calibration set.")
    parser.add_argument("--labels-csv", default=str(MERGED_LABELS_CSV))
    parser.add_argument("--out", default=str(FEATURES_CSV))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    rows = read_csv_dicts(args.labels_csv)
    if args.limit:
        rows = rows[: args.limit]

    with Pool(args.workers) as pool:
        results = pool.map(_score_one, rows)

    write_csv_dicts(args.out, FIELDNAMES, results)
    print(f"wrote {len(results)} rows to {args.out}")


if __name__ == "__main__":
    main()
