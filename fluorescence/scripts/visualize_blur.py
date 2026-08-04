"""Save the Gaussian-blurred illumination estimate (overexposure detector, step 2) for each raw
FOV, so the intermediate step can be inspected directly.

Usage:
    python scripts/visualize_blur.py data/raw --out-dir data/raw/blurred
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

from src.overexposure import compute_illumination

IMAGE_EXTENSIONS = (".png", ".bmp", ".tif", ".tiff", ".jpg", ".jpeg")


def list_images(path):
    if path.is_dir():
        return sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    return [path]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Image file or directory of raw FOVs.")
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw/blurred"), help="Where to save blurred images.")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    for path in list_images(args.input):
        image = cv2.imread(str(path))
        if image is None:
            print(f"[skip] could not read {path}", file=sys.stderr)
            continue
        illumination = compute_illumination(image)
        blurred_u8 = np.clip(illumination, 0, 255).astype(np.uint8)
        out_path = args.out_dir / f"{path.stem}__blurred.png"
        cv2.imwrite(str(out_path), blurred_u8)
        print(f"[ok] {path.name} -> {out_path}")


if __name__ == "__main__":
    main()
