"""Run edge-density feature extraction over a raw FOV dataset and write results to CSV.

Computes both the Otsu-masked variant (edges within the foreground mask only)
and the unmasked variant (edges over the full raw image), so the two can be
compared directly while Otsu's segmentation accuracy is still being validated.

Usage:
    python scripts/run_edge_density.py data/raw/initial-dataset-071626 data/results/initial-dataset-071626/edge-density.csv
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.features.edge_density import edge_density
from src.pipeline import IMAGE_EXTENSIONS, load_image
from src.segmentation import otsu_segment


def run_edge_density_on_directory(directory):
    directory = Path(directory)
    paths = sorted(p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)

    rows = []
    for path in paths:
        image = load_image(path)
        mask, _ = otsu_segment(image)
        masked = edge_density(image, mask=mask)
        unmasked = edge_density(image)
        rows.append(
            {
                "filename": path.name,
                "edge_density_masked": round(masked, 4),
                "edge_density_masked_pct": round(masked * 100, 2),
                "edge_density_unmasked": round(unmasked, 4),
                "edge_density_unmasked_pct": round(unmasked * 100, 2),
            }
        )
    return rows


def write_csv(rows, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "filename",
        "edge_density_masked",
        "edge_density_masked_pct",
        "edge_density_unmasked",
        "edge_density_unmasked_pct",
    ]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Run edge-density extraction over a directory of FOV images.")
    parser.add_argument("input_dir", help="Directory of raw FOV images.")
    parser.add_argument("output_csv", help="Path to write the edge-density results CSV.")
    args = parser.parse_args()

    rows = run_edge_density_on_directory(args.input_dir)
    write_csv(rows, args.output_csv)
    print(f"Wrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
