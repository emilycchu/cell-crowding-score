# Fluorescence Overexposure Detector

A tool for detecting the overexposed blue-light halo artifact in raw fluorescence FOVs
(fields of view), as a preprocessing/triage step before any downstream model (e.g. spot/RBC
detection) sees the image.

## The artifact

Some fluorescence FOVs show a large, roughly circular region of stray blue light overlaid
on the monolayer -- ranging from a soft diffuse glow to a sharply saturated disc. It's often
(not always) clipped by the frame border, so only an arc of it is visible, and its brightness
varies a lot between occurrences. It is visually and physically distinct from the many small,
sharp fluorescent puncta scattered across a normal FOV (those are the actual signal of
interest -- individual stained cells/parasites -- and are tiny and numerous, not one large
coherent bright region).

## Why classical CV over a pretrained model

Only 8 labeled positive examples exist (`data/labels/fluorescent-spot-examples.csv`, rows
1-8) and no labeled negatives -- nowhere near enough to train or fine-tune a model, and a
pretrained general-purpose model has no reason to know this instrument-specific illumination
artifact. The artifact also has a simple, physically-motivated signature: it's a
large-area, low-spatial-frequency brightness anomaly, which is exactly what classical
frequency-domain filtering (a heavy Gaussian blur, i.e. a low-pass filter) isolates directly
and interpretably. This also matches how `crowding-crenation/` approaches its own FOV
filters. See "Future directions" for when a model might make sense instead.

## Method

`src/overexposure.py`:

1. Take the **blue channel** of the raw FOV. Both the artifact and the real fluorescence
   signal live almost entirely there -- in a sampled artifact region vs. a dark-background
   region on one reference image, channel means were B=59.3 vs 20.6, G=7.7 vs 5.1, R=1.9 vs
   2.7. A standard grayscale conversion would weight green (58.7%) far more than blue
   (11.4%) and throw most of the signal away, so this uses the raw blue channel instead.
2. Downsample (to a 400px long side) and heavily Gaussian-blur it (`BLUR_SIGMA_FRAC=0.06` of
   the downsampled size). This is a low-pass filter: individual puncta (a few to ~30px) get
   spread over a huge area and their peak amplitude collapses, while a halo spanning
   hundreds to thousands of pixels survives almost unchanged. What's left approximates the
   frame's large-scale illumination, with point signal filtered out.
3. Compare the bright tail of that illumination estimate (`HIGH_PERCENTILE=99.5`) to its dark
   baseline (`LOW_PERCENTILE=5`) as a **ratio**, not a difference. A plain brightness-delta
   threshold produced false positives on FOVs that were simply uniformly brighter overall
   (e.g. from many scattered puncta) without any actual halo -- see Calibration below. The
   ratio is robust to that: a uniformly brighter frame lifts baseline and peak together and
   leaves the ratio roughly unchanged, while a real halo lifts the peak much more than the
   baseline.
4. Threshold the illumination estimate (`MASK_FRAC=0.35` of the way from baseline to peak) to
   get a halo mask; report its area fraction and largest-component solidity (convexity) as
   supporting/visualization output alongside the ratio-based presence call.

`present = contrast_ratio >= RATIO_THRESHOLD (3.0)`, with a `confidence` in `[0, 1]` that
scales linearly between `CONFIDENCE_LOW=2.1` and `CONFIDENCE_HIGH=6.0`.

## Calibration

Ground truth: the 8 `LB-*` rows in `data/labels/fluorescent-spot-examples.csv` (all tagged
`Overexposed`), fetched from `gs://liberia-2025` via `sample_id`/`fov_id` (see "FOV
resolution" below). Since no negatives were labeled, 8 informal negative controls were
sampled from the same five source slides (other FOVs not in the labeled set) to check the
detector doesn't fire on ordinary frames:

| Group | contrast_ratio range |
|---|---|
| 8 labeled positives | 3.65 – 17.3 |
| 8 negative-control FOVs | 1.66 – 2.43 |

`RATIO_THRESHOLD=3.0` sits in the clean gap between these two groups, and running
`scripts/score_labels.py` against the 8 labeled rows gets 8/8 agreement with the annotator's
`Overexposed` tag (`data/results/reference-scores.csv`). Area fraction and solidity were
*not* used as hard gates: a raw brightness-elevation threshold and an area-fraction gate
were both tried first and produced a false positive on one negative-control FOV that was
simply a "busier" frame overall (many puncta, higher background) without an actual halo --
the ratio was the only feature that cleanly separated it from the true positives.

Since the negative controls are informal (not part of the labeled reference set, just a
sanity check), and 8+8 examples is still a small calibration set, treat `RATIO_THRESHOLD`
as a reasonable starting point, not a rigorously fit cutoff -- see Future directions.

## Anisotropy fiber-debris filter, and its corner-clipping rescue

A thin bright hair or fiber on the slide/optics can also survive the blur and pull
`contrast_ratio` above `RATIO_THRESHOLD`, because a line's peak falls off much more slowly
under 2D blur than a point punctum's does. `_region_anisotropy`/`_fft_anisotropy` in
`src/overexposure.py` catch this via the 2D FFT power spectrum of the candidate region: a
halo's brightness falls off isotropically (low anisotropy), while a fiber concentrates energy
along one orientation (high anisotropy) no matter how it curves. `ANISOTROPY_THRESHOLD=0.35`
demotes any ratio-gate-passing candidate whose anisotropy exceeds it, calibrated against 9 real
halos (0.072-0.315) vs. 3 hair-debris candidates (0.421-0.765) from one Liberia slide -- see
`src/overexposure.py`'s module docstring for the full writeup, including why shape metrics
(solidity, bounding-box aspect ratio) don't separate the two cases.

**Corner-clipping rescue (2026-08-07).** A halo clipped into roughly a quarter-circle by the
frame corner can score anisotropy above threshold purely from the clip geometry -- a narrower
angular range concentrates more FFT energy along the cut edges' normal axes, mimicking a
fiber's signature even though the underlying field is still isotropic. Confirmed on labeled
data (`data/results/overexposed-diverse-080726/`, `KIT-62501087`, a real halo,
`contrast_ratio=14.27`, wrongly demoted at `anisotropy=0.4602`) that detecting corner-clipping
directly can't fix this: that candidate is statistically indistinguishable from three labeled
fiber/debris cases on every corner-contact metric tried. What works instead: a rescue-only
second opinion, `_looks_like_corner_clipped_halo` in `src/overexposure.py`, checked only when
anisotropy has already triggered a demotion, requiring both `radial_rho > RADIAL_RHO_MIN`
(Spearman correlation between the frame's illumination and negative distance from the
candidate's centroid -- high for a halo's global radial field, low for a fiber's local one) and
`r2_over_r1 < R2_OVER_R1_MAX` (the FFT's second axial moment relative to the first -- low for a
clipped arc's broad angular plateau, high for a fiber's narrow spike). Measured 0 wrong rescues
across all labeled fiber/debris cases and their synthetic corner-clipped crops -- see
`src/overexposure.py`'s "Corner-clipping rescue" docstring section and
`scripts/validate_corner_clip_fix.py` for the full validation, including a known miss on a
synthetic (not real) corner-clip case. Rescue-only by construction, so it cannot introduce a
new false positive among already-passing halos; both thresholds are provisional, calibrated on
a small population (6 labeled fiber/artifact cases, 1 confirmed real corner-clipped halo).

## Diffuse-halo signal (reported only, not a decision gate)

`RATIO_THRESHOLD=3.0` misses genuinely faint/diffuse halos -- e.g. one known false negative
with `contrast_ratio=2.41`. Anisotropy, mask area fraction/solidity, interior texture
(coefficient of variation), and mask circularity were all investigated as ways to separate
these faint cases from ordinary negatives and all failed: every one overlapped between the
false negative and the informal negative controls.

One signal did show a real gap: thresholding the illumination estimate at a fixed
**absolute** brightness delta above baseline (`DIFFUSE_ABS_DELTA=40`, vs. `MASK_FRAC`'s
threshold that's relative to that frame's own peak) and measuring the surviving region's
*size* (`_sustained_footprint` in `src/overexposure.py`). Real halos kept a radius of
67-169px; most negatives had zero pixels that far above baseline at all, so there was no
region to measure. This works where the relative-mask shape metrics didn't because
`MASK_FRAC` always carves out *some* blob of comparable relative size regardless of whether
a real halo is present, so its shape reflects whatever happened to be locally bright rather
than "is this a halo"; the absolute threshold instead asks whether anything clears a fixed
physical brightness bar at all, which most negatives simply don't. `OverexposureResult`
reports both `diffuse_radius` and `diffuse_circularity` (the latter alongside, for
visualization -- not validated as a discriminator itself, since most negatives have no
contour to measure), surfaced in `detect_overexposure.py` and `score_labels.py` output --
but neither field affects `present`/`confidence`.

It's reported-only, not a gate, because it's calibrated against a single confirmed
diffuse-positive example and one near-miss negative (large-scale vignetting, not a halo,
confirmed by inspecting the raw image) that isn't confidently distinguishable from the
positive by eye either. Turning it into an auto-flip decision needs more labeled diffuse-halo
positives and negatives before a hard cutoff is worth calibrating.

### Neighbor-trend check

`diffuse_radius`/`diffuse_circularity` alone can't rule out the vignetted negative above --
its radius (79px) falls inside the real-halo range (67-169px), and its circularity is actually
*higher* than fov62's. But vignetting and slide/mounting edge effects are tied to a fixed
physical location, so they vary gradually across neighboring stage positions, while a real
halo is a one-off event specific to its own FOV. Checked against the vignetted negative's true
(fov_id-adjacent) neighbors: they land a nearly identical `diffuse_radius` (83, 83px vs. its
own 79px) at nearly the same centroid (within 0.03-0.06 of the frame's normalized size) --
part of a smooth trend, not a spike. fov62's true neighbors, by contrast, sit at roughly half
its radius (72, 97px vs. its own 151px) and 0.18-0.37 away in centroid -- a spike, not a
continuation.

`diffuse_candidate`, `matches_neighbor_trend`, and `diffuse_halo_flag` in
`src/overexposure.py` implement this, and `scripts/scan_diffuse_candidates.py` runs it as a
sequential walk over one scan's FOVs (comparing each ratio-failing candidate against the
`NEIGHBOR_WINDOW=2` FOVs immediately before it -- already computed for free in a pipeline that
processes a scan's FOVs in order). Same caveat as `diffuse_radius`: exactly one confirmed
example of each case, so `diffuse_halo_flag` is advisory only, never gating
`present`/`confidence`, until there's more labeled data to calibrate
`NEIGHBOR_CENTROID_MATCH_DIST`/`NEIGHBOR_RADIUS_MATCH_FACTOR` against.

### Ratio floor for diffuse candidates

A broader, cross-country labeled test (`data/results/overexposed-diverse-080726/`) simulated
folding `diffuse_halo_flag` into the actual decision and found `diffuse_candidate`'s original
gate (`not present`, any reason, plus `diffuse_radius >= DIFFUSE_RADIUS_MIN`) let through two
kinds of false positive: 6 ordinary elevated-background FOVs (no real halo, `contrast_ratio`
1.36-2.21) that cleared `DIFFUSE_ABS_DELTA` without matching a neighbor's trend, and 1 fiber/
debris artifact (`contrast_ratio=13.39`) that the anisotropy filter had already correctly
demoted, which the diffuse-fov step then wrongly un-demoted.

`diffuse_candidate` now additionally requires `DIFFUSE_RATIO_MIN (2.30) <= contrast_ratio <
RATIO_THRESHOLD` -- a genuine ratio-gate miss above a floor, not "present=False for any
reason." Both problems share one fix: the floor excludes the 6 fake-background rows (ratio
1.36-2.21, below 2.30) directly, using a field the pipeline already computes, and the
ratio-gate-miss requirement structurally excludes the debris artifact (and, as a side effect,
one real halo separately mis-demoted by the anisotropy filter -- `contrast_ratio=14.27` --
whose only route to being flagged was the same "any reason" gate; excluding it was an accepted
tradeoff, not a goal). Calibrated against the 12 labeled rows in that test (6 fake-background,
6 real sub-ratio halos, ratio 2.43-2.91) plus fov62 (2.4139, confirmed real) and two informal
negatives (fov84=2.325, fov9=2.518, both excluded regardless since their peak-baseline gap is
under `DIFFUSE_ABS_DELTA`) -- any floor in [2.25, 2.42] gives the same result on this data.

A patch-grid illumination-uniformity metric was tried first and rejected: tested against the
real images, it correlated with `contrast_ratio` at Spearman rho=0.95 -- a noisier restatement
of a field already computed, not a new signal (the same wall this file's anisotropy/area-
fraction/solidity/interior-texture attempts already hit for a similar faint-halo-vs-negative
problem -- see "Diffuse/dim halo candidates below the ratio gate" above).

Residual risk: `fov279` (background-tagged, no real halo, `contrast_ratio=2.632`) sits inside
the new candidate band and is excluded only because `matches_neighbor_trend` happens to catch
it. The ratio floor narrows how often that check has to do the work; it doesn't replace it.
Calibrated on a small population (12 rows, 11 of them Liberia) -- treat as directional, same
caveat as every other diffuse-fov constant.

## FOV resolution

`src/gcs_fov.py` resolves a `(sample_id, fov_id)` pair to its raw image in
`gs://liberia-2025`, using only the scanner's own `Scan.txt` metadata and raw tile images --
nothing under `detection_results/` or any other precomputed-model output in the bucket is
read, so this stays a "first thing you preprocess after imaging" step. See the module
docstring for how sample IDs map to scan folders and how `fov_id` decodes to a tile
filename (it addresses a fixed-width virtual raster with a column stride of 18, not the
slide's own saved-tile grid).

## Usage

```bash
pip install -r requirements.txt
gcloud auth application-default login   # once, for GCS access

# Fetch the 8 labeled reference FOVs from GCS (cached under data/raw/, gitignored)
python scripts/fetch_reference_images.py data/labels/fluorescent-spot-examples.csv --limit 8

# Score them against the annotator's tags + save annotated preview thumbnails
python scripts/score_labels.py data/labels/fluorescent-spot-examples.csv --limit 8 \
    data/results/reference-scores.csv --preview-dir data/results/preview

# Run the detector directly on any local image or directory of images
python scripts/detect_overexposure.py data/raw --preview-dir data/results/preview

# Walk one scan's FOVs in order, flagging diffuse-halo candidates against their neighbors'
# illumination trend (see "Neighbor-trend check" above; fetches from GCS as needed)
python scripts/scan_diffuse_candidates.py LB-D3-2025-10-22-131729-250917745-D-thin-2-3 \
    --start 55 --end 70
```

## Repository layout

```
src/
  gcs_fov.py        sample_id/fov_id -> gs://liberia-2025 raw Blue-channel image resolution
  overexposure.py   the halo detector (blue channel -> blur -> contrast-ratio threshold)
scripts/
  fetch_reference_images.py   download labeled FOVs from GCS into data/raw/ (gitignored)
  detect_overexposure.py      run the detector on a local image/directory
  score_labels.py             run the detector against a labels CSV + report agreement
  scan_diffuse_candidates.py  sequential per-scan walk, flags diffuse candidates vs. neighbors
data/
  labels/   fluorescent-spot-examples.csv (gitignored -- contains real patient sample IDs)
  raw/      downloaded raw FOV images (gitignored)
  results/  score CSVs + preview thumbnails
```

## Future directions

- **Fit `RATIO_THRESHOLD` on a larger, properly labeled negative set.** The current
  threshold is calibrated against 8 positives and 8 informal (unlabeled-as-such) negatives;
  the remaining rows in the labels CSV (non-`LB` samples) and the broader unlabeled dataset
  are the natural next validation/test set once this is run at scale.
- **A pretrained/learned model becomes worth revisiting once negatives are labeled at
  scale** -- particularly for cases the ratio heuristic can't distinguish well, like a dense
  local cluster of true-positive cells that's large enough to elevate the illumination
  estimate without being the halo artifact.
- **Handle multiple halos in one frame.** The current mask/solidity computation only looks
  at the single largest connected bright component; two smaller, separate halo fragments
  (e.g. from two overlapping stray-light sources) would each be undersized individually.
