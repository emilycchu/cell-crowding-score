"""Run the overexposed-halo detector against labeled rows from a data/labels/*.csv file,
fetching each FOV's raw fluorescence image from GCS (cached locally under data/raw/) and
comparing the detector's call against the annotator's "Overexposed" tag.

Usage:
    python scripts/score_labels.py data/labels/fluorescent-spot-examples.csv --limit 8 \
        data/results/reference-scores.csv --preview-dir data/results/preview
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2

from scripts.detect_overexposure import save_preview
from src.gcs_fov import load_fov_image, local_cache_name
from src.overexposure import detect_overexposure

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
FIELDNAMES = [
    "sample_id", "fov_id", "tags", "labeled_overexposed", "predicted_present",
    "confidence", "contrast_ratio", "baseline", "peak", "area_fraction", "solidity",
]


def get_image(sample_id, fov_id, cache_dir):
    cache_path = cache_dir / local_cache_name(sample_id, fov_id)
    if cache_path.exists():
        return cv2.imread(str(cache_path))
    image, _ = load_fov_image(sample_id, fov_id)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(cache_path), image)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels_csv", type=Path)
    parser.add_argument("out_csv", type=Path)
    parser.add_argument("--limit", type=int, default=None, help="Only score the first N rows.")
    parser.add_argument("--cache-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--preview-dir", type=Path, default=None)
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.labels_csv)))
    if args.limit:
        rows = rows[: args.limit]

    out_rows = []
    n_correct = 0
    for row in rows:
        sample_id, fov_id = row["sample_id"], int(row["fov_id"])
        labeled_overexposed = "overexposed" in row["tags"].lower()

        image = get_image(sample_id, fov_id, args.cache_dir)
        result = detect_overexposure(image)
        n_correct += int(result.present == labeled_overexposed)

        out_rows.append({
            "sample_id": sample_id,
            "fov_id": fov_id,
            "tags": row["tags"],
            "labeled_overexposed": labeled_overexposed,
            "predicted_present": result.present,
            "confidence": result.confidence,
            "contrast_ratio": result.contrast_ratio,
            "baseline": result.baseline,
            "peak": result.peak,
            "area_fraction": result.area_fraction,
            "solidity": result.solidity,
        })
        print(f"{sample_id} fov={fov_id}: labeled={labeled_overexposed} predicted={result.present} "
              f"(ratio={result.contrast_ratio}, conf={result.confidence})")

        if args.preview_dir:
            preview_name = local_cache_name(sample_id, fov_id).rsplit(".", 1)[0]
            save_preview(Path(preview_name), image, result, args.preview_dir)

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"\n{n_correct}/{len(out_rows)} rows matched the annotator's Overexposed tag")
    print(f"wrote {len(out_rows)} rows to {args.out_csv}")


if __name__ == "__main__":
    main()
