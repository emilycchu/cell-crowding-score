"""Boundary shape descriptors computed on Otsu mask blobs (no per-cell instance segmentation).

Blobs may be single cells or clumps of touching/overlapping cells -- these descriptors
operate on whatever connected components survive mask cleanup, without ever separating
touching cells into individual instances.
"""
import cv2
import numpy as np


def clean_mask(mask, open_ksize=3, close_ksize=0, min_area=50):
    """Remove speckle (opening), drop tiny leftover components.

    `close_ksize=0` (the default) skips closing entirely: in densely packed FOVs the
    foreground already merges into one blob via touching cells, and closing would fill
    in the small background gaps between cells -- which is exactly the boundary signal
    `find_blob_contours(..., include_holes=True)` relies on. Only pass a nonzero
    `close_ksize` if you specifically want blobs bridged and don't care about those gaps.
    """
    kernel_open = np.ones((open_ksize, open_ksize), np.uint8)
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
    if close_ksize > 0:
        kernel_close = np.ones((close_ksize, close_ksize), np.uint8)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_close)

    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
    areas = stats[:, cv2.CC_STAT_AREA]
    keep_labels = np.flatnonzero(areas >= min_area)
    keep_labels = keep_labels[keep_labels != 0]  # exclude background label
    keep_lut = np.zeros(n_labels, dtype=np.uint8)
    keep_lut[keep_labels] = 255
    return keep_lut[labels]


def find_blob_contours(mask, min_area=20, max_area_frac=0.5, include_holes=True):
    """Trace contours on mask blobs -- no per-cell separation.

    In dense/packed FOVs the foreground typically merges into one giant blob whose
    outer contour just traces the image border (useless for shape analysis). When
    `include_holes` is True, this also returns the background gaps enclosed by that
    blob: each gap's boundary is made entirely of real cell-membrane edges from the
    surrounding touching cells, so it carries genuine boundary-shape signal even when
    individual cells can't be separated. Contours touching the image border (truncated)
    and anything larger than `max_area_frac` of the image (the merged blob itself) are
    dropped.
    """
    mode = cv2.RETR_CCOMP if include_holes else cv2.RETR_EXTERNAL
    contours, hierarchy = cv2.findContours(mask, mode, cv2.CHAIN_APPROX_NONE)
    h, w = mask.shape
    max_area = max_area_frac * h * w

    kept = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < min_area or area > max_area:
            continue
        if include_holes and hierarchy[0][i][3] == -1:
            continue  # outer blob contour, not a hole
        x, y, cw, ch = cv2.boundingRect(contour)
        if x <= 0 or y <= 0 or x + cw >= w - 1 or y + ch >= h - 1:
            continue  # touches border, truncated
        kept.append(contour)
    return kept


def convexity_defect_stats(contour):
    """Depth distribution (in pixels) of convexity defects. None if the contour is degenerate."""
    if len(contour) < 4:
        return None
    hull_indices = cv2.convexHull(contour, returnPoints=False)
    hull_indices = np.sort(hull_indices.flatten())
    if len(hull_indices) < 4:
        return None
    try:
        defects = cv2.convexityDefects(contour, hull_indices)
    except cv2.error:
        return None
    if defects is None:
        return {"count": 0, "depths": []}
    depths = (defects[:, 0, 3] / 256.0).tolist()
    return {"count": len(depths), "depths": depths}


def radial_profile(contour, n_bins=360):
    """Distance from centroid vs. angle, resampled onto n_bins evenly spaced angles."""
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return None
    cx = moments["m10"] / moments["m00"]
    cy = moments["m01"] / moments["m00"]

    points = contour.reshape(-1, 2).astype(np.float64)
    dx = points[:, 0] - cx
    dy = points[:, 1] - cy
    angles = np.arctan2(dy, dx)
    radii = np.hypot(dx, dy)

    order = np.argsort(angles)
    angles, radii = angles[order], radii[order]

    bin_edges = np.linspace(-np.pi, np.pi, n_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    return np.interp(bin_centers, angles, radii, period=2 * np.pi)


def radial_fft_power(radial_signal, band=(8, 20)):
    """FFT power spectrum of the radial signal, and the fraction of (non-DC) power in `band`."""
    signal = radial_signal - radial_signal.mean()
    spectrum = np.abs(np.fft.rfft(signal)) ** 2
    total_power = spectrum[1:].sum()
    if total_power == 0:
        return spectrum, 0.0
    lo, hi = band
    band_power = spectrum[lo : hi + 1].sum()
    return spectrum, float(band_power / total_power)
