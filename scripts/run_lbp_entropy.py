"""Run LBP entropy feature extraction over a raw FOV dataset and write results to CSV.

lbp_entropy() already operates on the raw image with no Otsu mask involved,
so there's nothing to decouple here -- this just produces the comparison CSV.

Usage:
    python scripts/run_lbp_entropy.py data/raw/initial-dataset-071626 data/results/initial-dataset-071626/lbp-entropy.csv
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.features.lbp_entropy import lbp_entropy
from src.pipeline import IMAGE_EXTENSIONS, load_image


def run_lbp_entropy_on_directory(directory):
    directory = Path(directory)
    paths = sorted(p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)

    rows = []
    for path in paths:
        image = load_image(path)
        entropy = lbp_entropy(image)
        rows.append({"filename": path.name, "lbp_entropy": round(entropy, 4)})
    return rows


def write_csv(rows, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "lbp_entropy"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Run LBP entropy extraction over a directory of FOV images.")
    parser.add_argument("input_dir", help="Directory of raw FOV images.")
    parser.add_argument("output_csv", help="Path to write the LBP entropy results CSV.")
    args = parser.parse_args()

    rows = run_lbp_entropy_on_directory(args.input_dir)
    write_csv(rows, args.output_csv)
    print(f"Wrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
