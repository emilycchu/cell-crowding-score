"""Render a quadrant-grid preview per FOV with each quadrant's focus metrics annotated, so
the raw scores from score_focus.py can actually be eyeballed against the image instead of
just read as numbers.

Usage:
    python scripts/visualize_focus.py data/labels/focus-spot-examples-080426.csv \\
        data/results/focus-080426/previews
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2

from src.focus_metrics import score_fov
from src.gcs_fov import local_cache_name

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "focus-spot"

LINE_COLOR = (0, 255, 255)
TEXT_COLOR = (0, 255, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX
CORNER_OFFSET = {"tl": (30, 40), "tr": (-330, 40), "bl": (30, -150), "br": (-330, -150)}


def draw_preview(image, scores, title):
    preview = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    h, w = image.shape[:2]
    hh, hw = h // 2, w // 2

    cv2.line(preview, (hw, 0), (hw, h), LINE_COLOR, 2)
    cv2.line(preview, (0, hh), (w, hh), LINE_COLOR, 2)

    for region, (dx, dy) in CORNER_OFFSET.items():
        # Anchor to the near edge (0/w, 0/h) of the quadrant's own corner, not the
        # center crosshair, so each region's text lands inside its own quadrant.
        x = dx if dx >= 0 else (w + dx)
        y = dy if dy >= 0 else (h + dy)
        lines = [
            f"lapvar={scores[f'{region}__laplacian_variance']:.0f}",
            f"tenengrad={scores[f'{region}__tenengrad']:.0f}",
            f"edge_w={scores[f'{region}__edge_width']}",
            f"cover={scores[f'{region}__coverage_fraction']:.2f}",
        ]
        for i, line in enumerate(lines):
            cv2.putText(preview, line, (x, y + i * 30), FONT, 0.8, TEXT_COLOR, 2, cv2.LINE_AA)

    cv2.putText(preview, title, (30, h - 20), FONT, 1.0, TEXT_COLOR, 2, cv2.LINE_AA)
    return preview


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels_csv", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.labels_csv)))
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for row in rows:
        sample_id, fov_id, country = row["sample_id"], int(row["fov_id"]), row["country"]
        image_path = args.raw_dir / local_cache_name(sample_id, fov_id)
        if not image_path.exists():
            print(f"[skip] {image_path.name} not found -- run fetch_reference_images.py first")
            continue

        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        scores = score_fov(image)
        title = f"{sample_id} fov{fov_id} ({country}, annotated: {row.get('focus_level', '?')})"
        preview = draw_preview(image, scores, title)

        out_path = args.out_dir / f"{image_path.stem}__quadrants.png"
        cv2.imwrite(str(out_path), preview)
        print(f"[ok] {out_path.name}")


if __name__ == "__main__":
    main()
