"""Manually explore radial-FFT crenation descriptors on specific FOVs.

Exploratory/diagnostic only: flattens the illumination gradient, cleans up the Otsu mask
(light opening + area filter -- no closing, since closing would erase the inter-cell gaps
this relies on), then traces contours on the surviving blobs *and* the background gaps
enclosed within them (no per-cell separation -- see src/boundary.py:find_blob_contours).
In densely packed FOVs the foreground usually merges into one blob, so those gap contours
(each bounded by real cell-membrane edges) are typically the more useful signal. Computes
the radial-FFT descriptor per contour and saves a visualization + summary CSV per FOV for
manual review -- not wired into the composite score or report yet.

Convexity-defect stats are computed in src/boundary.py but disabled here for now (radial
FFT looked more deterministic on the first pass) -- uncomment the marked lines to bring
them back.

Usage:
    python scripts/explore_crenation.py data/raw/initial-dataset-071626 \
        data/results/initial-dataset-071626/crenation-manual

    # or restrict to specific FOVs:
    python scripts/explore_crenation.py data/raw/initial-dataset-071626 \
        data/results/initial-dataset-071626/crenation-manual \
        dpc-035-LB-D3-2025-10-03-122127-250912792D-thin-3-4.png
"""
import argparse
import csv
import sys
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.boundary import clean_mask, find_blob_contours, radial_fft_power, radial_profile

# from src.boundary import convexity_defect_stats  # disabled for now -- radial FFT looked more deterministic
from src.pipeline import IMAGE_EXTENSIONS, load_image
from src.segmentation import correct_illumination, otsu_segment, to_grayscale

CRENATION_BAND = (8, 20)  # cycles/perimeter -- see plan doc for rationale
MIN_COMPONENT_AREA = 50  # drop tiny leftover noise components after opening
MIN_HOLE_AREA = 50  # drop gap contours too small to carry a meaningful boundary signal


def analyze_fov(image_path, min_hole_area=MIN_HOLE_AREA, band=CRENATION_BAND):
    image = load_image(image_path)
    gray = to_grayscale(image)
    flat = correct_illumination(gray)
    mask, _ = otsu_segment(flat)
    cleaned = clean_mask(mask, min_area=MIN_COMPONENT_AREA)
    contours = find_blob_contours(cleaned, min_area=min_hole_area, include_holes=True)

    blobs = [
        {
            # "defect_stats": convexity_defect_stats(contour),  # disabled for now -- radial FFT looked more deterministic
            "area": cv2.contourArea(contour),
            "contour": contour,
            "radii": radial_profile(contour),
            "spectrum": None,
            "radial_band_power_frac": None,
        }
        for contour in contours
    ]

    # Batch the FFT stage across every contour with a valid profile in one call, instead of one
    # Python-level rfft per contour -- radial_profile itself stays per-contour since points are
    # unevenly spaced per contour and need individual interpolation.
    valid_indices = [i for i, blob in enumerate(blobs) if blob["radii"] is not None]
    if valid_indices:
        radii_matrix = np.stack([blobs[i]["radii"] for i in valid_indices])
        spectra, band_powers = radial_fft_power(radii_matrix, band=band)
        for row, i in enumerate(valid_indices):
            blobs[i]["spectrum"] = spectra[row]
            blobs[i]["radial_band_power_frac"] = float(band_powers[row])

    return image, mask, cleaned, blobs


def summarize(blobs):
    if not blobs:
        return {
            "n_blobs": 0,
            "largest_blob_area": None,
            "largest_blob_band_power_frac": None,
            "largest_blob_band_power_pct": None,
            # "largest_blob_defect_count": None,
            "median_band_power_frac": None,
            "median_band_power_pct": None,
            # "median_defect_count": None,
        }
    largest = max(blobs, key=lambda b: b["area"])
    band_powers = [b["radial_band_power_frac"] for b in blobs if b["radial_band_power_frac"] is not None]
    # defect_counts = [b["defect_count"] for b in blobs if b["defect_count"] is not None]
    median_band_power = float(np.median(band_powers)) if band_powers else None
    return {
        "n_blobs": len(blobs),
        "largest_blob_area": largest["area"],
        "largest_blob_band_power_frac": largest["radial_band_power_frac"],
        "largest_blob_band_power_pct": round(largest["radial_band_power_frac"] * 100, 2)
        if largest["radial_band_power_frac"] is not None
        else None,
        # "largest_blob_defect_count": largest["defect_count"],
        "median_band_power_frac": median_band_power,
        "median_band_power_pct": round(median_band_power * 100, 2) if median_band_power is not None else None,
        # "median_defect_count": float(np.median(defect_counts)) if defect_counts else None,
    }


def save_visualization(image, mask, cleaned, blobs, out_path):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    for blob in blobs:
        cv2.drawContours(overlay, [blob["contour"]], -1, (0, 0, 255), 3)
        cv2.drawContours(overlay, [cv2.convexHull(blob["contour"])], -1, (0, 255, 0), 2)

    largest = max(blobs, key=lambda b: b["area"]) if blobs else None

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes[0, 0].imshow(gray, cmap="gray")
    axes[0, 0].set_title("Raw FOV")
    axes[0, 0].axis("off")
    axes[0, 1].imshow(mask, cmap="gray")
    axes[0, 1].set_title("Raw Otsu mask")
    axes[0, 1].axis("off")
    axes[0, 2].imshow(cleaned, cmap="gray")
    axes[0, 2].set_title("Cleaned mask (open + area filter, illumination-corrected)")
    axes[0, 2].axis("off")
    axes[1, 0].imshow(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
    axes[1, 0].set_title("Gap contour (red) vs. convex hull (green)")
    axes[1, 0].axis("off")

    if largest is not None and largest["radii"] is not None:
        axes[1, 1].plot(largest["radii"])
        axes[1, 1].set_title("Largest gap: radius vs. angle bin")
        axes[1, 2].plot(largest["spectrum"][:60])
        axes[1, 2].axvspan(CRENATION_BAND[0], CRENATION_BAND[1], color="red", alpha=0.2)
        axes[1, 2].set_title("Largest gap: radial FFT power\n(crenation band shaded)")
    else:
        axes[1, 1].axis("off")
        axes[1, 2].axis("off")

    fig.tight_layout()
    fig.savefig(out_path, dpi=100)
    plt.close(fig)


def write_csv(rows, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "filename",
        "n_blobs",
        "largest_blob_area",
        "largest_blob_band_power_frac",
        "largest_blob_band_power_pct",
        # "largest_blob_defect_count",
        "median_band_power_frac",
        "median_band_power_pct",
        # "median_defect_count",
    ]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Manually explore convexity-defect and radial-FFT crenation descriptors.")
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    parser.add_argument("filenames", nargs="*", help="Specific filenames to analyze; defaults to every image in input_dir.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filenames = args.filenames or [p.name for p in sorted(input_dir.iterdir()) if p.suffix.lower() in IMAGE_EXTENSIONS]

    rows = []
    for filename in filenames:
        image, mask, cleaned, blobs = analyze_fov(input_dir / filename)
        rows.append({"filename": filename, **summarize(blobs)})

        viz_path = output_dir / f"{Path(filename).stem}-crenation-manual.png"
        save_visualization(image, mask, cleaned, blobs, viz_path)
        print(f"Wrote {viz_path} ({len(blobs)} blobs)")

    csv_path = output_dir / "crenation-manual-summary.csv"
    write_csv(rows, csv_path)
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
