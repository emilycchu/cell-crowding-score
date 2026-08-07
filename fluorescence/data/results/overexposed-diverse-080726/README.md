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
| LB-D3-2025-10-24-113736-250918214-D-thin-2-3 | 96 | A. Chen | Liberia | Overexposed | yes |  |
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

## Method and what "predicted" means here

Full per-row detection was run via `scripts/run_overexposed_diverse_test.py`, which streams
each FOV from GCS and calls the same production code path as `scripts/score_labels.py`:
`detect_overexposure()` (ratio gate -> anisotropy-fft fiber-debris demotion), plus the
advisory-only diffuse-fov step (`diffuse_candidate` -> neighbor-trend check ->
`diffuse_halo_flag`, fetching the 2 preceding fov_ids for context, same as
`scripts/scan_diffuse_candidates.py`).

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
for the 17 rows that were ratio-failing with a large-enough diffuse footprint to trigger a
neighbor-trend check (`diffuse_candidate`); it covers fetching + detecting on up to 2
preceding fov_ids for that check alone.

| sample_id | fov_id | country | gcs_fetch_s | initial_test_s | anisotropy_s | diffuse_fov_s | neighbor_fetch_s |
|---|---|---|---|---|---|---|---|
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 153 | Liberia | 14.0097 | 0.0512 | 0.0123 | 0.0022 | 0.0 |
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 154 | Liberia | 1.3379 | 0.0537 | 0.0212 | 0.0022 | 0.0 |
| LB-D10-2025-12-30-083614-0250901VFPCHC-2-1 | 210 | Liberia | 1.376 | 0.0567 | 0.0127 | 0.0021 | 0.0 |
| LB-D10-2025-12-30-083614-0250901VFPCHC-2-1 | 227 | Liberia | 1.2439 | 0.0527 | 0.0164 | 0.0027 | 0.0 |
| LB-D10-2025-12-30-084453-0250071VFPCHC-2-2 | 200 | Liberia | 1.5098 | 0.0592 | 0.0361 | 0.0023 | 0.0 |
| LB-D11-2025-12-17-115859-0250319D-thin-4-1 | 29 | Liberia | 1.9503 | 0.0558 | 0.0 | 0.0029 | 3.4523 |
| LB-D11-2025-12-19-111309-0211715-VFPCHC-3-1 | 277 | Liberia | 2.2825 | 0.0532 | 0.0 | 0.0021 | 3.3588 |
| LB-D11-2025-12-19-131014-0241591-VFPCHC-3-2 | 278 | Liberia | 1.8582 | 0.0565 | 0.0 | 0.0021 | 3.0643 |
| LB-D11-2025-12-19-134126-025073-VFPCHC-3-1 | 1 | Liberia | 1.6186 | 0.05 | 0.0 | 0.0023 | 0.0 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 257 | Liberia | 1.5743 | 0.0532 | 0.0154 | 0.0023 | 0.0 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 269 | Liberia | 1.3516 | 0.0558 | 0.0 | 0.0019 | 3.1276 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 274 | Liberia | 1.6508 | 0.0481 | 0.0068 | 0.0021 | 0.0 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 279 | Liberia | 1.4803 | 0.0503 | 0.0 | 0.0018 | 2.9643 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 289 | Liberia | 1.3793 | 0.0472 | 0.0319 | 0.0025 | 0.0 |
| LB-D3-2025-09-02-141940-25087110-D-Only-1-2 | 42 | Liberia | 3.9464 | 0.049 | 0.0161 | 0.0023 | 0.0 |
| LB-D3-2025-09-09-093425-250917463-D-Only-1-1 | 166 | Liberia | 2.2452 | 0.0497 | 0.0178 | 0.0022 | 0.0 |
| LB-D3-2025-09-27-121918-17217958-D-thin-4-4 | 262 | Liberia | 1.748 | 0.0485 | 0.0256 | 0.0028 | 0.0 |
| LB-D3-2025-10-03-104211-250917371-D-thin-2-3 | 4 | Liberia | 1.8197 | 0.0484 | 0.0224 | 0.0024 | 0.0 |
| LB-D3-2025-10-03-104643-250917465-D-thin-3-4 | 185 | Liberia | 1.6108 | 0.0516 | 0.014 | 0.0013 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 1 | Liberia | 1.5482 | 0.053 | 0.0 | 0.0019 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 16 | Liberia | 1.7044 | 0.0499 | 0.0 | 0.0018 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 17 | Liberia | 1.537 | 0.0468 | 0.0 | 0.0017 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 18 | Liberia | 1.4336 | 0.0889 | 0.0 | 0.0019 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 19 | Liberia | 1.3621 | 0.0574 | 0.0 | 0.0019 | 2.6905 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 53 | Liberia | 1.5994 | 0.0543 | 0.0 | 0.0017 | 3.1115 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 114 | Liberia | 1.603 | 0.0694 | 0.0497 | 0.0031 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 125 | Liberia | 1.7148 | 0.0584 | 0.0064 | 0.0016 | 0.0 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 126 | Liberia | 1.3878 | 0.0562 | 0.0078 | 0.0027 | 2.8854 |
| LB-D3-2025-10-03-125352-2402169466D-thin-2-1 | 3 | Liberia | 1.4922 | 0.0563 | 0.0115 | 0.0022 | 0.0 |
| LB-D3-2025-10-03-130859-250916865-D-thin-1-4 | 236 | Liberia | 1.461 | 0.0542 | 0.0214 | 0.0026 | 0.0 |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 134 | Liberia | 2.0359 | 0.0556 | 0.0361 | 0.003 | 0.0 |
| LB-D3-2025-10-22-132316-2411189646-D-thin-1-4 | 135 | Liberia | 1.543 | 0.0635 | 0.0 | 0.0025 | 2.7661 |
| LB-D3-2025-10-22-140622-250917738-D-thin-1-1 | 122 | Liberia | 1.5306 | 0.0553 | 0.0 | 0.0025 | 3.2133 |
| LB-D3-2025-10-22-140622-250917738-D-thin-1-1 | 238 | Liberia | 1.9281 | 0.0515 | 0.0151 | 0.0024 | 0.0 |
| LB-D3-2025-10-24-113736-250918214-D-thin-2-3 | 96 | Liberia | 2.5637 | 0.0524 | 0.0 | 0.0011 | 0.0 |
| LB-D3-2025-10-24-132012-25046898-D-thin-1-4 | 3 | Liberia | 1.9472 | 0.0517 | 0.0 | 0.0021 | 3.8082 |
| LB-D3-2025-10-24-132012-25046898-D-thin-1-4 | 305 | Liberia | 1.9716 | 0.0508 | 0.014 | 0.0026 | 0.0 |
| LB-D3-2025-10-24-162727-230918080-D-thin-1-4 | 8 | Liberia | 1.8512 | 0.0493 | 0.0 | 0.0021 | 3.2547 |
| LB-D3-2025-10-25-105806-180951467-D-thin-1-1 | 270 | Liberia | 2.4905 | 0.0473 | 0.0101 | 0.0023 | 0.0 |
| LB-D3-2025-10-25-150947-250917467-D-thin-3-2 | 235 | Liberia | 1.9834 | 0.0503 | 0.0223 | 0.0027 | 0.0 |
| LB-D3-2025-10-27-123159-251123404-D-thin-4-1 | 48 | Liberia | 2.6114 | 0.0588 | 0.0207 | 0.0041 | 0.0 |
| LB-D3-2025-10-27-123159-251123404-D-thin-4-1 | 49 | Liberia | 1.8573 | 0.0506 | 0.0058 | 0.0025 | 0.0 |
| LB-D3-2025-10-27-124239-250916732-D-thin-1-3 | 301 | Liberia | 1.6959 | 0.0631 | 0.052 | 0.0028 | 0.0 |
| LB-D3-2025-10-27-134711-250917368-D-thin-1-3 | 52 | Liberia | 1.9126 | 0.0561 | 0.0263 | 0.0025 | 0.0 |
| LB-D3-2025-10-27-144635-250918691-D-thin-2-2 | 57 | Liberia | 1.9867 | 0.0534 | 0.006 | 0.0022 | 0.0 |
| LB-D3-2025-10-27-144635-250918691-D-thin-2-2 | 243 | Liberia | 1.8926 | 0.0611 | 0.0 | 0.001 | 0.0 |
| LB-D3-2025-10-27-145205-250917002-D-thin-3-3 | 310 | Liberia | 1.6342 | 0.0527 | 0.0029 | 0.0017 | 0.0 |
| LB-D3-2025-10-27-154305-250917412-D-thin-1-4 | 119 | Liberia | 1.6482 | 0.06 | 0.0 | 0.002 | 3.4071 |
| LB-D3-2025-10-27-155920-250713919-D-thin-3-3 | 169 | Liberia | 1.7499 | 0.0641 | 0.0 | 0.0011 | 0.0 |
| LB-D3-2025-10-27-173317-250917493-D-thin-2-4 | 82 | Liberia | 1.9329 | 0.0585 | 0.0186 | 0.0027 | 0.0 |
| LB-D5-2026-01-27-112616-0240052-VFPCHC-2-2 | 40 | Liberia | 2.787 | 0.0523 | 0.0 | 0.0018 | 3.6355 |
| KIT-62500763 | 200 | Tanzania | 24.8049 | 0.0332 | 0.0199 | 0.0028 | 0.0 |
| KIT-62501035 | 67 | Tanzania | 1.0191 | 0.033 | 0.0301 | 0.0029 | 0.0 |
| KIT-62501062 | 83 | Tanzania | 0.8403 | 0.0332 | 0.0 | 0.001 | 0.0 |
| KIT-62501081 | 141 | Tanzania | 1.0577 | 0.0357 | 0.0157 | 0.0022 | 0.0 |
| KIT-62501087 | 271 | Tanzania | 0.9844 | 0.0422 | 0.0167 | 0.0026 | 1.7317 |
| KTR-72502946 | 54 | Tanzania | 1.1398 | 0.0353 | 0.026 | 0.0023 | 0.0 |
| KTR-72502946 | 198 | Tanzania | 1.2847 | 0.0423 | 0.0469 | 0.0033 | 0.0 |
| NKR-72502319 | 119 | Tanzania | 1.0215 | 0.0365 | 0.0 | 0.001 | 0.0 |
| NKR-72502319 | 293 | Tanzania | 1.1657 | 0.0351 | 0.0166 | 0.0023 | 0.0 |
| NKR-72502319 | 311 | Tanzania | 1.207 | 0.0363 | 0.0131 | 0.0022 | 0.0 |
| RUB-62501332 | 133 | Tanzania | 1.3503 | 0.0425 | 0.0203 | 0.0024 | 0.0 |
| RUB-62501389 | 284 | Tanzania | 1.022 | 0.0364 | 0.0266 | 0.0023 | 0.0 |
| RUB-62501518 | 315 | Tanzania | 1.3214 | 0.041 | 0.0 | 0.001 | 0.0 |
| RUB-62501529 | 87 | Tanzania | 1.0089 | 0.0401 | 0.0 | 0.001 | 0.0 |
| RUB-72501756 | 315 | Tanzania | 1.1637 | 0.0469 | 0.024 | 0.0024 | 0.0 |
| PAT-070-3 | 34 | Uganda | 1.191 | 0.0488 | 0.0424 | 0.003 | 0.0 |
| PAT-072-1 | 14 | Uganda | 1.0437 | 0.0393 | 0.0068 | 0.0021 | 0.0 |
| PAT-072-1 | 94 | Uganda | 1.0505 | 0.0451 | 0.0497 | 0.0024 | 0.0 |
| PAT-154-1 | 478 | Uganda | 1.3411 | 0.0335 | 0.0 | 0.0009 | 0.0 |
| PBC-225_AM-1 | 30 | Uganda | 1.2138 | 0.037 | 0.0 | 0.001 | 0.0 |
| PBC-608-KH-1 | 171 | Uganda | 1.167 | 0.0356 | 0.0316 | 0.0029 | 0.0 |
| PBC-800-1 | 128 | Uganda | 1.2821 | 0.0342 | 0.0 | 0.0018 | 2.3308 |
| PBC-800-1 | 732 | Uganda | 1.1419 | 0.0416 | 0.0 | 0.002 | 2.545 |
| PAT-103-2 | 441 | Uganda | 1.2169 | 0.0331 | 0.0 | 0.001 | 0.0 |
| PAT-112-2 | 124 | Uganda | 1.1394 | 0.0406 | 0.0 | 0.0009 | 0.0 |

**Summary:**

| stage | min (s) | median (s) | max (s) | total (s) |
|---|---|---|---|---|
| gcs_fetch_s | 0.8403 | 1.5400 | 24.8049 | 156.5695 |
| time_initial_test_s | 0.0330 | 0.0504 | 0.0889 | 3.7525 |
| time_anisotropy_s | 0.0000 | 0.0089 | 0.0520 | 0.9618 |
| time_diffuse_fov_s | 0.0009 | 0.0022 | 0.0041 | 0.1630 |
| neighbor_fetch_s | 0.0000 | 0.0000 | 3.8082 | 51.3471 |

| country | n | median gcs_fetch_s | mean gcs_fetch_s |
|---|---|---|---|
| Liberia | 51 | 1.70 | 2.05 |
| Tanzania | 15 | 1.14 | 2.69 |
| Uganda | 10 | 1.18 | 1.18 |

Excluding the very first row of the run (14.0s, LB -- a one-time GCS client cold-start cost),
`gcs_fetch_s` ranges 0.84-24.8s with a median of 1.54s; the 24.8s Tanzania outlier (row 54,
`KIT-62500763`) is the first Tanzania row and looks like a second, box-listing-specific
cold-start rather than typical per-FOV cost (every subsequent Tanzania row is ~1s). **Neither
`gcs_fov.py` (Liberia) nor `gcs_fov_multi.py` (Tanzania/Uganda) caches slide/box lookups
across calls** -- every single fetch re-lists the Liberia `_Blue` folder and re-reads its
`Scan.txt`, or (for Tanzania) re-checks up to 5 `TZ2025-Box<N>` prefixes, even for FOVs from
the same scan/sample already resolved earlier in this same run. Uganda has no such lookup
(direct path), which is consistent with it having the lowest mean fetch time despite no
within-sample caching either. This isn't specific to this test -- it's how
`scripts/score_labels.py` and `scripts/fetch_reference_images.py` already behave -- but it
means per-FOV GCS time here is *not* representative of what a full-scan batch run would cost
per FOV if slide/box resolution were cached once per sample_id; that's a real optimization
opportunity if this pipeline is ever run at full-slide scale (see Recommendations).
`time_initial_test_s`/`time_anisotropy_s`/`time_diffuse_fov_s` are all local CPU work
(downsample/blur/threshold/FFT) and dominated entirely by network time -- consistent with the
prior diffuse-fov timing note ([[project-fluorescence-diffuse-halo-investigation]]: ~22ms/image
for the diffuse-fov step alone, matching `time_diffuse_fov_s`'s ~2-3ms here... actually smaller
here since that estimate included more overhead; treat both as "a few ms, negligible next to
network").

## Results: confusion matrices

Ground truth = `spot` column (is the halo artifact genuinely present). Predicted = `present`
directly (see "Method" above). All 4 matrices below are repeated for both variants.

### Diffuse-fov step NOT folded in (production behavior today)

**all** (n=76)

| | Predicted: spot | Predicted: no spot |
|---|---|---|
| Truth: spot | TP=36 | FN=9 |
| Truth: no spot | FP=5 | TN=26 |

FN rate: 9/45 (20.0%) -- FP rate: 5/31 (16.1%)

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

### Diffuse-fov step folded in (`present_folded = present_base OR diffuse_halo_flag`)

**all** (n=76)

| | Predicted: spot | Predicted: no spot |
|---|---|---|
| Truth: spot | TP=43 | FN=2 |
| Truth: no spot | FP=12 | TN=19 |

FN rate: 2/45 (4.4%) -- FP rate: 12/31 (38.7%)

**background** (n=28)

| | Predicted: spot | Predicted: no spot |
|---|---|---|
| Truth: spot | TP=3 | FN=0 |
| Truth: no spot | FP=9 | TN=16 |

FN rate: 0/3 (0.0%) -- FP rate: 9/25 (36.0%)

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

**Folding in the diffuse-fov step is a real recall/specificity tradeoff: it rescues most of
the faint halos the ratio gate misses, at the cost of new false positives on ordinary
elevated-background FOVs.** 17 of 76 rows were ratio-failing candidates with a large enough
diffuse footprint to trigger the neighbor-trend check; 14 were flagged as isolated diffuse
halos (didn't match a neighbor's trend) and flipped from `present=False` to `present=True`
under fold-in:

| notes category | spot_truth=yes flips (helps -- rescues a missed halo) | spot_truth=no flips (hurts -- new false positive) |
|---|---|---|
| background | 2 | 6 |
| artifact | 0 | 1 |
| diffuse | 3 | 0 |
| double | 1 | 0 |
| (blank) | 1 | 0 |
| **total** | **7** | **7** |

Overall: FN rate drops from 20.0% to 4.4% (missing 9 real halos -> missing 2), while FP rate
more than doubles, 16.1% to 38.7% (5 false positives -> 12). The gains land almost entirely on
the cases the step was built for -- **all 3 ratio-failing `diffuse`-tagged real halos and the
1 `double`-tagged one get correctly rescued** (`diffuse` subset recall 1/5 -> 4/5, `double`
5/5 -> 5/5 with the pre-existing FN also caught). The cost lands almost entirely on
`background`-tagged FOVs: 6 of the 7 new false positives are rows annotated `background`
(ordinary elevated illumination from puncta/staining, not a real halo), pushing that subset's
FP rate from 12.0% to 36.0%. This lines up with a risk `src/overexposure.py`'s own module
docstring already calls out for the *ratio* gate's design ("a plain brightness-delta threshold
produced false positives on FOVs that were simply uniformly brighter overall... without an
actual halo") -- `DIFFUSE_ABS_DELTA` is exactly that kind of absolute-delta threshold, applied
without the ratio gate's normalization, so it's plausible this is the same failure mode
resurfacing in the diffuse-fov step specifically.

Two rows also relied on Tanzania/Uganda cross-country data for the diffuse check for the first
time (`KIT-62501087` fov=271, `PBC-800-1` fov=732) -- the diffuse-fov constants
(`DIFFUSE_RADIUS_MIN`, `NEIGHBOR_CENTROID_MATCH_DIST`, `NEIGHBOR_RADIUS_MATCH_FACTOR`) were
calibrated only on Liberia FOVs, so these two flips are a first (informal) look at whether
that calibration transfers, not a validation of it. (`KIT-62501087` was a `spot_truth=yes`
rescue; `PBC-800-1` fov=732 was a `background`-tagged false positive.)

**Baseline performance is already reasonably good** (FN 20.0%, FP 16.1% overall) for a
detector whose ratio/anisotropy design predates this specific labeled test set. `diffuse` is
the weakest baseline subset (FN 80.0%) precisely because it's defined as the faint/sub-ratio
population the diffuse-fov step targets -- which is exactly why folding it in helps there so
much.

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
  that `spot` ground truth *is* ground truth on the halo artifact's presence. `results.csv`'s
  `predicted_spot_base`/`predicted_spot_folded` columns were patched in place to match
  (they're now identical to `present_base`/`present_folded`); no GCS data was re-fetched.

## Files

- `README.md` -- this file
- `results.csv` -- full per-row output: detection fields (`present_base`/`present_folded`/
  `diffuse_halo_flag`/`contrast_ratio`/`anisotropy`/`diffuse_radius`/etc.), both predicted-spot
  variants, and all runtime columns
- `../../src/gcs_fov_multi.py` -- new LB/TZ/UG FOV resolver (streams, no disk cache)
- `../../scripts/run_overexposed_diverse_test.py` -- pipeline runner used for this test
- `../../scripts/analyze_overexposed_diverse.py` -- confusion-matrix/FN-FP tally generator

## Recommendations

1. **Cache slide/box resolution per sample_id within a run** if this pipeline is ever run at
   full-slide or multi-scan batch scale -- `gcs_fov.py`/`gcs_fov_multi.py` currently re-resolve
   on every single fetch, which is fine for a 76-row spot-check but would add up across a full
   slide (hundreds of FOVs, often the same handful of samples repeated).
2. **Finish categorizing `notes`** so the background/diffuse/double (and any new categories)
   breakdowns cover the full dataset, not just the ~35 rows currently tagged.
3. **Consider folding the diffuse-fov step into `present`, but recalibrate `DIFFUSE_ABS_DELTA`
   first specifically against `background`-tagged (elevated-illumination, no-halo) FOVs** --
   this test is the first labeled evidence that it substantially improves recall on faint/
   diffuse real halos (the case it was built for), but more than doubles the false-positive
   rate, concentrated on exactly the ordinary-background-elevation failure mode the ratio gate
   was originally designed to avoid.
