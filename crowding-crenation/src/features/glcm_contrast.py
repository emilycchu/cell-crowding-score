"""GLCM contrast feature: local intensity variation via gray-level co-occurrence."""
import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops


def glcm_contrast(image, distances=(1,), angles=(0, np.pi / 4, np.pi / 2, 3 * np.pi / 4), levels=256):
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    glcm = graycomatrix(
        gray,
        distances=distances,
        angles=angles,
        levels=levels,
        symmetric=True,
        normed=True,
    )
    contrast = graycoprops(glcm, "contrast")
    return float(np.mean(contrast))
