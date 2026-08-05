"""Run all four src/features/ techniques over the Tanzania slide KTR-72502948's raw
DPC images, for comparison against the ai-first (score_new_slide.py) pipeline on the
same slide.

Unlike run_otsu.py/run_edge_density.py/etc. (one CSV per technique), this writes a
single CSV with all four features per FOV, keyed by fov idx (parsed from the
dpc-<idx>-<slide>.png filename) so it joins directly against
data/new/KTR-72502948/fov_scores.csv and the manual annotation CSV.

Usage:
    python scripts/four-step/run_four_step_tanzania.py \
        data/new/KTR-72502948/dpc data/new/KTR-72502948/four_step_scores.csv
"""
import argparse
import csv
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.features.edge_density import edge_density
from src.features.glcm_contrast import glcm_contrast
from src.features.lbp_entropy import lbp_entropy
from src.pipeline import list_image_paths, load_image
from src.segmentation import cell_coverage, otsu_segment


def score_fov(path):
    image = load_image(path)
    mask, otsu_threshold = otsu_segment(image)
    return {
        "coverage": cell_coverage(mask),
        "edge_density_masked": edge_density(image, mask=mask),
        "edge_density_unmasked": edge_density(image),
        "glcm_contrast": glcm_contrast(image),
        "lbp_entropy": lbp_entropy(image),
        "otsu_threshold": otsu_threshold,
    }


def idx_of(path):
    # filenames look like dpc-001-KTR-72502948.png
    return int(path.name.split("-")[1])


def _score_one(path):
    row = score_fov(path)
    row["idx"] = idx_of(path)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dpc_dir", type=Path)
    parser.add_argument("out_csv", type=Path)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    paths = list_image_paths(args.dpc_dir)
    if args.limit:
        paths = paths[: args.limit]

    with Pool(args.workers) as pool:
        rows = pool.map(_score_one, paths)
    rows.sort(key=lambda r: r["idx"])

    fieldnames = [
        "idx", "coverage", "edge_density_masked", "edge_density_unmasked",
        "glcm_contrast", "lbp_entropy", "otsu_threshold",
    ]
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {args.out_csv}")


if __name__ == "__main__":
    main()
