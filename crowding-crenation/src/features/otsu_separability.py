"""Otsu separability feature: how well Otsu's threshold actually separates two populations.

cv2's THRESH_OTSU returns only the chosen threshold, not the separability it achieves.
This recomputes Otsu's own between-class/total-variance criterion (eta) from the grayscale
histogram at that threshold. eta -> 1 means the histogram is cleanly bimodal (a real
foreground/background split); eta -> 0 means Otsu picked *a* number but the two sides it
split barely differ -- e.g. a FOV so densely packed with cells there's no real background
left to separate from.
"""
import cv2
import numpy as np


def otsu_separability(image, blur_ksize=5):
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if blur_ksize > 0:
        gray = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)

    threshold, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    t = int(threshold)

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    total = hist.sum()
    if total == 0:
        return 0.0
    p = hist / total
    levels = np.arange(256)

    mu_total = float(np.sum(levels * p))
    sigma2_total = float(np.sum(p * (levels - mu_total) ** 2))
    if sigma2_total < 1e-9:
        return 0.0

    omega0 = float(np.sum(p[: t + 1]))
    omega1 = 1.0 - omega0
    if omega0 < 1e-9 or omega1 < 1e-9:
        return 0.0

    mu0 = float(np.sum(levels[: t + 1] * p[: t + 1])) / omega0
    mu1 = (mu_total - omega0 * mu0) / omega1

    sigma2_between = omega0 * omega1 * (mu1 - mu0) ** 2
    return float(np.clip(sigma2_between / sigma2_total, 0.0, 1.0))
