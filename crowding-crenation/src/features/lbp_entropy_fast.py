"""Experimental, unvalidated downsampled variant of lbp_entropy().

Striding the image before computing LBP is ~16x faster at downsample=4, but it changes
the effective spatial texture scale, not just the runtime -- so it also changes the
numeric output. composite_score() (src/composite.py) is calibrated against
lbp_entropy()'s exact current output on the 13-FOV labeled set
(data/results/initial-dataset-071626/), so this module must NOT be imported by
src/pipeline.py, score_image(), or any calibrated batch script until that calibration
has been explicitly revalidated against the new numbers. Use
scripts/compare_lbp_entropy_fast.py to measure the drift first.

downsample=1 degenerates to the exact original lbp_entropy() (used as a correctness check).
"""
import cv2
import numpy as np
from skimage.feature import local_binary_pattern


def lbp_entropy_downsampled(image, radius=3, n_points=None, method="uniform", downsample=4):
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if n_points is None:
        n_points = 8 * radius
    gray = gray[::downsample, ::downsample]

    lbp = local_binary_pattern(gray, n_points, radius, method=method)
    n_bins = int(lbp.max()) + 1
    hist, _ = np.histogram(lbp, bins=n_bins, range=(0, n_bins), density=True)

    probs = hist[hist > 0]
    if probs.size == 0:
        return 0.0
    return float(-np.sum(probs * np.log2(probs)))
