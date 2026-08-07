# AI-first v2 density/Rouleaux pipeline

Two independent tools live in this directory:

1. **The v2 calibrated pipeline** (`merge_labels_v2.py` -> `extract_features_v2.py` ->
   `calibrate_v2.py`/`calibrate_v2.1.py`/`calibrate_v2.2.py` -> `score_fov_v2.py`) — fits
   density and Rouleaux composite scores against a growing pool of manually-labeled FOVs,
   with fixed thresholds that generalize to new slides without recalibration. This is the
   main subject of this README.
2. **`score_new_slide.py` + `label_new_slide.py`** — an earlier, from-scratch classical-CV
   (watershed) pipeline that never touches a manual label; it derives density/crowding
   labels from *that slide's own* quintiles. Superseded by the v2 pipeline for anything
   that needs to generalize across slides, but kept because it needs no calibration set at
   all. See its own docstrings for how it works — not covered further here.

## Overview: what v2 does

Given a raw FOV image, `score_fov_v2.py`:

1. Computes a fixed vector of classical CV features from the image (`_v2_common.compute_features`).
2. Combines a per-axis subset of those features into two independent `[0, 1]` composite
   scores — one for **density**, one for **Rouleaux** (cell overlap/stacking) — via a
   fitted weighted average (`src/composite_v2.py::weighted_composite`).
3. Buckets each composite score into one of 5 ordinal labels using fixed thresholds derived
   by calibration (`src/composite_v2.py::bucket`).

The weights, per-feature normalization ranges, and bucket thresholds are not hand-tuned —
they come from `calibrate_v2*.py` regressing those same features against a pool of manually
labeled FOVs, and are saved to a `density_overlap_v2*_params.json` file that `score_fov_v2.py`
loads at inference time. This is the key difference from the classical `src/composite.py`
pipeline in the repo root README: there, weights are hand-adjusted from correlation analysis;
here, they're fit.

```bash
python scripts/ai-first/score_fov_v2.py data/raw/some-dataset --params data/results/density-rouleaux-v2/density_overlap_v2.2_params.json --out-csv out.csv
```

## Feature vector (`_v2_common.compute_features`)

Every FOV image (regardless of density or Rouleaux) is reduced to this fixed set of
candidate features — the same function is imported by both calibration
(`extract_features_v2.py`) and inference (`score_fov_v2.py`), so the two can never compute
features differently:

| Feature | What it measures |
|---|---|
| `coverage` | Fraction of Otsu-masked foreground pixels (`src/segmentation.py::cell_coverage`) |
| `otsu_separability` | How cleanly Otsu's threshold splits the grayscale histogram into two populations (`src/features/otsu_separability.py`) — recomputes Otsu's own between-class/total-variance ratio (eta); eta -> 0 means a FOV so densely packed there's no real background left to separate from |
| `saturation_score` | `coverage * (1 - otsu_separability)`, clipped to [0, 1] — high when the image is both mostly-foreground *and* has a poorly-separated histogram, i.e. plausibly saturated/overcrowded past the point Otsu can even describe it. Currently informational only (see `apply_saturation_override` below) |
| `lbp_entropy` | Shannon entropy of the local-binary-pattern histogram (`src/features/lbp_entropy.py`) |
| `glcm_contrast` | Mean GLCM contrast across 4 angles, whole image (`src/features/glcm_contrast.py`) |
| `edge_density_unmasked` | Fraction of pixels on a Canny edge, unmasked (`src/features/edge_density.py`) |
| `tile_glcm_cv` | Coefficient of variation of per-tile GLCM contrast across a 7x7 grid (`src/features/tile_heterogeneity.py`) — a single whole-image contrast scalar can't tell a uniformly dense FOV from a patchy one; tiling exposes that variation. Computed on illumination-corrected grayscale (`correct_illumination`, 301px blur) so large-scale brightness gradients don't get read as tile-to-tile "heterogeneity" |
| `tile_glcm_patchiness` | `(max - median) / median` of the same per-tile GLCM contrast array — catches a small number of outlier tiles (e.g. one localized Rouleaux cluster) that barely move the mean/CV |

`otsu_threshold` is also recorded (for diagnostics) but is not a candidate feature.

Note the density/Rouleaux axes are **not** computed from distinct pipelines — both draw
from this one shared feature vector; what differs between axes is *which* features get
weighted in, and by how much (see below).

## Calibration data

`merge_labels_v2.py` pools every available manually-labeled dataset into one CSV
(`data/results/density-rouleaux-v2/merged-labels.csv`), each row a FOV with `density_label`
and `overlap_label` (displayed to the user as "Rouleaux", but named `overlap` internally to
match the source CSV columns and repo convention) on a shared 5-level ordinal scale:

- Density: `sparser`, `monolayer`, `slightly dense`, `dense`, `very dense`
- Rouleaux: `no rouleaux`, `slight rouleaux`, `some rouleaux`, `rouleaux`, `heavy rouleaux`

Sources merged (661 FOVs total, as of v2.2):

- `initial-dataset-071626` — 13 FOVs, clean `density`/`overlap` label columns.
- `tanzania-073026` (KTR-72502948) — 324 FOVs, free-text `tags` column parsed by
  `parse_tanzania_tags`.
- `tanzania-080526` (KTR-72502946) — 324 FOVs, same free-text format, images streamed
  directly from `gs://tanzania_02032026/TZ2025-Box5/KTR-72502946/` and never downloaded
  locally (see `data/results/tanzania-080526/README.md`).

`extract_features_v2.py` then runs `compute_features()` over every row's image (parallelized
via `multiprocessing.Pool`) and joins the result onto the label columns, producing
`features.csv` (or `features-v2.2.csv` for the 661-row pool) — the input to calibration.

## Calibration approach (`calibrate_v2.py` / `.1` / `.2`)

All three scripts share the same fitting machinery in `calibrate_v2.py`; `.1` and `.2` are
successive recalibrations (see "Version history" below) that reuse it wholesale and only
change *what* feeds in.

### 1. Feature selection (marginal + partial correlation)

Density and Rouleaux severity are themselves correlated in the manual labels (denser slides
tend to show more Rouleaux) — a plain marginal correlation of a feature against, say,
density can't tell whether that feature genuinely tracks density or is just riding the
density/Rouleaux confound. `correlation_table()` computes each candidate feature's Spearman
rho against both axes, plus its **partial** correlation with each axis controlling for the
other (`tanzania_comparison.partial_spearman`). `calibrate_v2.py` (the original v2) then
assigns each feature to whichever axis has the higher partial correlation, provided it
clears `MIN_PARTIAL_RHO = 0.05`; otherwise the feature is excluded from both composites.

This axis-exclusive selection turned out to be too strict for Rouleaux (see "v2.1" below),
so `calibrate_v2.1.py`/`calibrate_v2.2.py` skip the exclusive assignment and fit each axis
against the **full 8-feature candidate pool** instead, letting the regression step's own
sign-instability dropping (next section) do the real selection.

### 2. Ridge regression weight fitting

For a given axis and its candidate feature set, `fit_weights_stable`:

1. Percentile-normalizes each feature to its 2nd-98th percentile range across the
   calibration set (`percentile_ranges` / `normalize_matrix`) — robust to outliers, unlike a
   plain min-max.
2. Fits ridge regression (`fit_ridge`, closed-form, `alpha=10.0`) of the normalized feature
   matrix against the axis's ordinal label (0-4).
3. If any fitted coefficient comes out negative — despite the feature having been
   pre-selected for *positive* partial correlation with this axis — that's treated as a
   multicollinearity artifact (e.g. `tile_glcm_cv`/`tile_glcm_patchiness` are correlated at
   rho=0.63, both derived from the same per-tile array, and can flip each other's sign at
   low regularization), not a real inverse relationship. That feature is dropped and the fit
   re-run on the remaining features, iterating until all coefficients are non-negative.
4. The surviving coefficients are normalized to sum to 1 (`|coef| / sum(|coef|)`), becoming
   the composite's weights — so `weighted_composite()` at inference time is a convex
   combination of normalized features, always in `[0, 1]`.

`RIDGE_ALPHA = 10.0` was chosen empirically against this calibration set as the smallest
value that keeps correlated feature pairs' coefficients stably non-negative, so they
contribute jointly rather than one getting dropped by the sign-instability loop above.

### 3. Cross-validation

`cross_validate()` runs 5-fold CV (`N_FOLDS = 5`), stratified by ordinal label
(`stratified_folds` — shuffles within each label level before splitting, so every fold sees
every bucket) so a bucket with few examples isn't accidentally absent from a fold. Each fold
refits weights and PAVA thresholds (below) on the training rows only, then scores the held-out
rows — producing out-of-fold predictions used for the exact-match rate, off-by-one rate, and
confusion matrix reported for each axis. The final weights/thresholds shipped in the params
JSON are refit once more on the **full** calibration set (CV is for reporting expected
generalization, not for selecting the deployed fit).

### 4. PAVA-monotonic bucket thresholds

A raw composite score is continuous; `derive_thresholds()` turns it into 5 ordinal buckets:

1. Compute the median raw score within each manually-labeled level (`medians`).
2. These medians should increase monotonically with severity level, but with limited data
   per level they sometimes don't (e.g. "Some Rouleaux" scoring higher than "Rouleaux" on a
   composite that happens to conflate two different visual patterns). **PAVA**
   (pool-adjacent-violators algorithm, `_pava_merge`) enforces monotonicity by merging any
   adjacent violating levels into one weighted-average block, repeating until the whole
   sequence is non-decreasing.
3. Any level with too few (or zero) FOVs to have a stable median inherits its nearest
   neighbor's corrected value.
4. The final per-level bucket threshold is the midpoint between each pair of adjacent
   corrected medians — these are the cut points `score_fov_v2.py`'s `bucket()` applies to a
   new image's raw score.

When PAVA has to merge levels, that's reported as a `merged_bucket_groups` finding in
`calibration-report.md` — an honest signal that those buckets aren't yet cleanly separable
by the current features/sample size, not a fitting bug.

`bootstrap_median_ci` additionally bootstraps a 90% CI on each bucket's median raw score
(1000 resamples) so the report shows how much sampling noise is in each bucket's centroid.

### 5. Axis-separation check

Since density and Rouleaux are correlated in the labels, a sanity check confirms the two
*fitted* composites aren't just measuring the same thing twice: among FOVs where manual
density-rank and Rouleaux-rank disagree by at least `min_delta` levels,
`axis_separation_check()` tests whether the out-of-fold predicted score deltas diverge in
the same direction, at a better-than-chance rate (one-sided binomial test vs. 0.5, plus
Spearman rho between predicted and manual deltas).

### Output artifacts

- `density_overlap_v2*_params.json` — the deployed params (`feature_names`, `weights`,
  per-feature normalization `min`/`max`, `bucket_thresholds`, `bucket_labels`) that
  `score_fov_v2.py` loads.
- `calibration-report.md` — correlation tables, fitted weights, CV numbers, confusion
  matrices, bucket thresholds/CIs, PAVA merge notes, axis-separation results, and known
  cross-slide/cross-stain generalization caveats. `calibrate_v2.1.py`/`calibrate_v2.2.py`
  *append* a new dated section rather than overwriting it, so the report is a running
  history of every recalibration.
- `plots/` (via `plot_results_v2.py`, `plot_bucket_comparison_v2.py`) — jittered
  density/Rouleaux scatter plots and a manual-vs-model bucket-comparison grid, generated
  directly from `features.csv` + the params JSON (same scoring functions as
  `score_fov_v2.py`, so the plots always match what the tool would actually output).

## Version history

- **v2** (`calibrate_v2.py`) — first fit, 337 FOVs (13 initial + 324 tanzania-073026),
  axis-exclusive partial-correlation feature selection. Rouleaux ended up with only 2
  features (`tile_glcm_cv`, `tile_glcm_patchiness`), which had an inverted-U relationship
  with true Rouleaux severity — a severe, confluent Rouleaux sheet reads as *more*
  homogeneous than a moderate patchy case — forcing PAVA to merge the top 3 Rouleaux
  buckets.
- **v2.1** (`calibrate_v2.1.py`) — same 337 FOVs, but fits each axis against the full
  8-feature candidate pool instead of an axis-exclusive subset, letting `glcm_contrast` and
  `edge_density_unmasked` (excluded from Rouleaux in v2 on partial-correlation grounds) back
  into the Rouleaux composite, where they're cleanly monotonic across the previously-merged
  range. Trade-off: the two composites become more correlated with each other than the true
  manual density-vs-Rouleaux label correlation, since they now share more features.
- **v2.2** (`calibrate_v2.2.py`) — same full-feature-pool fitting as v2.1, pooling in a
  second Tanzania slide (`tanzania-080526`/KTR-72502946, 324 more FOVs) to grow the
  calibration set to 661, primarily to stress-test the Sparser/Monolayer boundary (thin in
  the original single-slide set: 44 Sparser examples against 241 Monolayer). Both axes'
  cross-validated rho improved after pooling (density 0.705->0.783, Rouleaux 0.620->0.737).
  See `data/results/tanzania-080526/README.md` for the full held-out-vs-pooled comparison.

**Known limitation (all versions):** every candidate feature is a raw pixel/intensity
statistic, sensitive to staining protocol, scanner, and illumination — not just true cell
density. Calibration is validated mainly on Tanzania-stain slides (only 13/661 FOVs are
non-Tanzania); spot-check `score_fov_v2.py` output against a handful of manual labels before
trusting it on a new slide or stain, and expect to refit if there's a systematic offset.
`saturation_score` is computed but not yet wired into a hard override
(`apply_saturation_override` is a documented no-op pending a fitted cutoff) — the project
decision so far is to keep it data-driven rather than a hard rule.

## Repository layout (this directory)

```
_v2_common.py            shared constants, label parsing, IO, compute_features() (the
                          single source of truth for the feature vector)
merge_labels_v2.py        pool manual label sources -> merged-labels.csv
extract_features_v2.py    compute_features() over the merged set -> features.csv
calibrate_v2.py            v2: axis-exclusive partial-correlation selection + ridge + PAVA
calibrate_v2.1.py          v2.1: full-feature-pool refit, same 337 FOVs
calibrate_v2.2.py          v2.2: full-feature-pool refit, pooled to 661 FOVs
score_fov_v2.py            inference: score a new image/directory with a params JSON
plot_results_v2.py         density/Rouleaux/density-vs-Rouleaux scatter plots
plot_bucket_comparison_v2.py  manual-vs-model bucket-grid comparison plot
score_new_slide.py         from-scratch watershed pipeline (see "Overview" above)
label_new_slide.py         slide-relative quintile labels for score_new_slide.py's output
```
