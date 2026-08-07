# Diverse overexposed FOVs test (2026-08-07)

Full run of the overexposure-detection pipeline (`src/overexposure.py`) against
`data/labels/overexposure-diverse-080726.csv` -- 76 rows, hand-picked to be visually diverse
"Overexposed"-tagged FOVs spanning all three labeled countries (51 Liberia, 15 Tanzania, 10
Uganda), each additionally labeled with ground truth on whether a genuine fluorescent spot is
present (independent of the overexposure look). Every FOV was streamed directly from GCS (no
local disk cache) via a new `src/gcs_fov_multi.py` resolver that extends the existing
Liberia-only `src/gcs_fov.py` to Tanzania (`gs://tanzania_02032026`) and Uganda
(`gs://malaria-annotation-web`).

## Input labels

| sample_id | fov_id | annotator | country | tags | spot | notes |
|---|---|---|---|---|---|---|
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 153 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 154 | A. Chen | Liberia | Slightly Dense, Rouleaux, Overexposed | yes |  |
| LB-D10-2025-12-30-083614-0250901VFPCHC-2-1 | 210 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D10-2025-12-30-083614-0250901VFPCHC-2-1 | 227 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D10-2025-12-30-084453-0250071VFPCHC-2-2 | 200 | A. Chen | Liberia | Rouleaux, Overexposed | yes |  |
| LB-D11-2025-12-17-115859-0250319D-thin-4-1 | 29 | A. Chen | Liberia | Overexposed | no | background |
| LB-D11-2025-12-19-111309-0211715-VFPCHC-3-1 | 277 | A. Chen | Liberia | Overexposed | yes | background |
| LB-D11-2025-12-19-131014-0241591-VFPCHC-3-2 | 278 | A. Chen | Liberia | Overexposed | yes | background |
| LB-D11-2025-12-19-134126-025073-VFPCHC-3-1 | 1 | A. Chen | Liberia | Overexposed | no | background |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 257 | A. Chen | Liberia | Sparser, Crenated, Overexposed, Unfocused | no | background |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 269 | A. Chen | Liberia | Sparser, Overexposed, Unfocused | no | background |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 274 | A. Chen | Liberia | Sparser, Crenated, Overexposed | no | background |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 279 | A. Chen | Liberia | Sparser, Crenated, Unfocused, Overexposed | no | background |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 289 | A. Chen | Liberia | Sparser, Crenated, Overexposed, Unfocused | no | background |
| LB-D3-2025-09-02-141940-25087110-D-Only-1-2 | 42 | A. Chen | Liberia | Overexposed | yes | background |
| LB-D3-2025-09-09-093425-250917463-D-Only-1-1 | 166 | A. Chen | Liberia | Crenated, Overexposed | yes |  |
| LB-D3-2025-09-27-121918-17217958-D-thin-4-4 | 262 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D3-2025-10-03-104211-250917371-D-thin-2-3 | 4 | A. Chen | Liberia | Overexposed, Unfocused | yes |  |
| LB-D3-2025-10-03-104643-250917465-D-thin-3-4 | 185 | A. Chen | Liberia | Overexposed | yes | green |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 1 | A. Chen | Liberia | Crenated, Overexposed | no | background |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 16 | A. Chen | Liberia | Crenated, Overexposed | no | background |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 17 | A. Chen | Liberia | Crenated, Overexposed | no | background |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 18 | A. Chen | Liberia | Crenated, Overexposed | no | background |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 19 | A. Chen | Liberia | Crenated, Overexposed | no | background |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 53 | A. Chen | Liberia | Crenated, Overexposed | no | background |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 114 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 125 | A. Chen | Liberia | Crenated, Overexposed | yes |  |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 126 | A. Chen | Liberia | Overexposed, Artifact | no | artifact |
| LB-D3-2025-10-03-125352-2402169466D-thin-2-1 | 3 | A. Chen | Liberia | Overexposed | yes | diffuse |
| LB-D3-2025-10-03-130859-250916865-D-thin-1-4 | 236 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 134 | A. Chen | Liberia | Overexposed | yes | double |
| LB-D3-2025-10-22-132316-2411189646-D-thin-1-4 | 135 | A. Chen | Liberia | Overexposed | yes | diffuse |
| LB-D3-2025-10-22-140622-250917738-D-thin-1-1 | 122 | A. Chen | Liberia | Overexposed | yes | double |
| LB-D3-2025-10-22-140622-250917738-D-thin-1-1 | 238 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D3-2025-10-24-113736-250918214-D-thin-2-3 | 96 | A. Chen | Liberia | Overexposed | no* | relabeled by Emily 2026-08-07 (was yes) |
| LB-D3-2025-10-24-132012-25046898-D-thin-1-4 | 3 | A. Chen | Liberia | Overexposed | yes | diffuse |
| LB-D3-2025-10-24-132012-25046898-D-thin-1-4 | 305 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D3-2025-10-24-162727-230918080-D-thin-1-4 | 8 | A. Chen | Liberia | Overexposed | yes | diffuse |
| LB-D3-2025-10-25-105806-180951467-D-thin-1-1 | 270 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D3-2025-10-25-150947-250917467-D-thin-3-2 | 235 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D3-2025-10-27-123159-251123404-D-thin-4-1 | 48 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D3-2025-10-27-123159-251123404-D-thin-4-1 | 49 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D3-2025-10-27-124239-250916732-D-thin-1-3 | 301 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D3-2025-10-27-134711-250917368-D-thin-1-3 | 52 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D3-2025-10-27-144635-250918691-D-thin-2-2 | 57 | A. Chen | Liberia | Overexposed, Large | no | artifact |
| LB-D3-2025-10-27-144635-250918691-D-thin-2-2 | 243 | A. Chen | Liberia | Unfocused, Overexposed | no | background |
| LB-D3-2025-10-27-145205-250917002-D-thin-3-3 | 310 | A. Chen | Liberia | Overexposed, Artifact | no | artifact |
| LB-D3-2025-10-27-154305-250917412-D-thin-1-4 | 119 | A. Chen | Liberia | Overexposed | yes | diffuse |
| LB-D3-2025-10-27-155920-250713919-D-thin-3-3 | 169 | A. Chen | Liberia | Overexposed | no | background |
| LB-D3-2025-10-27-173317-250917493-D-thin-2-4 | 82 | A. Chen | Liberia | Overexposed | yes |  |
| LB-D5-2026-01-27-112616-0240052-VFPCHC-2-2 | 40 | A. Chen | Liberia | Overexposed | no | background |
| KIT-62500763 | 200 | A. Chen | Tanzania | Overexposed | yes | green |
| KIT-62501035 | 67 | A. Chen | Tanzania | Overexposed | yes |  |
| KIT-62501062 | 83 | A. Chen | Tanzania | Overexposed | no | artifact |
| KIT-62501081 | 141 | A. Chen | Tanzania | Overexposed | yes | double |
| KIT-62501087 | 271 | A. Chen | Tanzania | Overexposed | yes |  |
| KTR-72502946 | 54 | E. Chu | Tanzania | Slightly Dense, Some Rouleaux, Overexposed | yes |  |
| KTR-72502946 | 198 | E. Chu | Tanzania | Dense, Some Rouleaux, Overexposed | yes |  |
| NKR-72502319 | 119 | A. Chen | Tanzania | Overexposed | no | background |
| NKR-72502319 | 293 | A. Chen | Tanzania | Overexposed | yes |  |
| NKR-72502319 | 311 | A. Chen | Tanzania | Overexposed | yes |  |
| RUB-62501332 | 133 | A. Chen | Tanzania | Overexposed | yes |  |
| RUB-62501389 | 284 | Z. Ahamad | Tanzania | Overexposed | yes | double |
| RUB-62501518 | 315 | A. Chen | Tanzania | Overexposed | no | background |
| RUB-62501529 | 87 | A. Ma | Tanzania | Overexposed | no | background |
| RUB-72501756 | 315 | A. Chen | Tanzania | Overexposed | yes |  |
| PAT-070-3 | 34 | A. Chen | Uganda | Overexposed | yes | double |
| PAT-072-1 | 14 | A. Chen | Uganda | Overexposed, Artifact | no | artifact |
| PAT-072-1 | 94 | A. Chen | Uganda | Sparser, Some Rouleaux, Overexposed, Artifact | no | artifact |
| PAT-154-1 | 478 | A. Chen | Uganda | Overexposed | no | background |
| PBC-225_AM-1 | 30 | A. Ma | Uganda | Sparser, Overexposed | no | background |
| PBC-608-KH-1 | 171 | A. Chen | Uganda | Overexposed | yes |  |
| PBC-800-1 | 128 | A. Ma | Uganda | Sparser, Deep Dimples, Overexposed, Medium | no | background |
| PBC-800-1 | 732 | A. Ma | Uganda | Deep Dimples, Overexposed | no | background |
| PAT-103-2 | 441 | E. Chu | Uganda | Overexposed | no | background |
| PAT-112-2 | 124 | E. Chu | Uganda | Overexposed | no | background |

`notes` is only partially filled in (background/artifact/diffuse/double/green on some rows,
blank on the rest) -- per Emily, the remaining rows still need categorizing. The subset
breakdowns below use only the rows currently tagged `background`/`diffuse`/`double`, so they
under-cover each category and will change as `notes` gets filled in further.

`*` fov=96 (`LB-D3-2025-10-24-113736-250918214-D-thin-2-3`) was originally labeled
`spot=yes`; Emily flagged it as mislabeled on 2026-08-07 after reviewing its preview (see
"FN/FP examples" -- it had shown up there as a false negative missed by both variants, but
looking at the actual image the ground truth itself was wrong, not the detector). Corrected to
`spot=no` in both `data/labels/overexposure-diverse-080726.csv` and `results.csv`; all
confusion matrices, rates, and the FN/FP example set below reflect the corrected label.

## Method and what "predicted" means here

Full per-row detection was run via `scripts/run_overexposed_diverse_test.py`, which streams
each FOV from GCS and calls the same production code path as `scripts/score_labels.py`:
`detect_overexposure()` (ratio gate -> anisotropy-fft fiber-debris demotion), plus the
advisory-only diffuse-fov step (`diffuse_candidate` -> neighbor-trend check ->
`diffuse_halo_flag`, fetching the 2 preceding fov_ids for context, same as
`scripts/scan_diffuse_candidates.py`).

**Update (2026-08-07, same day): `diffuse_candidate()` was changed** after this doc's first
pass found the diffuse-fov fold-in created 7 new false positives (see "Discussion" below for
the original numbers). It now requires `DIFFUSE_RATIO_MIN <= contrast_ratio < RATIO_THRESHOLD`
(previously just `not present`, any reason) -- see `src/overexposure.py`'s module docstring,
"Ratio floor for diffuse candidates", for the calibration. All numbers in this doc reflect the
fixed version; the "Which FOVs flip" and "Discussion" sections below narrate both the original
finding and the fix.

**Important framing note (corrected 2026-08-07 -- an earlier draft of this doc had this
backwards).** In this dataset, "the fluorescent spot" and "the overexposed halo artifact" are
the same thing -- `spot` is ground truth on whether the overexposure artifact itself is
genuinely present, not a separate real-signal-vs-artifact distinction. So the predicted label
is `present` directly, with no inversion:

```
predicted_spot_present = present
```

A false negative is a real halo the ratio/anisotropy gate missed entirely (most importantly, a
faint/diffuse halo below `RATIO_THRESHOLD` -- exactly the case the diffuse-fov step was built
to catch). A false positive is an ordinary FOV -- elevated background from many puncta,
debris/hair, etc. -- that tripped the ratio gate without an actual halo present.

**"Folded in" vs. not.** `present_base` is exactly what production code returns today (diffuse
fields computed but never gating). `present_folded = present_base OR diffuse_halo_flag` --
i.e., what `present` (and therefore predicted spot) would become if the diffuse-fov step's
flag *were* wired into the decision, which it currently is not (see
`fluorescence/README.md`'s "Diffuse-halo signal" section for why).

## Per-FOV runtime

Streamed live from GCS, one FOV at a time, no disk cache. `neighbor_fetch_s` is only nonzero
for the 7 rows that pass `diffuse_candidate()` (`DIFFUSE_RATIO_MIN <= contrast_ratio <
RATIO_THRESHOLD` and `diffuse_radius >= DIFFUSE_RADIUS_MIN` -- see "Method" above); it
covers fetching + detecting on up to 2 preceding fov_ids for the neighbor-trend check alone.
This is fewer than the pre-fix run (17 rows) since the ratio floor now skips the neighbor
fetch entirely for FOVs it can already tell aren't real diffuse-halo candidates.

| sample_id | fov_id | country | gcs_fetch_s | initial_test_s | anisotropy_s | diffuse_fov_s | neighbor_fetch_s |
|---|---|---|---|---|---|---|---|
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 153 | Liberia | 17.4788 | 0.0733 | 0.0291 | 0.0028 | 0.0 |
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 154 | Liberia | 1.0663 | 0.0686 | 0.0368 | 0.0034 | 0.0 |
| LB-D10-2025-12-30-083614-0250901VFPCHC-2-1 | 210 | Liberia | 1.072 | 0.0739 | 0.0226 | 0.003 | 0.0 |
| LB-D10-2025-12-30-083614-0250901VFPCHC-2-1 | 227 | Liberia | 1.1105 | 0.0714 | 0.0266 | 0.0036 | 0.0 |
| LB-D10-2025-12-30-084453-0250071VFPCHC-2-2 | 200 | Liberia | 1.3207 | 0.0661 | 0.0416 | 0.0031 | 0.0 |
| LB-D11-2025-12-17-115859-0250319D-thin-4-1 | 29 | Liberia | 1.2788 | 0.0581 | 0.0 | 0.002 | 0.0 |
| LB-D11-2025-12-19-111309-0211715-VFPCHC-3-1 | 277 | Liberia | 1.1218 | 0.0556 | 0.0 | 0.0023 | 2.3871 |
| LB-D11-2025-12-19-131014-0241591-VFPCHC-3-2 | 278 | Liberia | 1.0517 | 0.0553 | 0.0 | 0.002 | 2.4076 |
| LB-D11-2025-12-19-134126-025073-VFPCHC-3-1 | 1 | Liberia | 1.0636 | 0.0607 | 0.0 | 0.0037 | 0.0 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 257 | Liberia | 0.9205 | 0.059 | 0.0157 | 0.0023 | 0.0 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 269 | Liberia | 0.8491 | 0.0501 | 0.0 | 0.0022 | 0.0 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 274 | Liberia | 1.0574 | 0.0538 | 0.0073 | 0.0021 | 0.0 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 279 | Liberia | 0.8023 | 0.0594 | 0.0 | 0.0024 | 1.7621 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 289 | Liberia | 1.0149 | 0.0564 | 0.0469 | 0.0028 | 0.0 |
| LB-D3-2025-09-02-141940-25087110-D-Only-1-2 | 42 | Liberia | 1.2058 | 0.0627 | 0.0187 | 0.0022 | 0.0 |
| LB-D3-2025-09-09-093425-250917463-D-Only-1-1 | 166 | Liberia | 1.118 | 0.0677 | 0.0276 | 0.0029 | 0.0 |
| LB-D3-2025-09-27-121918-17217958-D-thin-4-4 | 262 | Liberia | 0.9895 | 0.0659 | 0.0295 | 0.0031 | 0.0 |
| LB-D3-2025-10-03-104211-250917371-D-thin-2-3 | 4 | Liberia | 1.3722 | 0.0617 | 0.0303 | 0.0029 | 0.0 |
| LB-D3-2025-10-03-104643-250917465-D-thin-3-4 | 185 | Liberia | 1.1886 | 0.0632 | 0.0171 | 0.0014 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 1 | Liberia | 1.0482 | 0.0817 | 0.0 | 0.0018 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 16 | Liberia | 1.2068 | 0.0579 | 0.0 | 0.0021 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 17 | Liberia | 1.352 | 0.0561 | 0.0 | 0.0017 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 18 | Liberia | 1.2378 | 0.0558 | 0.0 | 0.002 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 19 | Liberia | 1.3267 | 0.0613 | 0.0 | 0.002 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 53 | Liberia | 1.126 | 0.0601 | 0.0 | 0.002 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 114 | Liberia | 1.0449 | 0.0556 | 0.0444 | 0.003 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 125 | Liberia | 1.2023 | 0.0489 | 0.0063 | 0.0017 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 126 | Liberia | 1.0397 | 0.0508 | 0.0076 | 0.0021 | 0.0 |
| LB-D3-2025-10-03-125352-2402169466D-thin-2-1 | 3 | Liberia | 1.1602 | 0.0509 | 0.0117 | 0.003 | 0.0 |
| LB-D3-2025-10-03-130859-250916865-D-thin-1-4 | 236 | Liberia | 1.203 | 0.0473 | 0.0197 | 0.0028 | 0.0 |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 134 | Liberia | 1.4271 | 0.0469 | 0.037 | 0.0032 | 0.0 |
| LB-D3-2025-10-22-132316-2411189646-D-thin-1-4 | 135 | Liberia | 1.187 | 0.0464 | 0.0 | 0.0024 | 2.2427 |
| LB-D3-2025-10-22-140622-250917738-D-thin-1-1 | 122 | Liberia | 1.3452 | 0.063 | 0.0 | 0.0028 | 2.4223 |
| LB-D3-2025-10-22-140622-250917738-D-thin-1-1 | 238 | Liberia | 1.0558 | 0.0478 | 0.0144 | 0.0023 | 0.0 |
| LB-D3-2025-10-24-113736-250918214-D-thin-2-3 | 96 | Liberia | 1.2039 | 0.0487 | 0.0 | 0.001 | 0.0 |
| LB-D3-2025-10-24-132012-25046898-D-thin-1-4 | 3 | Liberia | 1.2381 | 0.0478 | 0.0 | 0.002 | 2.338 |
| LB-D3-2025-10-24-132012-25046898-D-thin-1-4 | 305 | Liberia | 1.0568 | 0.0492 | 0.0137 | 0.0021 | 0.0 |
| LB-D3-2025-10-24-162727-230918080-D-thin-1-4 | 8 | Liberia | 1.1203 | 0.045 | 0.0 | 0.0019 | 0.0 |
| LB-D3-2025-10-25-105806-180951467-D-thin-1-1 | 270 | Liberia | 1.7886 | 0.0455 | 0.0107 | 0.0022 | 0.0 |
| LB-D3-2025-10-25-150947-250917467-D-thin-3-2 | 235 | Liberia | 1.3948 | 0.0495 | 0.0207 | 0.0028 | 0.0 |
| LB-D3-2025-10-27-123159-251123404-D-thin-4-1 | 48 | Liberia | 1.3002 | 0.0537 | 0.0186 | 0.0023 | 0.0 |
| LB-D3-2025-10-27-123159-251123404-D-thin-4-1 | 49 | Liberia | 1.2636 | 0.0483 | 0.0064 | 0.0019 | 0.0 |
| LB-D3-2025-10-27-124239-250916732-D-thin-1-3 | 301 | Liberia | 1.3511 | 0.0561 | 0.0411 | 0.0025 | 0.0 |
| LB-D3-2025-10-27-134711-250917368-D-thin-1-3 | 52 | Liberia | 1.3876 | 0.0536 | 0.03 | 0.0027 | 0.0 |
| LB-D3-2025-10-27-144635-250918691-D-thin-2-2 | 57 | Liberia | 1.3869 | 0.0469 | 0.0062 | 0.0021 | 0.0 |
| LB-D3-2025-10-27-144635-250918691-D-thin-2-2 | 243 | Liberia | 1.1609 | 0.0454 | 0.0 | 0.0014 | 0.0 |
| LB-D3-2025-10-27-145205-250917002-D-thin-3-3 | 310 | Liberia | 1.2626 | 0.0532 | 0.0031 | 0.0016 | 0.0 |
| LB-D3-2025-10-27-154305-250917412-D-thin-1-4 | 119 | Liberia | 1.2712 | 0.0486 | 0.0 | 0.0019 | 2.4503 |
| LB-D3-2025-10-27-155920-250713919-D-thin-3-3 | 169 | Liberia | 1.2504 | 0.0641 | 0.0 | 0.001 | 0.0 |
| LB-D3-2025-10-27-173317-250917493-D-thin-2-4 | 82 | Liberia | 1.3111 | 0.0482 | 0.0123 | 0.002 | 0.0 |
| LB-D5-2026-01-27-112616-0240052-VFPCHC-2-2 | 40 | Liberia | 1.2928 | 0.0483 | 0.0 | 0.0016 | 0.0 |
| KIT-62500763 | 200 | Tanzania | 24.9753 | 0.0445 | 0.0226 | 0.0021 | 0.0 |
| KIT-62501035 | 67 | Tanzania | 0.9237 | 0.0446 | 0.0361 | 0.0027 | 0.0 |
| KIT-62501062 | 83 | Tanzania | 0.6798 | 0.047 | 0.0 | 0.0015 | 0.0 |
| KIT-62501081 | 141 | Tanzania | 0.7498 | 0.0418 | 0.0155 | 0.0026 | 0.0 |
| KIT-62501087 | 271 | Tanzania | 0.6752 | 0.0416 | 0.0191 | 0.0026 | 0.0 |
| KTR-72502946 | 54 | Tanzania | 0.8919 | 0.0419 | 0.0284 | 0.0024 | 0.0 |
| KTR-72502946 | 198 | Tanzania | 0.9965 | 0.0414 | 0.0338 | 0.003 | 0.0 |
| NKR-72502319 | 119 | Tanzania | 0.9144 | 0.0447 | 0.0 | 0.0011 | 0.0 |
| NKR-72502319 | 293 | Tanzania | 1.0146 | 0.0422 | 0.0157 | 0.0024 | 0.0 |
| NKR-72502319 | 311 | Tanzania | 0.9176 | 0.038 | 0.0133 | 0.0023 | 0.0 |
| RUB-62501332 | 133 | Tanzania | 0.9019 | 0.039 | 0.028 | 0.0026 | 0.0 |
| RUB-62501389 | 284 | Tanzania | 0.864 | 0.0446 | 0.0309 | 0.0029 | 0.0 |
| RUB-62501518 | 315 | Tanzania | 1.0008 | 0.0508 | 0.0 | 0.0013 | 0.0 |
| RUB-62501529 | 87 | Tanzania | 0.8352 | 0.0462 | 0.0 | 0.001 | 0.0 |
| RUB-72501756 | 315 | Tanzania | 0.9415 | 0.0379 | 0.0177 | 0.0022 | 0.0 |
| PAT-070-3 | 34 | Uganda | 0.8981 | 0.0404 | 0.0293 | 0.0025 | 0.0 |
| PAT-072-1 | 14 | Uganda | 0.8635 | 0.0373 | 0.0053 | 0.0024 | 0.0 |
| PAT-072-1 | 94 | Uganda | 0.7299 | 0.0618 | 0.0396 | 0.0024 | 0.0 |
| PAT-154-1 | 478 | Uganda | 0.881 | 0.0408 | 0.0 | 0.0011 | 0.0 |
| PBC-225_AM-1 | 30 | Uganda | 0.8947 | 0.0433 | 0.0 | 0.001 | 0.0 |
| PBC-608-KH-1 | 171 | Uganda | 0.6961 | 0.0466 | 0.0304 | 0.003 | 0.0 |
| PBC-800-1 | 128 | Uganda | 0.604 | 0.0409 | 0.0 | 0.0019 | 0.0 |
| PBC-800-1 | 732 | Uganda | 0.6729 | 0.0441 | 0.0 | 0.0022 | 0.0 |
| PAT-103-2 | 441 | Uganda | 0.7748 | 0.0466 | 0.0 | 0.0013 | 0.0 |
| PAT-112-2 | 124 | Uganda | 0.673 | 0.0492 | 0.0 | 0.001 | 0.0 |

**Summary:**

| stage | min (s) | median (s) | max (s) | total (s) |
|---|---|---|---|---|
| gcs_fetch_s | 0.6040 | 1.0692 | 24.9753 | 122.0563 |
| time_initial_test_s | 0.0373 | 0.0492 | 0.0817 | 3.9627 |
| time_anisotropy_s | 0.0000 | 0.0092 | 0.0469 | 1.0194 |
| time_diffuse_fov_s | 0.0010 | 0.0022 | 0.0037 | 0.1696 |
| neighbor_fetch_s | 0.0000 | 0.0000 | 2.4503 | 16.0101 |

| country | n | median gcs_fetch_s | mean gcs_fetch_s |
|---|---|---|---|
| Liberia | 51 | 1.2030 | 1.5115 |
| Tanzania | 15 | 0.9144 | 2.4855 |
| Uganda | 10 | 0.7524 | 0.7688 |

Excluding the very first row of the run (a one-time GCS client cold-start cost), `gcs_fetch_s` ranges 0.60-24.98s with a median of 1.07s; the Tanzania outlier (row 54, `KIT-62500763`, this run's first Tanzania row) looks like a second, box-listing-specific cold-start rather than typical per-FOV cost (every subsequent Tanzania row is under 1s). **Neither `gcs_fov.py` (Liberia) nor `gcs_fov_multi.py` (Tanzania/Uganda) caches slide/box lookups across calls** -- every single fetch re-lists the Liberia `_Blue` folder and re-reads its `Scan.txt`, or (for Tanzania) re-checks up to 5 `TZ2025-Box<N>` prefixes, even for FOVs from the same scan/sample already resolved earlier in this same run. Uganda has no such lookup (direct path), which is consistent with it having the lowest mean fetch time despite no within-sample caching either. This isn't specific to this test -- it's how `scripts/score_labels.py` and `scripts/fetch_reference_images.py` already behave -- but it means per-FOV GCS time here is *not* representative of what a full-scan batch run would cost per FOV if slide/box resolution were cached once per sample_id; that's a real optimization opportunity if this pipeline is ever run at full-slide scale (see Recommendations). `time_initial_test_s`/`time_anisotropy_s`/`time_diffuse_fov_s` are all local CPU work (downsample/blur/threshold/FFT) and dominated entirely by network time -- consistent with the prior diffuse-fov timing note ([[project-fluorescence-diffuse-halo-investigation]]: ~22ms/image for the diffuse-fov step alone, matching `time_diffuse_fov_s`'s ~2-3ms here -- treat both as "a few ms, negligible next to network").

## Results: confusion matrices

Ground truth = `spot` column (is the halo artifact genuinely present). Predicted = `present`
directly (see "Method" above). All 4 matrices below are repeated for both variants.

### Diffuse-fov step NOT folded in (production behavior today)

**all** (n=76)

| | Predicted: spot | Predicted: no spot |
|---|---|---|
| Truth: spot | TP=36 | FN=8 |
| Truth: no spot | FP=5 | TN=27 |

FN rate: 8/44 (18.2%) -- FP rate: 5/32 (15.6%)

**background** (n=28)

| | Predicted: spot | Predicted: no spot |
|---|---|---|
| Truth: spot | TP=1 | FN=2 |
| Truth: no spot | FP=3 | TN=22 |

FN rate: 2/3 (66.7%) -- FP rate: 3/25 (12.0%)

**diffuse** (n=5)

| | Predicted: spot | Predicted: no spot |
|---|---|---|
| Truth: spot | TP=1 | FN=4 |
| Truth: no spot | FP=0 | TN=0 |

FN rate: 4/5 (80.0%) -- FP rate: n/a (no spot-negative rows in this subset)

**double** (n=5)

| | Predicted: spot | Predicted: no spot |
|---|---|---|
| Truth: spot | TP=4 | FN=1 |
| Truth: no spot | FP=0 | TN=0 |

FN rate: 1/5 (20.0%) -- FP rate: n/a (no spot-negative rows in this subset)

### Diffuse-fov step folded in, with the DIFFUSE_RATIO_MIN fix (`present_folded = present_base OR diffuse_halo_flag`)

**all** (n=76)

| | Predicted: spot | Predicted: no spot |
|---|---|---|
| Truth: spot | TP=42 | FN=2 |
| Truth: no spot | FP=5 | TN=27 |

FN rate: 2/44 (4.5%) -- FP rate: 5/32 (15.6%) -- **identical to the baseline FP rate: zero net new false positives**

**background** (n=28)

| | Predicted: spot | Predicted: no spot |
|---|---|---|
| Truth: spot | TP=3 | FN=0 |
| Truth: no spot | FP=3 | TN=22 |

FN rate: 0/3 (0.0%) -- FP rate: 3/25 (12.0%) -- **identical to baseline**

**diffuse** (n=5)

| | Predicted: spot | Predicted: no spot |
|---|---|---|
| Truth: spot | TP=4 | FN=1 |
| Truth: no spot | FP=0 | TN=0 |

FN rate: 1/5 (20.0%) -- FP rate: n/a (no spot-negative rows in this subset)

**double** (n=5)

| | Predicted: spot | Predicted: no spot |
|---|---|---|
| Truth: spot | TP=5 | FN=0 |
| Truth: no spot | FP=0 | TN=0 |

FN rate: 0/5 (0.0%) -- FP rate: n/a (no spot-negative rows in this subset)

## Discussion

**This section originally reported the diffuse-fov fold-in as a recall/specificity tradeoff
that traded a lot of false positives for a little more recall. Emily asked for a fix; the fix
is now in `src/overexposure.py` and the numbers below are what shipped, not the original
finding.** The "before" story, kept for context: 17 of 76 rows had `present_base=False` with a
large enough diffuse footprint to trigger the neighbor-trend check; 14 flipped from
`present=False` to `present=True` under fold-in -- 7 correct rescues of real halos the ratio
gate missed, but 7 new false positives, 6 of them `background`-tagged (ordinary elevated
illumination from puncta/staining, no real halo) and 1 (`fov126`) a fiber/debris artifact the
anisotropy filter had already correctly demoted. Folding in dropped the overall FN rate from
18.2% to 2.3% but more than doubled the FP rate, 15.6% to 37.5% -- and the `background` subset
alone went from FP 12.0% to 36.0%.

**The fix:** `diffuse_candidate()` now also requires `contrast_ratio >= DIFFUSE_RATIO_MIN
(2.30)` and, separately, requires a genuine ratio-gate miss (`contrast_ratio < RATIO_THRESHOLD`)
rather than accepting `present=False` for any reason. See `src/overexposure.py`'s module
docstring, "Ratio floor for diffuse candidates", for the full calibration writeup. Two design
alternatives were considered and rejected before this one: a new patch-grid illumination-
uniformity metric (tested against the real images and found to correlate at Spearman rho=0.95
with `contrast_ratio` -- a noisier restatement of an existing field, not a new signal), and a
ratio floor without the ratio-gate-miss requirement (keeps the `KIT-62501087` rescue below, but
leaves `fov126` unfixed). Emily chose the stricter version.

**Result with the fix: zero net new false positives, most of the recall gain kept.** FP stays
at 5/32 (15.6%) -- byte-identical to baseline, because the two anisotropy-mechanism rows
(`fov126`, `KIT-62501087`) and all 6 fake-`background` rows are now excluded from
`diffuse_candidate()` entirely (ratios 1.36-2.21, all below `DIFFUSE_RATIO_MIN`, or 13-14, both
above `RATIO_THRESHOLD` and reached `present=False` only via anisotropy). FN improves from
18.2% to 4.5% (8 missed real halos -> 2) -- slightly less improvement than the original,
unfixed fold-in's 2.3%, because the fix also excludes `KIT-62501087`'s rescue (an accident of
the anisotropy filter misfiring on a real halo, not the diffuse-fov step catching a faint one
-- see "Which FOVs flip" below). All 5 non-`KIT-62501087` real-halo rescues survive: the
`diffuse` subset's recall still improves 1/5 -> 4/5 and `double`'s 4/5 -> 5/5, unchanged from
the original fold-in.

**`fov279` is the one residual risk the fix doesn't structurally close.** It's `background`-
tagged, no real halo, `contrast_ratio=2.632` -- inside the new `[2.30, 3.0)` candidate band --
and is only excluded because `matches_neighbor_trend` happens to catch it (see
`src/overexposure.py`'s docstring). The ratio floor narrows how often that check has to do the
work; it doesn't replace it. Worth watching if `notes` labeling surfaces more cases like it.

**Baseline performance is already reasonably good** (FN 18.2%, FP 15.6% overall) for a
detector whose ratio/anisotropy design predates this specific labeled test set. `diffuse` is
the weakest baseline subset (FN 80.0%) precisely because it's defined as the faint/sub-ratio
population the diffuse-fov step targets -- which is exactly why folding it in (with the fix)
helps there so much, at no false-positive cost.

## Which FOVs flip if diffuse-fov is folded in

With the `DIFFUSE_RATIO_MIN` fix in place, only **6** rows have `present_base != present_folded`
-- down from the original 14 -- and every one of them is a correct rescue of a real halo the
ratio gate missed. Zero false positives are introduced by folding in.

| sample_id | fov_id | country | spot_truth | notes | contrast_ratio | diffuse_radius | outcome | preview |
|---|---|---|---|---|---|---|---|---|
| LB-D11-2025-12-19-111309-0211715-VFPCHC-3-1 | 277 | Liberia | yes | background | 2.75 | 176.2 | rescued (was FN) | [link](previews/LB-D11-2025-12-19-111309-0211715-VFPCHC-3-1__fov277__preview.png) |
| LB-D11-2025-12-19-131014-0241591-VFPCHC-3-2 | 278 | Liberia | yes | background | 2.43 | 161.9 | rescued (was FN) | [link](previews/LB-D11-2025-12-19-131014-0241591-VFPCHC-3-2__fov278__preview.png) |
| LB-D3-2025-10-22-132316-2411189646-D-thin-1-4 | 135 | Liberia | yes | diffuse | 2.59 | 155.7 | rescued (was FN) | [link](previews/LB-D3-2025-10-22-132316-2411189646-D-thin-1-4__fov135__preview.png) |
| LB-D3-2025-10-22-140622-250917738-D-thin-1-1 | 122 | Liberia | yes | double | 2.75 | 205.7 | rescued (was FN) | [link](previews/LB-D3-2025-10-22-140622-250917738-D-thin-1-1__fov122__preview.png) |
| LB-D3-2025-10-24-132012-25046898-D-thin-1-4 | 3 | Liberia | yes | diffuse | 2.45 | 129.4 | rescued (was FN) | [link](previews/LB-D3-2025-10-24-132012-25046898-D-thin-1-4__fov3__preview.png) |
| LB-D3-2025-10-27-154305-250917412-D-thin-1-4 | 119 | Liberia | yes | diffuse | 2.91 | 84.9 | rescued (was FN) | [link](previews/LB-D3-2025-10-27-154305-250917412-D-thin-1-4__fov119__preview.png) |

### The 8 rows that used to flip, and why they're excluded now

For the audit trail: before the fix, these 8 rows also flipped `present_base=False` ->
`present_folded=True`. All 8 are now correctly excluded from `diffuse_candidate()` before ever
reaching the neighbor-trend check.

**6 fake-`background` false positives, excluded by the new `DIFFUSE_RATIO_MIN=2.30` floor**
(all `contrast_ratio` 1.36-2.21, below the floor): `LB-D11-...-134126...` fov=1 (1.36),
`LB-D3-...-thin-4` fov=269 (2.15), `LB-D3-...-2404175445-2-3` fov=1 (1.92)/fov=19 (2.21)/fov=53
(2.05), `PBC-800-1` fov=732 (2.13). These are ordinary elevated-background FOVs, no real halo
-- the population this fix targets.

**`fov126` (`LB-D3-...-2404175445-2-3`), excluded by the ratio-gate-miss requirement, not the
floor.** Its `contrast_ratio=13.39` clears `RATIO_THRESHOLD=3.0` easily -- it was never a
ratio-gate miss. `results.csv` shows `anisotropy=0.5588`, above `ANISOTROPY_THRESHOLD=0.35`, so
this candidate was correctly demoted to `present=False` by the fiber/hair-debris check
(consistent with its `artifact` note). `diffuse_candidate()`'s old gate (`not present`, any
reason) let it through anyway; requiring `contrast_ratio < RATIO_THRESHOLD` now excludes it
structurally, since it's mechanically impossible to reach `present=False` via anisotropy while
also having `contrast_ratio < RATIO_THRESHOLD` (anisotropy is only evaluated when the ratio
gate already said yes).

**`KIT-62501087` fov=271, excluded the same way -- the accepted tradeoff.** This is the mirror
case: a real halo (`spot_truth=yes`) mis-demoted by the anisotropy filter
(`contrast_ratio=14.27`, `anisotropy=0.4602`), not a faint halo the ratio gate missed. Looking
at its preview, it's a clean, sharply-defined, corner-clipped circular halo -- plausibly the
corner-clipping itself biased the FFT-based anisotropy measurement toward the two frame-edge
axes, mimicking the directional-energy signature the check is designed to catch in actual
fibers. It's also the first Tanzania FOV in this test where the anisotropy value crossed
`ANISOTROPY_THRESHOLD` at all, and that threshold was calibrated exclusively on one Liberia
slide's real-halo-vs-hair examples -- so this could equally be a genuine cross-country
calibration gap. Either way, the diffuse-fov step's old fold-in flip here was never really
catching a faint halo (its intended job) -- it was incidentally undoing an unrelated anisotropy
misfire, and Emily chose to exclude it along with `fov126` rather than special-case it back in
(see Discussion). This FOV goes back to being a false negative under the fix.

## FN/FP examples

Annotated previews for all 13 rows that are a false negative or false positive in either
variant, with the fix applied, grouped into the same 4 buckets used throughout this doc. Red
outline = `present` (this variant's detector call fired); green = did not fire. Caption lines
show truth/notes, both variants' `present`, contrast ratio, and diffuse radius. (Down from 20
before the fix -- bucket D, "new false positive introduced by folding in," is now empty; see
"Which FOVs flip" above for the 8 rows that used to populate buckets A/D and are now excluded.)

### A -- rescued by folding in (spot_truth=yes, missed at baseline, caught after fold-in) (n=6)

![LB-D11-2025-12-19-111309-0211715-VFPCHC-3-1 fov=277 (Liberia) -- truth=yes, notes=background, ratio=2.75](previews/LB-D11-2025-12-19-111309-0211715-VFPCHC-3-1__fov277__preview.png)
*LB-D11-2025-12-19-111309-0211715-VFPCHC-3-1 fov=277 (Liberia) -- truth=yes, notes=background, ratio=2.75*

![LB-D11-2025-12-19-131014-0241591-VFPCHC-3-2 fov=278 (Liberia) -- truth=yes, notes=background, ratio=2.43](previews/LB-D11-2025-12-19-131014-0241591-VFPCHC-3-2__fov278__preview.png)
*LB-D11-2025-12-19-131014-0241591-VFPCHC-3-2 fov=278 (Liberia) -- truth=yes, notes=background, ratio=2.43*

![LB-D3-2025-10-22-132316-2411189646-D-thin-1-4 fov=135 (Liberia) -- truth=yes, notes=diffuse, ratio=2.59](previews/LB-D3-2025-10-22-132316-2411189646-D-thin-1-4__fov135__preview.png)
*LB-D3-2025-10-22-132316-2411189646-D-thin-1-4 fov=135 (Liberia) -- truth=yes, notes=diffuse, ratio=2.59*

![LB-D3-2025-10-22-140622-250917738-D-thin-1-1 fov=122 (Liberia) -- truth=yes, notes=double, ratio=2.75](previews/LB-D3-2025-10-22-140622-250917738-D-thin-1-1__fov122__preview.png)
*LB-D3-2025-10-22-140622-250917738-D-thin-1-1 fov=122 (Liberia) -- truth=yes, notes=double, ratio=2.75*

![LB-D3-2025-10-24-132012-25046898-D-thin-1-4 fov=3 (Liberia) -- truth=yes, notes=diffuse, ratio=2.45](previews/LB-D3-2025-10-24-132012-25046898-D-thin-1-4__fov3__preview.png)
*LB-D3-2025-10-24-132012-25046898-D-thin-1-4 fov=3 (Liberia) -- truth=yes, notes=diffuse, ratio=2.45*

![LB-D3-2025-10-27-154305-250917412-D-thin-1-4 fov=119 (Liberia) -- truth=yes, notes=diffuse, ratio=2.91](previews/LB-D3-2025-10-27-154305-250917412-D-thin-1-4__fov119__preview.png)
*LB-D3-2025-10-27-154305-250917412-D-thin-1-4 fov=119 (Liberia) -- truth=yes, notes=diffuse, ratio=2.91*

### B -- still missed after folding in (spot_truth=yes, missed by both variants) (n=2)

![LB-D3-2025-10-24-162727-230918080-D-thin-1-4 fov=8 (Liberia) -- truth=yes, notes=diffuse, ratio=1.98](previews/LB-D3-2025-10-24-162727-230918080-D-thin-1-4__fov8__preview.png)
*LB-D3-2025-10-24-162727-230918080-D-thin-1-4 fov=8 (Liberia) -- truth=yes, notes=diffuse, ratio=1.98*

![KIT-62501087 fov=271 (Tanzania) -- truth=yes, notes=(none), ratio=14.27](previews/KIT-62501087__fov271__preview.png)
*KIT-62501087 fov=271 (Tanzania) -- truth=yes, notes=(none), ratio=14.27 -- moved here from bucket A after the fix; see "Which FOVs flip" above for why this rescue was traded away.*

(fov=96, `LB-D3-2025-10-24-113736-250918214-D-thin-2-3`, was originally in this bucket but has
been removed after Emily flagged its `spot=yes` label as incorrect on 2026-08-07 -- see the
`*` footnote under "Input labels". With the corrected `spot=no` label it's a true negative in
both variants, not an error case.)

### C -- false positive already at baseline (spot_truth=no, present_base=True; folding in can't fix these, since it only ever turns present False->True) (n=5)

![LB-D3-2025-08-30-103102-250876706-D-thin-4 fov=257 (Liberia) -- truth=no, notes=background, ratio=3.56](previews/LB-D3-2025-08-30-103102-250876706-D-thin-4__fov257__preview.png)
*LB-D3-2025-08-30-103102-250876706-D-thin-4 fov=257 (Liberia) -- truth=no, notes=background, ratio=3.56*

![LB-D3-2025-08-30-103102-250876706-D-thin-4 fov=274 (Liberia) -- truth=no, notes=background, ratio=6.49](previews/LB-D3-2025-08-30-103102-250876706-D-thin-4__fov274__preview.png)
*LB-D3-2025-08-30-103102-250876706-D-thin-4 fov=274 (Liberia) -- truth=no, notes=background, ratio=6.49*

![LB-D3-2025-08-30-103102-250876706-D-thin-4 fov=289 (Liberia) -- truth=no, notes=background, ratio=5.12](previews/LB-D3-2025-08-30-103102-250876706-D-thin-4__fov289__preview.png)
*LB-D3-2025-08-30-103102-250876706-D-thin-4 fov=289 (Liberia) -- truth=no, notes=background, ratio=5.12*

![PAT-072-1 fov=14 (Uganda) -- truth=no, notes=artifact, ratio=3.15](previews/PAT-072-1__fov14__preview.png)
*PAT-072-1 fov=14 (Uganda) -- truth=no, notes=artifact, ratio=3.15*

![PAT-072-1 fov=94 (Uganda) -- truth=no, notes=artifact, ratio=5.91](previews/PAT-072-1__fov94__preview.png)
*PAT-072-1 fov=94 (Uganda) -- truth=no, notes=artifact, ratio=5.91*

### D -- new false positive introduced by folding in (n=0)

Empty. Before the fix, this bucket held the 6 fake-`background` false positives plus `fov126`
(the anisotropy-demoted debris artifact) -- see "Which FOVs flip" above for the full list and
why each is now excluded.

## Caveats

- **Subset sizes are small.** `diffuse` and `double` are 5 rows each; a single-row flip shifts
  their FN/FP rate by 20 points. Treat the subset numbers as directional, not statistically
  robust, until `notes` is filled in further ([[project-fluorescence-diffuse-halo-investigation]]
  already flags the underlying diffuse-halo signal as calibrated on n=1 per class).
- **`notes` is incomplete.** Many rows (mostly straightforward, unambiguous cases) have no
  `notes` value and are excluded from every subset but `all`.
- **GCS per-FOV timings include repeated, uncached slide/box lookups** (see "Per-FOV runtime"
  above) -- don't use these numbers directly to estimate full-slide batch throughput.
- **This doc originally had the predicted/ground-truth polarity inverted** (comparing `NOT
  present` against `spot`, on the mistaken assumption that `spot` meant "genuine parasite
  signal independent of the overexposure artifact"). Corrected 2026-08-07 after Emily clarified
  that `spot` ground truth *is* ground truth on the halo artifact's presence.
- **`DIFFUSE_RATIO_MIN` is a fit on the same 12 labeled rows it was validated against** (6 fake-
  `background` FPs, 6 real sub-ratio halos), cross-checked against 3 historical FOVs from the
  earlier fov62 investigation. It's a much cheaper, wider-margin fit than the patch-uniformity
  metric that was tried and rejected, using a field (`contrast_ratio`) the file already trusts
  -- but it's still calibrated on a small population. `fov279` (see "Discussion") is a known,
  unresolved near-miss inside the new candidate band.
- **`KIT-62501087`'s rescue was deliberately traded away** to fix `fov126`'s false positive
  (Variant D, chosen by Emily over Variant C -- see "Which FOVs flip"). It's a real halo and is
  now a false negative again under both variants.

## Files

- `README.md` -- this file
- `results.csv` -- full per-row output: detection fields (`present_base`/`present_folded`/
  `diffuse_halo_flag`/`contrast_ratio`/`anisotropy`/`diffuse_radius`/etc.), both predicted-spot
  variants, and all runtime columns
- `previews/` -- annotated preview thumbnails for all 13 FN/FP rows (see "FN/FP examples"),
  plus `previews/manifest.csv` mapping each file back to its full result row and bucket
- `../../src/gcs_fov_multi.py` -- new LB/TZ/UG FOV resolver (streams, no disk cache)
- `../../scripts/run_overexposed_diverse_test.py` -- pipeline runner used for this test
- `../../scripts/analyze_overexposed_diverse.py` -- confusion-matrix/FN-FP tally generator
- `../../scripts/render_fn_fp_previews.py` -- renders the `previews/` thumbnails

## Recommendations

1. **Cache slide/box resolution per sample_id within a run** if this pipeline is ever run at
   full-slide or multi-scan batch scale -- `gcs_fov.py`/`gcs_fov_multi.py` currently re-resolve
   on every single fetch, which is fine for a 76-row spot-check but would add up across a full
   slide (hundreds of FOVs, often the same handful of samples repeated).
2. **Finish categorizing `notes`** so the background/diffuse/double (and any new categories)
   breakdowns cover the full dataset, not just the ~35 rows currently tagged.
3. **Done, 2026-08-07: `diffuse_candidate()` now requires `DIFFUSE_RATIO_MIN <= contrast_ratio
   < RATIO_THRESHOLD`** (see `src/overexposure.py`'s docstring). This was originally going to
   be "recalibrate `DIFFUSE_ABS_DELTA`," but the actual fix turned out to be scoping candidacy
   with a field already computed (`contrast_ratio`), not a new threshold on the absolute-delta
   footprint. Folding the diffuse-fov step into `present` is now net-positive on this labeled
   set: zero new false positives, FN rate 18.2% -> 4.5%.
4. **Recalibrate `DIFFUSE_RATIO_MIN` (and re-check `fov279`) once more `background`-tagged
   labels exist**, particularly outside Liberia -- the current calibration set is 12 rows, 11
   of them Liberia.
5. **If `KIT-62501087`'s rescue matters enough to want back, investigate the anisotropy
   check's corner-clipping/cross-country behavior directly** rather than re-widening
   `diffuse_candidate()` to cover it -- see "Which FOVs flip" for why that would also let
   `fov126` back in.
