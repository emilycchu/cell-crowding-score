"""Download the raw DPC image for each labeled FOV in a data/labels/*.csv file, caching them
locally so downstream scripts don't re-hit GCS.

Usage:
    python scripts/fetch_reference_images.py data/labels/focus-spot-examples-080426.csv
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2

from src.gcs_fov import load_fov_image, local_cache_name

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "focus-spot"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels_csv", type=Path)
    parser.add_argument("--limit", type=int, default=None, help="Only fetch the first N rows.")
    parser.add_argument("--out-dir", type=Path, default=RAW_DIR)
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.labels_csv)))
    if args.limit:
        rows = rows[: args.limit]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        sample_id, fov_id, country = row["sample_id"], int(row["fov_id"]), row["country"]
        out_path = args.out_dir / local_cache_name(sample_id, fov_id)
        if out_path.exists():
            print(f"[skip] {out_path.name} already cached")
            continue
        image, blob_uri = load_fov_image(sample_id, fov_id, country)
        cv2.imwrite(str(out_path), image)
        print(f"[ok] {sample_id} fov={fov_id} -> {blob_uri} -> {out_path.name}")


if __name__ == "__main__":
    main()
