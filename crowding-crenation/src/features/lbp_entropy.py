"""LBP entropy feature: texture complexity via local binary pattern histogram entropy."""
import cv2
import numpy as np
from skimage.feature import local_binary_pattern


def lbp_entropy(image, radius=3, n_points=None, method="uniform"):
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if n_points is None:
        n_points = 8 * radius

    lbp = local_binary_pattern(gray, n_points, radius, method=method)
    n_bins = int(lbp.max()) + 1
    hist, _ = np.histogram(lbp, bins=n_bins, range=(0, n_bins), density=True)

    probs = hist[hist > 0]
    return float(-np.sum(probs * np.log2(probs)))
