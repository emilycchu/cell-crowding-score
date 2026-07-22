"""Save Otsu segmentation mask images for specific FOVs.

Usage:
    python scripts/save_otsu_masks.py data/raw/initial-dataset-071626 \
        data/results/initial-dataset-071626/otsu-masks \
        dpc-035-LB-D3-2025-10-03-122127-250912792D-thin-3-4.png \
        dpc-015-LB-D3-2025-10-03-122127-250912792D-thin-3-4.png \
        dpc-134-LB-D3-2025-08-30-125645-25021889-D-thin-1.png
"""
import argparse
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.boundary import clean_mask
from src.pipeline import load_image
from src.segmentation import correct_illumination, otsu_segment, to_grayscale


def save_otsu_masks(input_dir, output_dir, filenames, clean=False):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename in filenames:
        image = load_image(input_dir / filename)
        if clean:
            flat = correct_illumination(to_grayscale(image))
            mask, _ = otsu_segment(flat)
            mask = clean_mask(mask)
        else:
            mask, _ = otsu_segment(image)
        out_path = output_dir / f"{Path(filename).stem}-otsu-mask.png"
        cv2.imwrite(str(out_path), mask)
        print(f"Wrote {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Save Otsu segmentation masks for specific FOVs.")
    parser.add_argument("input_dir", help="Directory of raw FOV images.")
    parser.add_argument("output_dir", help="Directory to write mask images to.")
    parser.add_argument("filenames", nargs="+", help="Filenames (within input_dir) to segment.")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Flatten illumination gradient and apply morphological cleanup (src.boundary.clean_mask) before saving.",
    )
    args = parser.parse_args()

    save_otsu_masks(args.input_dir, args.output_dir, args.filenames, clean=args.clean)


if __name__ == "__main__":
    main()
