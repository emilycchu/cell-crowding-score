"""End-to-end cell crowding scoring pipeline: segment, extract features, score."""
import argparse
import json
from pathlib import Path

import cv2

from .composite import composite_score
from .features.edge_density import edge_density
from .features.glcm_contrast import glcm_contrast
from .features.lbp_entropy import lbp_entropy
from .segmentation import cell_coverage, otsu_segment

IMAGE_EXTENSIONS = (".png", ".tif", ".tiff", ".jpg", ".jpeg")


def load_image(path):
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return image


def score_image(path):
    image = load_image(path)
    mask, otsu_threshold = otsu_segment(image)

    features = {
        "coverage": cell_coverage(mask),
        "edge_density": edge_density(image, mask=mask),
        "glcm_contrast": glcm_contrast(image),
        "lbp_entropy": lbp_entropy(image),
    }

    return {
        "path": str(path),
        "otsu_threshold": otsu_threshold,
        "features": features,
        "score": composite_score(features),
    }


def score_directory(directory, extensions=IMAGE_EXTENSIONS):
    directory = Path(directory)
    paths = sorted(p for p in directory.iterdir() if p.suffix.lower() in extensions)
    return [score_image(p) for p in paths]


def main():
    parser = argparse.ArgumentParser(description="Score cell crowding in microscopy images.")
    parser.add_argument("input", help="Path to an image file or a directory of images.")
    args = parser.parse_args()

    input_path = Path(args.input)
    results = score_directory(input_path) if input_path.is_dir() else [score_image(input_path)]

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
