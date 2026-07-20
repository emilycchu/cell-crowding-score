"""Run Otsu segmentation over a raw FOV dataset and write per-FOV coverage results to CSV.

Usage:
    python scripts/run_otsu.py data/raw/initial-dataset-071626 data/results/initial-dataset-071626/otsu.csv
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import IMAGE_EXTENSIONS, load_image
from src.segmentation import cell_coverage, otsu_segment


def run_otsu_on_directory(directory):
    directory = Path(directory)
    paths = sorted(p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)

    rows = []
    for path in paths:
        image = load_image(path)
        mask, threshold = otsu_segment(image)
        coverage = cell_coverage(mask)
        rows.append(
            {
                "filename": path.name,
                "otsu_threshold": threshold,
                "coverage": round(coverage, 4),
                "coverage_pct": round(coverage * 100, 2),
            }
        )
    return rows


def write_csv(rows, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "otsu_threshold", "coverage", "coverage_pct"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Run Otsu segmentation over a directory of FOV images.")
    parser.add_argument("input_dir", help="Directory of raw FOV images.")
    parser.add_argument("output_csv", help="Path to write the Otsu results CSV.")
    args = parser.parse_args()

    rows = run_otsu_on_directory(args.input_dir)
    write_csv(rows, args.output_csv)
    print(f"Wrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
