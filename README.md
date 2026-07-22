# Cell Crowding Score

**Version 1.0**

A tool for scoring cell crowding/density severity in thin-film blood smear microscopy images (FOVs), as a step toward automated slide quality control.

## Overview

Given a raw FOV image, the pipeline:

1. Segments foreground (cells) from background with Otsu thresholding (`src/segmentation.py`).
2. Extracts four crowding-related features from the image and mask (`src/features/`).
3. Combines those four features into a single **composite severity score** via a weighted average (`src/composite.py`).

Separately, an exploratory **crenation filter** looks for scalloped/crenated cell-membrane boundaries. It is *not* part of the composite score — it runs as a second, independent pass over the same Otsu mask, applied only after the mask has already passed the first-pass quality/segmentation step.

## Composite score (4-part)

`src/composite.py` combines four features into one `[0, 1]` severity score, each feature min-max normalized to a fixed range and then weighted:

| Feature | Source | Default weight | Normalization range |
|---|---|---|---|
| `coverage` | `src/segmentation.py::cell_coverage` — fraction of Otsu-masked foreground pixels | 0.4 | 0.0 – 1.0 |
| `edge_density` | `src/features/edge_density.py` — fraction of pixels on a Canny edge | 0.2 | 0.0 – 1.0 |
| `glcm_contrast` | `src/features/glcm_contrast.py` — mean GLCM contrast across 4 angles | 0.2 | 0.0 – 200.0 |
| `lbp_entropy` | `src/features/lbp_entropy.py` — Shannon entropy of the LBP histogram | 0.2 | 0.0 – 6.0 |

Weights and ranges are overridable via `FeatureWeights` and a ranges dict passed to `composite_score()`; they are not yet tuned against labeled data (see Future directions).

Run the full pipeline (segmentation + all four features + composite score) on a single image or a directory of images:

```bash
python -m src.pipeline data/raw/initial-dataset-071626
python -m src.pipeline data/raw/initial-dataset-071626/dpc-035-*.png
```

Output is JSON per image: `path`, `otsu_threshold`, `features`, `score`.

## Crenation filter (separate, post-quality-test)

`scripts/explore_crenation.py` and `src/boundary.py` implement a **diagnostic-only** crenation descriptor, run *after* the Otsu mask has been produced and cleaned — it is a second-stage filter, not one of the four composite-score inputs:

1. Flatten illumination gradient (`correct_illumination`), re-run Otsu, clean the mask (`clean_mask`: opening + connected-component area filter, no closing — closing would erase the inter-cell gaps this relies on).
2. Trace contours on surviving mask blobs *and* the background gaps enclosed within them (`find_blob_contours`). In densely packed FOVs the foreground usually merges into one blob, so the gap contours (bounded by real cell-membrane edges) carry the useful signal.
3. Resample each contour into a radial profile (distance from centroid vs. angle) and take its FFT; the fraction of power in a mid-frequency band (`CRENATION_BAND = (8, 20)` cycles/perimeter) is the crenation signal — scalloped/crenated membranes concentrate power in that band, smooth membranes don't.

This produces a per-FOV visualization and summary CSV for manual review only:

```bash
python scripts/explore_crenation.py data/raw/initial-dataset-071626 \
    data/results/initial-dataset-071626/crenation-manual
```

It is **not wired into `composite_score()` or the report** yet. Convexity-defect stats are also implemented in `src/boundary.py` (`convexity_defect_stats`) but currently disabled in the exploration script in favor of the radial-FFT approach.

## Repository layout

```
src/
  segmentation.py   Otsu segmentation, illumination correction, coverage
  boundary.py       contour/gap tracing, convexity defects, radial-FFT crenation descriptors
  features/         edge_density, glcm_contrast, lbp_entropy
  composite.py       weighted composite score
  pipeline.py        end-to-end scoring (CLI: python -m src.pipeline)
scripts/
  run_otsu.py, run_edge_density.py, run_glcm_contrast.py, run_lbp_entropy.py
                      per-technique batch runs over a raw FOV directory -> CSV
  save_otsu_masks.py  dump mask images for spot-checking
  explore_crenation.py  crenation exploration (see above)
  build_result_summary.py  render a density x overlap grid image with per-technique values dropped in
  generate_report.py  compare each technique's raw output against manually-labeled severity, flag outliers
data/
  raw/<dataset>/      source FOV images (gitignored)
  labels/<dataset>/   fovs.csv (density/overlap/crenated labels) + visual grid
  results/<dataset>/  per-technique CSVs, plots, report.md
```

## Setup

```bash
pip install -r requirements.txt
pip install Pillow   # needed by scripts/build_result_summary.py, not yet in requirements.txt
```

## Current validation status

`scripts/generate_report.py` compares each technique's raw output against a combined ordinal severity score built from manual `density` + `overlap` labels (`data/labels/initial-dataset-071626/fovs.csv`, 13 FOVs) and flags per-technique outliers by linear-fit residual. See `data/results/initial-dataset-071626/report.md`. On this initial dataset: GLCM contrast, LBP entropy, and unmasked edge density show strong correlation with labeled severity; Otsu coverage and masked edge density show only weak correlation. This has not yet been assembled into a validated composite-score correlation — the composite weights are still defaults, not fit to this data.

## Future directions / improvements

- **Tune composite score weights against labeled data.** Current weights (`FeatureWeights`) and normalization ranges (`DEFAULT_RANGES`) are hand-picked defaults, not fit to the manual density/overlap labels. Use `generate_report.py`'s per-technique correlations (and a similar analysis on the composite score itself) to set weights that actually track labeled severity.
- **Optimize the running crenation score.** The radial-FFT crenation descriptor (`explore_crenation.py`) is exploratory and manual today — it needs to be made efficient enough to run over a full dataset and wired into the pipeline/composite score as an actual filter rather than a one-off visualization step.
- **Outlier testing / handling.** Some features currently score high on severity for reasons unrelated to crowding — notably, dimpled (but otherwise monolayer) cells currently inflate severity even when the slide is not actually crowded. Need a principled way to detect and either correct for or flag these outliers rather than let them skew the composite score.
- **Run on larger datasets, ideally alongside a model.** Validate on more FOVs beyond the initial 13-image labeled set, and evaluate whether the composite score, used as an input/filter alongside a downstream model, actually improves that model's performance rather than just correlating with manual labels in isolation.
