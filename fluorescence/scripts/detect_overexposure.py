"""Run the overexposed-halo detector on a single raw fluorescence image or a directory of
them, as a preprocessing/triage step before any downstream model sees the FOV.

Usage:
    python scripts/detect_overexposure.py data/raw/some_fov.png
    python scripts/detect_overexposure.py data/raw --preview-dir data/results/preview
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2

from src.overexposure import detect_overexposure, mask_to_full_resolution

IMAGE_EXTENSIONS = (".png", ".bmp", ".tif", ".tiff", ".jpg", ".jpeg")


def list_images(path):
    if path.is_dir():
        return sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)
    return [path]


def save_preview(path, image, result, preview_dir):
    preview_dir.mkdir(parents=True, exist_ok=True)
    h, w = image.shape[:2]
    scale = 700 / max(h, w)
    preview = cv2.resize(image, (int(w * scale), int(h * scale)))

    mask_full = mask_to_full_resolution(result.mask, image.shape)
    mask_preview = cv2.resize(mask_full, (preview.shape[1], preview.shape[0]), interpolation=cv2.INTER_NEAREST)
    contours, _ = cv2.findContours(mask_preview, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    color = (0, 0, 255) if result.present else (0, 255, 0)
    cv2.drawContours(preview, contours, -1, color, 2)

    label = f"present={result.present} ratio={result.contrast_ratio:.2f} conf={result.confidence:.2f}"
    cv2.putText(preview, label, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)

    out_path = preview_dir / f"{path.stem}__preview.png"
    cv2.imwrite(str(out_path), preview)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Image file or directory of images.")
    parser.add_argument("--preview-dir", type=Path, default=None, help="If set, save annotated preview thumbnails here.")
    args = parser.parse_args()

    results = []
    for path in list_images(args.input):
        image = cv2.imread(str(path))
        if image is None:
            print(f"[skip] could not read {path}", file=sys.stderr)
            continue
        result = detect_overexposure(image)
        results.append({
            "path": str(path),
            "present": result.present,
            "confidence": result.confidence,
            "contrast_ratio": result.contrast_ratio,
            "baseline": result.baseline,
            "peak": result.peak,
            "area_fraction": result.area_fraction,
            "solidity": result.solidity,
            "anisotropy": result.anisotropy,
            "diffuse_radius": result.diffuse_radius,
            "diffuse_circularity": result.diffuse_circularity,
            "diffuse_centroid_x": result.diffuse_centroid_x,
            "diffuse_centroid_y": result.diffuse_centroid_y,
        })
        if args.preview_dir:
            save_preview(path, image, result, args.preview_dir)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
