"""Validation harness for a corner-clipping-robust rescue rule on top of the anisotropy
fiber-debris filter (see the corner-clipping brainstorm this implements: `KIT-62501087` is a
real halo wrongly demoted because it's clipped into a quarter-circle by the frame corner, but
naive corner-clip detection can't fix it -- it's statistically indistinguishable from labeled
fiber/debris cases on every corner-contact metric).

Tests two candidate signals, computed on top of the existing anisotropy-triggered region:
  - radial_rho: Spearman correlation between the whole frame's illumination and negative
    distance from the candidate mask's centroid. A halo is a global radially-decaying field;
    a fiber is a local linear object -- this should be high for halos, low for fibers,
    regardless of corner-clipping (the fitted center is allowed to sit outside the frame).
  - r2_over_r1: ratio of the FFT power spectrum's second axial moment (4*theta) to its first
    (2*theta, the existing `anisotropy` field). A quarter-arc's angular energy is a broad
    ~90-degree plateau (r1 high, r2 low); a fiber's is a narrow spike (r1 approx r2). Should be
    low for corner-clipped halos, high for fibers, corner-clipped or not.
  - area_fraction: already computed in production, included here as the cheap alternative.

Corner-clip simulation is scale-corrected: crop the FULL-resolution image to a quadrant with
the candidate's centroid at the new corner, then resize the crop back up to the *original*
image's own resolution (not straight to TARGET_MAX_DIM) before re-running detection, so the
candidate's effective pixel scale matches a real full-size FOV rather than being artificially
magnified by cropping-then-downsampling with the same fixed target size.

Usage:
    python scripts/validate_corner_clip_fix.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

from src.gcs_fov_multi import load_fov_image
from src.overexposure import (
    ANISOTROPY_PAD_FRAC,
    ANISOTROPY_R_MIN,
    HIGH_PERCENTILE,
    LOW_PERCENTILE,
    MASK_FRAC,
    RATIO_THRESHOLD,
    TARGET_MAX_DIM,
    _largest_component,
    _small_and_illumination,
)

# (sample_id, fov_id, country, label) -- label is "must_demote", "rescue_target", or "must_not_touch"
MUST_DEMOTE = [
    ("LB-D3-2025-10-22-131729-250917745-D-thin-2-3", 32, "Liberia", "fiber"),
    ("LB-D3-2025-10-22-131729-250917745-D-thin-2-3", 34, "Liberia", "fiber"),
    ("LB-D3-2025-10-22-131729-250917745-D-thin-2-3", 35, "Liberia", "fiber"),
    ("LB-D3-2025-10-27-145205-250917002-D-thin-3-3", 310, "Liberia", "artifact"),
    ("LB-D3-2025-10-03-124025-2404175445D-thin-2-3", 126, "Liberia", "artifact"),
    ("LB-D3-2025-10-27-144635-250918691-D-thin-2-2", 57, "Liberia", "artifact"),
]
RESCUE_TARGET = [("KIT-62501087", 271, "Tanzania", "real_halo")]
MUST_NOT_TOUCH = [
    ("LB-D10-2025-12-30-083614-0250901VFPCHC-2-1", 210, "Liberia", "real_halo"),
    ("LB-D3-2025-10-03-104211-250917371-D-thin-2-3", 4, "Liberia", "real_halo"),
    ("LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4", 153, "Liberia", "real_halo"),
    ("LB-D3-2025-10-22-131729-250917745-D-thin-2-3", 70, "Liberia", "real_halo"),
    ("LB-D3-2025-10-03-124025-2404175445D-thin-2-3", 114, "Liberia", "real_halo"),
    ("LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4", 154, "Liberia", "real_halo"),
    ("LB-D10-2025-12-30-084453-0250071VFPCHC-2-2", 200, "Liberia", "real_halo"),
    ("KIT-62500763", 200, "Tanzania", "real_halo"),
    ("PAT-070-3", 34, "Uganda", "real_halo"),
    ("PBC-608-KH-1", 171, "Uganda", "real_halo"),
]
ALL_ROWS = [(*r, "must_demote") for r in MUST_DEMOTE] + \
           [(*r, "rescue_target") for r in RESCUE_TARGET] + \
           [(*r, "must_not_touch") for r in MUST_NOT_TOUCH]

CORNERS = ["TL", "TR", "BL", "BR"]
MIN_CROP_FRAC = 0.25  # skip a corner crop if it would keep less than this fraction of either dimension


def spearman_rho(x, y):
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    if np.std(rx) == 0 or np.std(ry) == 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def _fft_r1_r2(patch):
    h, w = patch.shape
    if h < 8 or w < 8:
        return 0.0, 0.0
    patch = patch.astype(np.float32)
    patch = patch - patch.mean()
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
        return 0.0, 0.0

    angle = np.arctan2(yy, xx)
    power_ring = power[ring]
    angle_ring = angle[ring]
    total = np.sum(power_ring)
    r1 = float(np.abs(np.sum(power_ring * np.exp(2j * angle_ring))) / total)
    r2 = float(np.abs(np.sum(power_ring * np.exp(4j * angle_ring))) / total)
    return r1, r2


def _radial_rho(illumination, contour):
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return 0.0
    cx, cy = moments["m10"] / moments["m00"], moments["m01"] / moments["m00"]
    h, w = illumination.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    return spearman_rho(illumination.ravel(), -dist.ravel())


def analyze(image_bgr):
    """Run the ratio-gate + candidate-region extraction, then compute r1/r2/radial_rho/
    area_fraction on the candidate. Returns None if there's no candidate region at all.
    """
    small, illumination = _small_and_illumination(image_bgr)
    baseline = float(np.percentile(illumination, LOW_PERCENTILE))
    peak = float(np.percentile(illumination, HIGH_PERCENTILE))
    contrast_ratio = peak / max(baseline, 1e-3)

    mask_thresh = baseline + MASK_FRAC * (peak - baseline)
    mask = (illumination > mask_thresh).astype(np.uint8)
    area_fraction = float(mask.mean())
    contour, bbox = _largest_component(mask)
    if contour is None:
        return None

    x, y, w, h = bbox
    pad_x, pad_y = int(w * ANISOTROPY_PAD_FRAC), int(h * ANISOTROPY_PAD_FRAC)
    y0, y1 = max(y - pad_y, 0), min(y + h + pad_y, small.shape[0])
    x0, x1 = max(x - pad_x, 0), min(x + w + pad_x, small.shape[1])
    patch = small[y0:y1, x0:x1]

    r1, r2 = _fft_r1_r2(patch)
    rho = _radial_rho(illumination, contour)
    return {
        "contrast_ratio": round(contrast_ratio, 4),
        "area_fraction": round(area_fraction, 4),
        "r1": round(r1, 4),
        "r2": round(r2, 4),
        "r2_over_r1": round(r2 / r1, 4) if r1 > 1e-6 else 0.0,
        "radial_rho": round(rho, 4),
    }


def corner_crop(image_bgr, corner):
    """Crop image_bgr to the quadrant that puts `corner` at the frame's own frame-clipping
    corner, based on the candidate's centroid in full-resolution coordinates, then resize back
    up to the original resolution (scale-corrected, per the brainstorm's own caveat).
    """
    small, illumination = _small_and_illumination(image_bgr)
    baseline = float(np.percentile(illumination, LOW_PERCENTILE))
    peak = float(np.percentile(illumination, HIGH_PERCENTILE))
    mask_thresh = baseline + MASK_FRAC * (peak - baseline)
    mask = (illumination > mask_thresh).astype(np.uint8)
    contour, _ = _largest_component(mask)
    if contour is None:
        return None
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return None

    h_full, w_full = image_bgr.shape[:2]
    scale = TARGET_MAX_DIM / max(h_full, w_full)
    cx_small = moments["m10"] / moments["m00"]
    cy_small = moments["m01"] / moments["m00"]
    cx_full = int(cx_small / scale)
    cy_full = int(cy_small / scale)

    if corner == "TL":
        crop = image_bgr[cy_full:, cx_full:]
    elif corner == "TR":
        crop = image_bgr[cy_full:, :cx_full]
    elif corner == "BL":
        crop = image_bgr[:cy_full, cx_full:]
    elif corner == "BR":
        crop = image_bgr[:cy_full, :cx_full]
    else:
        raise ValueError(corner)

    if crop.shape[0] < h_full * MIN_CROP_FRAC or crop.shape[1] < w_full * MIN_CROP_FRAC:
        return None
    return cv2.resize(crop, (w_full, h_full), interpolation=cv2.INTER_LINEAR)


def main():
    rows = []
    for sample_id, fov_id, country, kind, group in ALL_ROWS:
        print(f"[{group}/{kind}] {sample_id} fov={fov_id} ({country})", flush=True)
        image, _ = load_fov_image(sample_id, fov_id, country)

        full = analyze(image)
        if full is not None:
            rows.append({"sample_id": sample_id, "fov_id": fov_id, "country": country,
                         "kind": kind, "group": group, "variant": "full", **full})

        for corner in CORNERS:
            cropped = corner_crop(image, corner)
            if cropped is None:
                continue
            result = analyze(cropped)
            if result is not None and result["contrast_ratio"] >= RATIO_THRESHOLD:
                rows.append({"sample_id": sample_id, "fov_id": fov_id, "country": country,
                             "kind": kind, "group": group, "variant": corner, **result})

    print(f"\n{'group':13} {'variant':6} {'sample_id':50} {'fov':5} {'ratio':7} "
          f"{'area_frac':9} {'r1':6} {'r2/r1':6} {'radial_rho':10}")
    for r in rows:
        print(f"{r['group']:13} {r['variant']:6} {r['sample_id']:50} {r['fov_id']:<5} "
              f"{r['contrast_ratio']:<7} {r['area_fraction']:<9} {r['r1']:<6} "
              f"{r['r2_over_r1']:<6} {r['radial_rho']:<10}")

    print("\n--- rescue-rule check: r1 > ANISOTROPY_THRESHOLD and (radial_rho > 0.90 and r2_over_r1 < 0.44) ---")
    for r in rows:
        if r["r1"] <= 0.35:
            continue
        rescued = r["radial_rho"] > 0.90 and r["r2_over_r1"] < 0.44
        flag = "RESCUED" if rescued else "stays demoted"
        print(f"{r['group']:13} {r['variant']:6} {r['sample_id']:40} fov={r['fov_id']:<5} "
              f"r1={r['r1']:.3f} rho={r['radial_rho']:.3f} r2/r1={r['r2_over_r1']:.3f} -> {flag}")


if __name__ == "__main__":
    main()
