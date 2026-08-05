"""Compute quadrant-level focus metrics (src/focus_metrics.py) for every FOV in a
data/labels/*.csv file, using the locally cached images from fetch_reference_images.py.

The annotator's focus_level is carried through as a passive reference column only -- it is
not used to threshold, calibrate, or select among the metrics computed here.

Usage:
    python scripts/score_focus.py data/labels/focus-spot-examples-080426.csv \\
        data/results/focus-080426/focus-scores.csv
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2

from src.focus_metrics import score_fov
from src.gcs_fov import local_cache_name

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "focus-spot"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels_csv", type=Path)
    parser.add_argument("out_csv", type=Path)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.labels_csv)))

    out_rows = []
    metric_columns = None
    for row in rows:
        sample_id, fov_id, country = row["sample_id"], int(row["fov_id"]), row["country"]
        image_path = args.raw_dir / local_cache_name(sample_id, fov_id)
        if not image_path.exists():
            print(f"[skip] {image_path.name} not found -- run fetch_reference_images.py first")
            continue

        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        scores = score_fov(image)
        if metric_columns is None:
            metric_columns = list(scores.keys())

        out_rows.append({
            "sample_id": sample_id,
            "fov_id": fov_id,
            "country": country,
            "annotated_focus_level": row.get("focus_level", ""),
            **scores,
        })
        print(f"[ok] {sample_id} fov={fov_id}")

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["sample_id", "fov_id", "country", "annotated_focus_level"] + (metric_columns or [])
    with open(args.out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"wrote {len(out_rows)} rows to {args.out_csv}")


if __name__ == "__main__":
    main()
