"""Otsu-threshold based cell/foreground segmentation."""
import cv2
import numpy as np


def to_grayscale(image):
    if image.ndim == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def otsu_segment(image, blur_ksize=5):
    """Segment foreground (cells) from background using Otsu's method.

    Returns the binary mask (0/255) and the threshold value Otsu selected.
    """
    gray = to_grayscale(image)
    if blur_ksize > 0:
        gray = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    threshold, mask = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return mask, threshold


def cell_coverage(mask):
    """Fraction of pixels in the mask that belong to the foreground."""
    return float(np.count_nonzero(mask)) / mask.size
