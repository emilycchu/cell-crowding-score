"""Edge density feature: fraction of (masked) pixels that lie on an edge."""
import cv2
import numpy as np


def edge_density(image, mask=None, low_threshold=50, high_threshold=150):
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, low_threshold, high_threshold)

    if mask is not None:
        region = mask > 0
        region_size = np.count_nonzero(region)
        if region_size == 0:
            return 0.0
        return float(np.count_nonzero(edges[region])) / region_size

    return float(np.count_nonzero(edges)) / edges.size
