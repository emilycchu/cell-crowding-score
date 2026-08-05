"""Candidate no-reference focus/sharpness metrics for a FOV, computed on the whole image and
on each of its four quadrants (top-left/top-right/bottom-left/bottom-right).

This is an exploratory pass -- several metrics are computed side by side rather than
committing to one, because a quick spot-check against a couple of labeled examples showed
the most common one (Laplacian variance) doesn't cleanly separate "focused" from
"unfocused": a labeled-unfocused FOV with a dense, grainy cell texture scored a *higher*
Laplacian variance than several labeled-focused FOVs with crisp, well-separated cells.
Fine-grained texture/noise generates plenty of raw high-frequency energy, which a generic
variance-of-high-pass metric can't tell apart from true edge sharpness. `edge_width` is
included specifically to probe that distinction (it measures how wide the intensity
transition is *across* detected edges, not how much high-frequency energy is present overall
-- a blurred edge spreads its brightness step over more pixels regardless of how textured the
surrounding region is), and `coverage_fraction` is reported alongside everything else so a
quadrant that's mostly empty background isn't mistaken for a blurry one.

Metrics:
  laplacian_variance   Variance of the Laplacian -- the standard no-reference blur metric.
  tenengrad            Mean squared Sobel gradient magnitude -- a second gradient-energy
                        metric, usually correlated with Laplacian variance but not
                        identical in how it reacts to noise.
  fft_high_freq_ratio   Fraction of 2D FFT power at/above FFT_CUTOFF_FRAC of Nyquist --
                        frequency-domain view of the same "how much fine detail" question.
  edge_width            Median (local contrast / gradient magnitude) across Canny edge
                        pixels, in pixels -- an estimate of how wide the intensity transition
                        is across real edges. Higher = blurrier. None if a region has too few
                        detected edges to estimate reliably.
  coverage_fraction     Fraction of pixels on the bright side of an Otsu threshold (same
                        foreground convention as crowding-crenation/src/segmentation.py,
                        validated there on the same DPC image modality) -- context, not a
                        focus measure by itself.
"""
import cv2
import numpy as np

FFT_CUTOFF_FRAC = 0.25    # fraction of Nyquist radius above which power counts as "high freq"
CANNY_LOW, CANNY_HIGH = 50, 150
EDGE_WIDTH_MIN_EDGES = 20  # below this many edge pixels, edge_width is too noisy to report
EDGE_WIDTH_KSIZE = 5       # window size for the local max-min (contrast) filter


def split_quadrants(image):
    h, w = image.shape[:2]
    hh, hw = h // 2, w // 2
    return {
        "tl": image[:hh, :hw],
        "tr": image[:hh, hw:],
        "bl": image[hh:, :hw],
        "br": image[hh:, hw:],
    }


def laplacian_variance(patch):
    return float(cv2.Laplacian(patch, cv2.CV_64F).var())


def _sobel_gradient(patch):
    patch_f = patch.astype(np.float32)
    gx = cv2.Sobel(patch_f, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(patch_f, cv2.CV_32F, 0, 1, ksize=3)
    return gx, gy


def tenengrad(patch):
    gx, gy = _sobel_gradient(patch)
    return float(np.mean(gx ** 2 + gy ** 2))


def fft_high_freq_ratio(patch, cutoff_frac=FFT_CUTOFF_FRAC):
    h, w = patch.shape
    f = patch.astype(np.float32)
    f -= f.mean()
    window = np.outer(np.hanning(h), np.hanning(w))
    spectrum = np.fft.fftshift(np.fft.fft2(f * window))
    power = np.abs(spectrum) ** 2

    cy, cx = h // 2, w // 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    radius = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    max_radius = min(cy, cx)

    total = float(power.sum())
    if total <= 0:
        return 0.0
    high_power = float(power[radius >= cutoff_frac * max_radius].sum())
    return high_power / total


def edge_width(patch):
    """Median (local contrast / gradient magnitude) across Canny edge pixels, in pixels.

    A linear intensity ramp of height `contrast` spread over `w` pixels has slope
    ~contrast/w, so w ~ contrast/slope: wider (blurrier) transitions have lower gradient
    magnitude for the same contrast step. `contrast` is approximated per-pixel via a small
    max-min (dilate/erode) filter rather than tracing perpendicular to each edge, which is
    enough for a per-region summary but not a precise per-edge measurement.
    """
    gx, gy = _sobel_gradient(patch)
    grad_mag = cv2.magnitude(gx, gy)

    edges = cv2.Canny(patch, CANNY_LOW, CANNY_HIGH)
    ys, xs = np.nonzero(edges)
    if len(ys) < EDGE_WIDTH_MIN_EDGES:
        return None

    patch_f = patch.astype(np.float32)
    kernel = np.ones((EDGE_WIDTH_KSIZE, EDGE_WIDTH_KSIZE), np.uint8)
    local_contrast = cv2.dilate(patch_f, kernel) - cv2.erode(patch_f, kernel)

    widths = local_contrast[ys, xs] / np.maximum(grad_mag[ys, xs], 1e-3)
    return float(np.median(widths))


def coverage_fraction(patch, blur_ksize=5):
    blurred = cv2.GaussianBlur(patch, (blur_ksize, blur_ksize), 0) if blur_ksize > 0 else patch
    _, mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return float(np.count_nonzero(mask)) / mask.size


METRIC_FUNCS = {
    "laplacian_variance": laplacian_variance,
    "tenengrad": tenengrad,
    "fft_high_freq_ratio": fft_high_freq_ratio,
    "edge_width": edge_width,
    "coverage_fraction": coverage_fraction,
}

REGION_NAMES = ["tl", "tr", "bl", "br"]


def score_region(patch):
    return {name: fn(patch) for name, fn in METRIC_FUNCS.items()}


def score_fov(image):
    """Score the whole image plus each quadrant on every metric in METRIC_FUNCS, and add a
    per-metric quadrant_range (max - min across the 4 quadrants) as a simple non-uniformity
    indicator -- the whole point of quadrant scoring is catching FOVs where focus varies
    across the frame, and this makes that variation a first-class number instead of something
    the user has to compute themselves from the 4 raw quadrant values.
    """
    regions = {"whole": image, **split_quadrants(image)}
    by_region = {region: score_region(patch) for region, patch in regions.items()}

    result = {}
    for region, metrics in by_region.items():
        for metric, value in metrics.items():
            result[f"{region}__{metric}"] = round(value, 4) if value is not None else None

    for metric in METRIC_FUNCS:
        values = [by_region[q][metric] for q in REGION_NAMES if by_region[q][metric] is not None]
        result[f"{metric}__quadrant_range"] = round(max(values) - min(values), 4) if values else None

    return result
