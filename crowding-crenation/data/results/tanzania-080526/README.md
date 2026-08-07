# Tanzania KTR-72502946: v2 model vs. manual annotation, with fluorescent-spot overlay

All 324 FOVs from slide `KTR-72502946` (Tanzania), streamed directly from
`gs://tanzania_02032026/TZ2025-Box5/KTR-72502946/` (dpc and fluorescent images alike --
nothing was downloaded to disk). Manual labels are
`data/labels/tanzania-080526/KTR-72502946-annotated.csv` (E. Chu; FOV 196 was originally
missing a density tag and was hand-labeled "Dense" per that call). Produced by
`scripts/tanzania_080526.py`.

Two independent tools:

- **Density/Rouleaux**: `scripts/ai-first/score_fov_v2.py`.
- **Fluorescent spot**: the `fluorescence/` project's overexposure/halo detector
  (`fluorescence/src/overexposure.py`, imported directly rather than duplicated) run on the
  fluorescent images, `present=True` marks a FOV "fluorescent-spot positive." Unaffected by
  the recalibration below (same images, same detector) -- carried over unchanged.

## Files

- `merged-results.csv` / `jitter-bucket-comparison.png` — scored against **v2.1**
  (`density_overlap_v2.1_params.json`, fit on the original 337-FOV set: 13 initial-071626 +
  324 tanzania-073026). KTR-72502946 was fully held out of that fit.
- `merged-results-calibrated.csv` / `jitter-bucket-comparison-calibrated.png` — scored
  against **v2.2** (`density_overlap_v2.2_params.json`, see "Recalibration" below).
- `jitter-bucket-comparison-combined.png` — all three groups (mine, v2.1, v2.2) on one grid,
  produced by `scripts/tanzania_080526_combined_plot.py`.
- `offby-vs-severity-v2.2.png` — Rouleaux and Density side by side, x = v2.2's measured
  continuous severity score per FOV, y = signed off-by amount (model level minus manual
  level). Produced by `scripts/tanzania_080526_offby_plot.py`.

## Result: v2.1 (held out)

n=324.

| axis | exact-match | off-by-one |
|---|---|---|
| Density | 65.7% | 99.4% |
| Rouleaux | 60.2% | 96.6% |

In the same range as v2.1's own out-of-fold cross-validation numbers on the 337-FOV
calibration set (exact-match 62.0% / 64.1%, see `calibration-report.md`), so it was
generalizing to this new slide about as well as it did on held-out folds of the slide it
was fit on.

## Recalibration: v2.2 (KTR-72502946 pooled in)

`scripts/ai-first/calibrate_v2.2.py` reruns the same full-feature-pool fitting v2.1 used
(ridge regression per axis over all 8 candidate features, PAVA-monotonic bucket
thresholds, 5-fold CV), but on a calibration set grown from 337 to **661 FOVs** by pooling
in this slide's own 324 labeled FOVs rather than holding them out. Motivation: this is a
more direct test of whether v2.1's thresholds -- fit on a single slide's label distribution
-- generalize to a second slide, particularly the Sparser bucket, which the original set
was thin on (44 examples, all from one slide, against 241 Monolayer).

**Sparser-bucket focus:** KTR-72502946 adds 6 more Sparser FOVs (44 -> 50 across the pool).
Out-of-fold, v2.2 calls Sparser correctly on 45/50 (90.0%) of manually-labeled Sparser FOVs
(5/50 mistaken for Monolayer, its only neighbor on the scale) — comparable to v2.1's 42/44
(95.5%) on its own single-slide set. The Sparser/Monolayer raw-score threshold moved only
slightly (0.281 -> 0.292) after pooling in the second slide, and density has **no PAVA
merges** at the new pool size (v2.1 already had none either) — the extra data didn't
destabilize this boundary, it just gave it a second slide's worth of support.

**Cross-validation (out-of-fold, 661-FOV pool):**

| axis | CV mean rho | exact-match | off-by-one |
|---|---|---|---|
| Density | 0.783 (was 0.705) | 69.4% (was 62.0%) | 98.0% (was 98.5%) |
| Rouleaux | 0.737 (was 0.620) | 67.6% (was 64.1%) | 93.8% (was 92.6%) |

Both axes improved on cross-validation after pooling in the second slide — Rouleaux
especially (CV rho +0.117), which was the weaker axis in v2.1. Trade-off, reported the same
way v2.1 reported it against v2: the two composites are now even more correlated with each
other (rho=0.972 vs. v2.1's 0.952) than the true manual density-vs-Rouleaux label
correlation (0.823) — more of the fitted signal is shared between axes rather than
axis-exclusive. Axis-separation (whether the two composites still diverge correctly on
FOVs where manual density and Rouleaux disagree by >=1 level) holds up: 69.7% sign-match
rate, p=9.9e-18, essentially the same as v2.1.

**Rescored KTR-72502946 with v2.2** (`merged-results-calibrated.csv`):

| axis | exact-match | off-by-one |
|---|---|---|
| Density | 79.6% | 100.0% |
| Rouleaux | 73.1% | 97.8% |

These are noticeably higher than v2.1's held-out numbers, but **not a fair apples-to-apples
generalization estimate** — KTR-72502946 is now inside the training pool, so this is closer
to in-sample performance than a held-out test. The 5-fold CV row above (69.4% / 67.6%) is
the more honest read on how v2.2 would do on a slide it hasn't seen.

## Fluorescent-spot overlay

Only 2/324 FOVs (0.6%) are fluorescent-spot positive (FOV 54, FOV 198) — both land in the
"some rouleaux" column at moderate-to-dense density on both mine and either model version,
but two points is nowhere near enough to say whether the halo artifact correlates with
crowding severity on this slide.
