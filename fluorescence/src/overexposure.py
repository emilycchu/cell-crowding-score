"""Detect the overexposed blue-light halo artifact in raw fluorescence FOVs.

The artifact (see README.md) is a large, smooth, low-spatial-frequency bright region --
ranging from a soft diffuse glow to a sharply saturated disc -- overlaid on the monolayer,
often (but not always) clipped by the frame border. It is not the same thing as the many
small, sharp fluorescent puncta (individual cells/parasites) that are the actual signal of
interest: those are tiny and numerous, while the artifact is one large, spatially coherent
region of elevated brightness.

Approach (classical CV, chosen over a pretrained model -- see README.md for why):
1. Take the blue channel (the artifact and the fluorescence signal both live almost
   entirely in blue -- see README.md for the channel-intensity comparison that showed this).
2. Downsample and heavily Gaussian-blur it. This is a low-pass filter: individual puncta
   (a few to ~30px) are spread over a huge area and their peak amplitude collapses, while a
   halo spanning hundreds to thousands of pixels survives almost unchanged. What's left is
   an estimate of the frame's large-scale illumination, uncontaminated by point signal.
3. Compare the bright tail of that illumination estimate to its dark baseline via a ratio
   (not a difference -- see below). A normal FOV's illumination estimate is close to flat
   (near-black background, maybe mild optical vignetting); a FOV with the halo artifact has
   a large region pulled far above that baseline.
4. Threshold the illumination estimate to get a halo mask, and report its area fraction and
   convexity/solidity as supporting evidence for visualization and QC, alongside the
   ratio-based presence call.

Why a ratio (peak / baseline) rather than a raw brightness difference: absolute background
brightness varies a lot between FOVs (dust, staining, focus), so a fixed brightness-delta
threshold produced false positives on FOVs that were simply uniformly brighter overall from
many scattered puncta, without an actual halo (see README.md's calibration section). The
ratio is far more robust to that because a uniformly-brighter frame lifts both the baseline
and the peak together, leaving the ratio roughly unchanged, whereas a real halo lifts the
peak much more than the baseline.
"""
from dataclasses import dataclass, field

import cv2
import numpy as np

TARGET_MAX_DIM = 400      # downsample size the blur/threshold operate on, for speed
BLUR_SIGMA_FRAC = 0.06    # Gaussian sigma as a fraction of the downsampled image's long side
LOW_PERCENTILE = 5        # "normal background" level of the blurred illumination estimate
HIGH_PERCENTILE = 99.5    # "brightest sustained region" level (robust to single hot pixels)
MASK_FRAC = 0.35          # halo mask threshold, as a fraction of the way from baseline to peak

# Calibrated against the 8 labeled positives in data/labels/fluorescent-spot-examples.csv
# (contrast_ratio 3.65-17.3) vs. 8 informal negative-control FOVs sampled from the same five
# slides (contrast_ratio 1.66-2.43) -- see README.md "Calibration" for the full table. The
# ratio threshold sits in the clean gap between those two groups.
RATIO_THRESHOLD = 3.0
CONFIDENCE_LOW = 2.1
CONFIDENCE_HIGH = 6.0


@dataclass
class OverexposureResult:
    present: bool
    confidence: float
    contrast_ratio: float
    baseline: float
    peak: float
    area_fraction: float
    solidity: float
    mask: np.ndarray = field(repr=False)


def _largest_component_solidity(mask):
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return 0.0
    areas = stats[1:, cv2.CC_STAT_AREA]
    idx = int(np.argmax(areas)) + 1
    comp_mask = (labels == idx).astype(np.uint8)
    contours, _ = cv2.findContours(comp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour = max(contours, key=cv2.contourArea)
    hull_area = cv2.contourArea(cv2.convexHull(contour))
    return float(cv2.contourArea(contour) / hull_area) if hull_area > 0 else 0.0


def detect_overexposure(image_bgr):
    """Detect the overexposed-halo artifact in one raw fluorescence FOV (BGR image)."""
    blue = image_bgr[:, :, 0].astype(np.float32)
    h, w = blue.shape
    scale = TARGET_MAX_DIM / max(h, w)
    small = cv2.resize(blue, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)

    sigma = BLUR_SIGMA_FRAC * max(small.shape)
    illumination = cv2.GaussianBlur(small, (0, 0), sigmaX=sigma)

    baseline = float(np.percentile(illumination, LOW_PERCENTILE))
    peak = float(np.percentile(illumination, HIGH_PERCENTILE))
    contrast_ratio = peak / max(baseline, 1e-3)

    mask_thresh = baseline + MASK_FRAC * (peak - baseline)
    mask = (illumination > mask_thresh).astype(np.uint8)
    area_fraction = float(mask.mean())
    solidity = _largest_component_solidity(mask)

    confidence = float(np.clip((contrast_ratio - CONFIDENCE_LOW) / (CONFIDENCE_HIGH - CONFIDENCE_LOW), 0.0, 1.0))
    present = contrast_ratio >= RATIO_THRESHOLD

    return OverexposureResult(
        present=present,
        confidence=round(confidence, 4),
        contrast_ratio=round(contrast_ratio, 4),
        baseline=round(baseline, 4),
        peak=round(peak, 4),
        area_fraction=round(area_fraction, 4),
        solidity=round(solidity, 4),
        mask=mask,
    )


def mask_to_full_resolution(mask, image_shape):
    """Upsample a detection mask (computed at TARGET_MAX_DIM) back to the source image size,
    for overlaying on a full-resolution preview.
    """
    h, w = image_shape[:2]
    return cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
