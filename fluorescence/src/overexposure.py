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

Diffuse candidate vs. neighboring-FOV illumination trend: circularity of the sustained-footprint
region doesn't separate fov62 from the vignetted negative either (see README) -- but comparing a
candidate against its immediately-preceding FOVs (already computed for free in a pipeline that
walks a scan's FOVs in order) does. Vignetting/slide-edge effects are tied to a fixed physical
location, so they vary gradually across neighboring stage positions: on the one vignetted negative
checked, its true neighbors landed a nearly identical diffuse_radius (83, 83px vs. its own 79px) at
nearly the same centroid (within 0.03-0.06 of the frame's normalized size). fov62, by contrast, is
roughly double either true neighbor's radius (72, 97px vs. its own 151px) at a centroid 0.18-0.37
away -- a spike, not a continuation of a trend. See diffuse_candidate/matches_neighbor_trend/
diffuse_halo_flag and scripts/scan_diffuse_candidates.py. Same caveat as above: exactly one
confirmed example of each case, so this is advisory only, never gating `present`/`confidence`.

Ratio floor for diffuse candidates: labeling a broader, cross-country "diverse overexposed
FOVs" set (data/labels/overexposure-diverse-080726.csv) and simulating what present would
become if diffuse_halo_flag WERE folded into the decision surfaced two problems with
diffuse_candidate's original "not present" gate (any reason present is False, no lower ratio
bound). First: 6 labeled FOVs with no real halo (annotator-tagged "background" -- ordinary
elevated illumination from dense puncta or general staining, not a halo) cleared
DIFFUSE_ABS_DELTA and DIFFUSE_RADIUS_MIN and didn't match a neighbor's trend, so they'd become
false positives if folded in; their contrast_ratio (1.36-2.21) sits well below the 6 real
sub-ratio halos in the same labeled set (2.43-2.91) -- a much cleaner, wider gap than any
shape/texture signal tried so far (a patch-grid illumination-uniformity metric was tried and
rejected here: it correlated at Spearman rho=0.95 with contrast_ratio itself, i.e. it's a
noisier restatement of a field already computed, not a new signal). Cross-checked against the
earlier fov62 investigation: fov62 (2.4139, confirmed real) sits above the gap; two informal
negatives, fov84 (2.325) and fov9 (2.518), sit inside the new candidate band by ratio alone but
are excluded regardless since their peak-baseline gap is under DIFFUSE_ABS_DELTA (diffuse_radius
already 0 for both). DIFFUSE_RATIO_MIN=2.30 sits in the middle of the [2.25, 2.42] plateau where
any floor choice gives the same result on this data.

Second: diffuse_candidate's original gate accepted present=False for ANY reason, including the
anisotropy-based fiber/debris demotion, not just a ratio-gate miss. Two labeled rows reach
present=False that way with contrast_ratio 13-14 (far above any floor): one is a fiber/debris
artifact correctly demoted by anisotropy, which the diffuse-fov step was wrongly un-demoting
(a false positive); the other is a real halo the anisotropy filter wrongly demoted, which the
diffuse-fov step happened to rescue -- by accident, not because the diffuse-fov step actually
caught a faint halo. Requiring contrast_ratio < RATIO_THRESHOLD in diffuse_candidate excludes
both, fixing the false positive at the cost of losing that one accidental rescue -- see
data/results/overexposed-diverse-080726/README.md for the full tradeoff and the confusion
matrices before/after.

Residual risk, not eliminated by the ratio floor: one labeled background-tagged FOV with no
real halo (fov279, contrast_ratio=2.632) sits inside the new [DIFFUSE_RATIO_MIN, RATIO_THRESHOLD)
candidate band and is excluded only because matches_neighbor_trend happens to catch it. The
ratio floor narrows how often that check has to do the work; it doesn't replace it.
"""
import math
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

# See module docstring, "Diffuse candidate vs. neighboring-FOV illumination trend". Gates which
# sub-ratio diffuse_radius readings are even worth comparing to neighbors -- chosen well below
# the two confirmed examples (fov62=151px, the vignetted negative=79px) but above the small
# incidental blips seen in unrelated neighboring tiles (9-31px). Advisory only.
DIFFUSE_RADIUS_MIN = 50

# See module docstring, "Ratio floor for diffuse candidates". Lower bound on contrast_ratio for
# a sub-ratio FOV to be worth treating as a diffuse candidate at all -- calibrated against 6
# labeled no-halo "background" FOVs (ratio 1.36-2.21) vs. 6 labeled real sub-ratio halos (ratio
# 2.43-2.91), cross-checked against fov62 (2.4139, real) and two informal negatives excluded
# regardless by DIFFUSE_ABS_DELTA. Any value in [2.25, 2.42] gives the same result on this data.
DIFFUSE_RATIO_MIN = 2.30

# A candidate's own diffuse blob counts as matching a neighbor's -- i.e. part of the same
# illumination trend, not an isolated event -- if the neighbor's blob sits within this
# normalized-frame distance of the candidate's centroid and its radius is within this factor.
# Calibrated against the one worked example: the vignetted negative's true neighbors matched at
# distance 0.03-0.06 and radius ratio ~1.0; fov62's true neighbors were 0.18-0.37 away at ratio
# ~1.5-2x. Advisory only -- see module docstring.
NEIGHBOR_CENTROID_MATCH_DIST = 0.12
NEIGHBOR_RADIUS_MATCH_FACTOR = 1.3


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
    diffuse_centroid_x: float
    diffuse_centroid_y: float
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
    """Size/shape/location of the region that stays elevated by a fixed absolute amount above
    baseline, as opposed to a fraction of this frame's own peak (see module docstring, "Diffuse/dim
    halo candidates below the ratio gate"). Returns (radius, circularity, centroid_x, centroid_y),
    all 0.0 if no pixels clear the delta -- centroid is normalized to [0, 1] within the frame, for
    comparing against a neighboring FOV's own footprint (see matches_neighbor_trend). Reported
    only -- not used to change `present` or `confidence`.
    """
    mask = (illumination > baseline + DIFFUSE_ABS_DELTA).astype(np.uint8)
    contour, _ = _largest_component(mask)
    if contour is None:
        return 0.0, 0.0, 0.0, 0.0
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    radius = float(np.sqrt(area / np.pi))
    circularity = float(4 * np.pi * area / (perimeter ** 2)) if perimeter > 0 else 0.0
    moments = cv2.moments(contour)
    h, w = illumination.shape
    cx = moments["m10"] / moments["m00"] / w
    cy = moments["m01"] / moments["m00"] / h
    return radius, circularity, cx, cy


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

    diffuse_radius, diffuse_circularity, diffuse_cx, diffuse_cy = _sustained_footprint(illumination, baseline)

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
        diffuse_centroid_x=round(diffuse_cx, 4),
        diffuse_centroid_y=round(diffuse_cy, 4),
        mask=mask,
    )


def diffuse_candidate(result):
    """Whether a ratio-failing FOV's sustained footprint is even large enough to be worth
    comparing against its neighbors (see DIFFUSE_RADIUS_MIN), and above DIFFUSE_RATIO_MIN (see
    module docstring, "Ratio floor for diffuse candidates") -- excludes both labeled no-halo
    background FOVs (which sit below the ratio floor) and FOVs that reached present=False via
    the anisotropy demotion rather than a genuine ratio-gate miss (which sit above
    RATIO_THRESHOLD entirely, a different failure mode this step isn't meant to touch). Most
    sub-ratio negatives never reach here at all -- their diffuse_radius is 0. Advisory only.
    """
    return (
        DIFFUSE_RATIO_MIN <= result.contrast_ratio < RATIO_THRESHOLD
        and result.diffuse_radius >= DIFFUSE_RADIUS_MIN
    )


def matches_neighbor_trend(result, neighbor_results):
    """True if an already-processed, adjacent FOV's own diffuse footprint sits at close to the
    same location and size as this one -- i.e. this candidate looks like part of a smooth,
    spatially-continuous illumination trend (vignetting, a slide/mounting edge effect) rather
    than a one-off event. See module docstring, "Diffuse candidate vs. neighboring-FOV
    illumination trend". Advisory only -- never gates `present`/`confidence`.
    """
    for neighbor in neighbor_results:
        if neighbor.diffuse_radius <= 0:
            continue
        dist = math.hypot(
            result.diffuse_centroid_x - neighbor.diffuse_centroid_x,
            result.diffuse_centroid_y - neighbor.diffuse_centroid_y,
        )
        if dist <= NEIGHBOR_CENTROID_MATCH_DIST and result.diffuse_radius <= neighbor.diffuse_radius * NEIGHBOR_RADIUS_MATCH_FACTOR:
            return True
    return False


def diffuse_halo_flag(result, neighbor_results):
    """Advisory flag for a human reviewing borderline low-ratio FOVs: True if this FOV clears
    DIFFUSE_RADIUS_MIN and does not match a neighboring FOV's illumination trend -- i.e. looks
    like an isolated diffuse halo rather than vignetting/an edge effect. Calibrated against
    exactly one confirmed example of each case (see module docstring) -- never used to change
    `present`/`confidence`.
    """
    return diffuse_candidate(result) and not matches_neighbor_trend(result, neighbor_results)


def mask_to_full_resolution(mask, image_shape):
    """Upsample a detection mask (computed at TARGET_MAX_DIM) back to the source image size,
    for overlaying on a full-resolution preview.
    """
    h, w = image_shape[:2]
    return cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
