"""Download the raw fluorescence (Blue-channel) image for each labeled FOV in a
data/labels/*.csv file, caching them locally so downstream scripts don't re-hit GCS.

Usage:
    python scripts/fetch_reference_images.py data/labels/fluorescent-spot-examples.csv --limit 8
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2

from src.gcs_fov import load_fov_image, local_cache_name

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


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
        sample_id, fov_id = row["sample_id"], int(row["fov_id"])
        out_path = args.out_dir / local_cache_name(sample_id, fov_id)
        if out_path.exists():
            print(f"[skip] {out_path.name} already cached")
            continue
        image, blob_name = load_fov_image(sample_id, fov_id)
        cv2.imwrite(str(out_path), image)
        print(f"[ok] {sample_id} fov={fov_id} -> gs://liberia-2025/{blob_name} -> {out_path.name}")


if __name__ == "__main__":
    main()
