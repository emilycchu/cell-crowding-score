"""Walk a slide's FOVs in fov_id order, flagging ratio-failing candidates whose sustained
diffuse footprint (see src/overexposure.py's DIFFUSE_ABS_DELTA) doesn't match the illumination
trend of the FOVs immediately before it -- i.e. looks like an isolated diffuse halo rather than
vignetting/an edge effect that varies smoothly across neighboring stage positions.

This only makes sense as a sequential walk over one scan's FOVs, since "neighbor" means
"adjacent fov_id, already processed" -- unlike detect_overexposure.py/score_labels.py, which
operate on arbitrary/sparse image sets. See src/overexposure.py's module docstring, "Diffuse
candidate vs. neighboring-FOV illumination trend", and README.md's "Diffuse-halo signal"
section for the worked example (fov62 vs. a vignetted negative) this is calibrated against.

Advisory only -- the flag is reported for human review, never changes `present`/`confidence`.

Usage:
    python scripts/scan_diffuse_candidates.py LB-D3-2025-10-22-131729-250917745-D-thin-2-3 \
        --start 55 --end 70
"""
import argparse
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2

from src.gcs_fov import load_fov_image, local_cache_name
from src.overexposure import detect_overexposure, diffuse_candidate, diffuse_halo_flag

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
NEIGHBOR_WINDOW = 2  # how many immediately-preceding FOVs to compare against


def get_image(sample_id, fov_id, cache_dir):
    cache_path = cache_dir / local_cache_name(sample_id, fov_id)
    if cache_path.exists():
        return cv2.imread(str(cache_path))
    image, _ = load_fov_image(sample_id, fov_id)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(cache_path), image)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample_id")
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--cache-dir", type=Path, default=RAW_DIR)
    args = parser.parse_args()

    recent = deque(maxlen=NEIGHBOR_WINDOW)
    for fov_id in range(args.start, args.end + 1):
        image = get_image(args.sample_id, fov_id, args.cache_dir)
        result = detect_overexposure(image)

        flag = None
        if diffuse_candidate(result):
            flag = diffuse_halo_flag(result, list(recent))

        print(
            f"fov={fov_id:<5} ratio={result.contrast_ratio:6.2f} present={result.present!s:5} "
            f"diffuse_radius={result.diffuse_radius:6.1f} "
            f"centroid=({result.diffuse_centroid_x:.2f},{result.diffuse_centroid_y:.2f}) "
            f"diffuse_halo_flag={flag}"
        )
        recent.append(result)


if __name__ == "__main__":
    main()
