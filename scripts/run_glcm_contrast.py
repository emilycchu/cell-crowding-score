"""Run GLCM contrast feature extraction over a raw FOV dataset and write results to CSV.

glcm_contrast() already operates on the raw image with no Otsu mask involved,
so there's nothing to decouple here -- this just produces the comparison CSV.

Usage:
    python scripts/run_glcm_contrast.py data/raw/initial-dataset-071626 data/results/initial-dataset-071626/glcm-contrast.csv
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.features.glcm_contrast import glcm_contrast
from src.pipeline import IMAGE_EXTENSIONS, load_image


def run_glcm_contrast_on_directory(directory):
    directory = Path(directory)
    paths = sorted(p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)

    rows = []
    for path in paths:
        image = load_image(path)
        contrast = glcm_contrast(image)
        rows.append({"filename": path.name, "glcm_contrast": round(contrast, 2)})
    return rows


def write_csv(rows, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "glcm_contrast"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Run GLCM contrast extraction over a directory of FOV images.")
    parser.add_argument("input_dir", help="Directory of raw FOV images.")
    parser.add_argument("output_csv", help="Path to write the GLCM contrast results CSV.")
    args = parser.parse_args()

    rows = run_glcm_contrast_on_directory(args.input_dir)
    write_csv(rows, args.output_csv)
    print(f"Wrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
