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
5. Before accepting a ratio-based candidate, rule out thin linear debris (hairs/fibers on the
   slide or optics) that can also pull the contrast ratio above threshold -- see "Distinguishing
   halos from linear debris" below.

Why a ratio (peak / baseline) rather than a raw brightness difference: absolute background
brightness varies a lot between FOVs (dust, staining, focus), so a fixed brightness-delta
threshold produced false positives on FOVs that were simply uniformly brighter overall from
many scattered puncta, without an actual halo (see README.md's calibration section). The
ratio is far more robust to that because a uniformly-brighter frame lifts both the baseline
and the peak together, leaving the ratio roughly unchanged, whereas a real halo lifts the
peak much more than the baseline.

Distinguishing halos from linear debris: a thin bright hair or fiber can also survive the blur
and pull contrast_ratio above threshold, because unlike a point punctum (whose peak collapses
as ~1/sigma^2 under 2D blur, since it spreads over an area) a line only spreads in the direction
perpendicular to itself, so its peak falls off as ~1/sigma -- much closer to how a real halo
(already large relative to sigma) survives blur. Increasing the blur kernel can't separate the
two cases: both decay at comparable rates and no kernel size opens a clean gap between them
(tested empirically). Shape metrics on the halo mask's outline don't work either -- solidity
and bounding-box aspect ratio are both fooled once a hair curves through the frame, which
blob-ifies its outline about as much as a real (often corner-clipped) halo's outline.
What does separate them is the orientation of the *pixel-intensity texture* inside the
candidate region, via the 2D FFT power spectrum: a halo's brightness falls off smoothly in
every direction (isotropic spectrum), while a hair concentrates energy along one orientation
no matter how it curves (anisotropic spectrum) -- see _fft_anisotropy. Calibrated against 9
real-halo candidates (anisotropy 0.072-0.315) vs. 3 hair-debris candidates that had passed the
contrast_ratio gate (anisotropy 0.421-0.765) from slide LB-D3-2025-10-22-131729-250917745-D-thin-2-3
(fovs 32/34/35 vs. 62/70 plus the original 7 calibration positives); ANISOTROPY_THRESHOLD sits
in the gap between those groups.

Diffuse/dim halo candidates below the ratio gate: a faint halo (e.g. fov62 on the same slide as
above, contrast_ratio=2.41) can fall under RATIO_THRESHOLD entirely, and none of anisotropy,
area_fraction, solidity, or interior texture (checked directly against fov62 and the 8 informal
negative-control FOVs) separates it from an ordinary sub-threshold negative -- all four overlap.
One thing that does show a gap: thresholding the illumination estimate at a fixed *absolute*
brightness delta above baseline (DIFFUSE_ABS_DELTA), rather than a fraction of this frame's own
peak, and measuring the surviving region's size -- see _sustained_footprint. Rationale: a
physical illumination artifact has a roughly fixed absolute brightness/size footprint regardless
of how bright it happens to be, whereas ordinary background elevation (puncta clusters, mild
vignetting) doesn't sustain that far above its own baseline. At baseline+40, real halos (the 8
original calibration positives plus fov70) keep a connected region with equivalent radius
67-169px, while 8 of the 10 informal negatives have no pixels that far above baseline at all;
fov62 keeps radius 151px, inside the real-halo range. But one negative (a slide with genuine
large-scale vignetting, confirmed by inspecting the raw image) still keeps radius 79px, and
that same raw-image check couldn't visually rule out similar large-scale unevenness in fov62
either -- so this is reported as an informational field only (diffuse_radius/diffuse_circularity),
never used to change `present` or `confidence`. It's calibrated against exactly one confirmed
diffuse-positive example; treat it as something for a human to look at on borderline low-ratio
FOVs, not a decision rule, until there's real labeled data for faint halos.
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

# See module docstring, "Distinguishing halos from linear debris". Anisotropy is only checked
# for candidates that already pass RATIO_THRESHOLD, so this only needs to separate real halos
# from hair/fiber debris, not from low-signal negatives (whose mask outlines are noise, not
# real structure, and score unreliably on this metric).
ANISOTROPY_PAD_FRAC = 0.15   # padding added around the candidate region's bbox before the FFT
ANISOTROPY_R_MIN = 3         # excludes the DC/near-DC bins (bulk brightness, not orientation)
ANISOTROPY_THRESHOLD = 0.35

# See module docstring, "Diffuse/dim halo candidates below the ratio gate". Reported only --
# not used as a decision threshold, since it's calibrated against a single confirmed example.
DIFFUSE_ABS_DELTA = 40


@dataclass
class OverexposureResult:
    present: bool
    confidence: float
    contrast_ratio: float
    baseline: float
    peak: float
    area_fraction: float
    solidity: float
    anisotropy: float
    diffuse_radius: float
    diffuse_circularity: float
    mask: np.ndarray = field(repr=False)


def _downsample_blue_channel(image_bgr):
    blue = image_bgr[:, :, 0].astype(np.float32)
    h, w = blue.shape
    scale = TARGET_MAX_DIM / max(h, w)
    return cv2.resize(blue, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)


def _small_and_illumination(image_bgr):
    small = _downsample_blue_channel(image_bgr)
    sigma = BLUR_SIGMA_FRAC * max(small.shape)
    illumination = cv2.GaussianBlur(small, (0, 0), sigmaX=sigma)
    return small, illumination


def compute_illumination(image_bgr):
    """Downsample the blue channel and heavily Gaussian-blur it (see module docstring, step 2).
    Returns the float32 illumination estimate at the downsampled size.
    """
    _small, illumination = _small_and_illumination(image_bgr)
    return illumination


def _largest_component(mask):
    """Return (contour, bbox) of the largest connected component in a binary mask, or
    (None, None) if the mask is empty.
    """
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return None, None
    idx = int(np.argmax(stats[1:, cv2.CC_STAT_AREA])) + 1
    comp_mask = (labels == idx).astype(np.uint8)
    contours, _ = cv2.findContours(comp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour = max(contours, key=cv2.contourArea)
    x, y, w, h = stats[idx][:4]
    return contour, (x, y, w, h)


def _solidity(contour):
    hull_area = cv2.contourArea(cv2.convexHull(contour))
    return float(cv2.contourArea(contour) / hull_area) if hull_area > 0 else 0.0


def _fft_anisotropy(patch):
    """Orientation coherence of patch's 2D FFT power spectrum, in [0, 1]: ~0 for a halo's
    isotropic falloff, -> 1 for a thin fiber/hair whose energy concentrates along one
    orientation (see module docstring, "Distinguishing halos from linear debris").
    """
    h, w = patch.shape
    if h < 8 or w < 8:
        return 0.0

    patch = patch.astype(np.float32)
    patch -= patch.mean()
    window = np.outer(np.hanning(h), np.hanning(w))
    spectrum = np.fft.fftshift(np.fft.fft2(patch * window))
    power = np.abs(spectrum) ** 2

    cy, cx = h // 2, w // 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    yy -= cy
    xx -= cx
    radius = np.sqrt(xx ** 2 + yy ** 2)
    ring = (radius >= ANISOTROPY_R_MIN) & (radius <= max(min(cy, cx) - 2, ANISOTROPY_R_MIN + 1))
    if ring.sum() < 10:
        return 0.0

    angle = np.arctan2(yy, xx)
    power_ring = power[ring]
    # Doubled angle because orientation (a line and its 180-degree rotation) is the same
    # feature, not opposite ones -- this is the standard circular-statistics trick for
    # measuring concentration of an axial (mod pi) rather than directional (mod 2pi) quantity.
    resultant = np.sum(power_ring * np.exp(2j * angle[ring]))
    return float(np.abs(resultant) / np.sum(power_ring))


def _sustained_footprint(illumination, baseline):
    """Size/shape of the region that stays elevated by a fixed absolute amount above baseline,
    as opposed to a fraction of this frame's own peak (see module docstring, "Diffuse/dim halo
    candidates below the ratio gate"). Returns (radius, circularity), both 0.0 if no pixels
    clear the delta. Reported only -- not used to change `present` or `confidence`.
    """
    mask = (illumination > baseline + DIFFUSE_ABS_DELTA).astype(np.uint8)
    contour, _ = _largest_component(mask)
    if contour is None:
        return 0.0, 0.0
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    radius = float(np.sqrt(area / np.pi))
    circularity = float(4 * np.pi * area / (perimeter ** 2)) if perimeter > 0 else 0.0
    return radius, circularity


def _region_anisotropy(small, bbox):
    x, y, w, h = bbox
    pad_x, pad_y = int(w * ANISOTROPY_PAD_FRAC), int(h * ANISOTROPY_PAD_FRAC)
    y0, y1 = max(y - pad_y, 0), min(y + h + pad_y, small.shape[0])
    x0, x1 = max(x - pad_x, 0), min(x + w + pad_x, small.shape[1])
    return _fft_anisotropy(small[y0:y1, x0:x1])


def detect_overexposure(image_bgr):
    """Detect the overexposed-halo artifact in one raw fluorescence FOV (BGR image)."""
    small, illumination = _small_and_illumination(image_bgr)

    baseline = float(np.percentile(illumination, LOW_PERCENTILE))
    peak = float(np.percentile(illumination, HIGH_PERCENTILE))
    contrast_ratio = peak / max(baseline, 1e-3)

    mask_thresh = baseline + MASK_FRAC * (peak - baseline)
    mask = (illumination > mask_thresh).astype(np.uint8)
    area_fraction = float(mask.mean())
    contour, bbox = _largest_component(mask)
    solidity = _solidity(contour) if contour is not None else 0.0

    confidence = float(np.clip((contrast_ratio - CONFIDENCE_LOW) / (CONFIDENCE_HIGH - CONFIDENCE_LOW), 0.0, 1.0))
    present = contrast_ratio >= RATIO_THRESHOLD

    anisotropy = 0.0
    if present and contour is not None:
        anisotropy = _region_anisotropy(small, bbox)
        if anisotropy > ANISOTROPY_THRESHOLD:
            present = False
            confidence = 0.0

    diffuse_radius, diffuse_circularity = _sustained_footprint(illumination, baseline)

    return OverexposureResult(
        present=present,
        confidence=round(confidence, 4),
        contrast_ratio=round(contrast_ratio, 4),
        baseline=round(baseline, 4),
        peak=round(peak, 4),
        area_fraction=round(area_fraction, 4),
        solidity=round(solidity, 4),
        anisotropy=round(anisotropy, 4),
        diffuse_radius=round(diffuse_radius, 2),
        diffuse_circularity=round(diffuse_circularity, 4),
        mask=mask,
    )


def mask_to_full_resolution(mask, image_shape):
    """Upsample a detection mask (computed at TARGET_MAX_DIM) back to the source image size,
    for overlaying on a full-resolution preview.
    """
    h, w = image_shape[:2]
    return cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
