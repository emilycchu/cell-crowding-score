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

## Diffuse-halo signal (reported only, not a decision gate)

`RATIO_THRESHOLD=3.0` misses genuinely faint/diffuse halos -- e.g. one known false negative
with `contrast_ratio=2.41`. Anisotropy, mask area fraction/solidity, interior texture
(coefficient of variation), and mask circularity were all investigated as ways to separate
these faint cases from ordinary negatives and all failed: every one overlapped between the
false negative and the informal negative controls.

One signal did show a real gap: thresholding the illumination estimate at a fixed
**absolute** brightness delta above baseline (`DIFFUSE_ABS_DELTA=40`, vs. `MASK_FRAC`'s
threshold that's relative to that frame's own peak) and measuring the surviving region's
radius and circularity (`_sustained_footprint` in `src/overexposure.py`). Real halos kept a
radius of 67-169px; most negatives had zero pixels that far above baseline. `OverexposureResult`
reports this unconditionally as `diffuse_radius`/`diffuse_circularity`, surfaced in
`detect_overexposure.py` and `score_labels.py` output -- but it does **not** affect
`present`/`confidence`.

It's reported-only, not a gate, because it's calibrated against a single confirmed
diffuse-positive example and one near-miss negative (large-scale vignetting, not a halo,
confirmed by inspecting the raw image) that isn't confidently distinguishable from the
positive by eye either. Turning it into an auto-flip decision needs more labeled diffuse-halo
positives and negatives before a hard cutoff is worth calibrating.

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
