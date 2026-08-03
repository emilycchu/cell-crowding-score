# Extended detector test: CSV rows 9-13 + random same-slide negatives (2026-07-31)

## Method

Extends the calibration described in `README.md` to a held-out slice of `data/labels/fluorescent-spot-examples.csv` that wasn't part of the original 8-positive calibration set.

1. **Positives**: rows 9-13 of the labels CSV (1-indexed by `csv.DictReader` order, header excluded) — 5 rows, each a distinct slide, all tagged `Overexposed`:
   - `LB-D3-2025-10-03-125352-2402169466D-thin-2-1` fov 3
   - `LB-D3-2025-10-22-131729-250917745-D-thin-2-3` fov 134
   - `LB-D3-2025-10-25-150947-250917467-D-thin-3-2` fov 235
   - `RUB-62501389` fov 284 (Tanzania)
   - `RUB-72501756` fov 315 (Tanzania)
2. **Negatives**: for each of those 5 slides, 2 FOVs chosen uniformly at random from the slide's full grid, excluding any FOV already in the labels CSV for that slide (10 negatives total). Same informal-negative-control approach as the README's original calibration, just applied to a different slide set.
3. **Fetch**: everything pulled directly from GCS into memory (`cv2.imdecode` on bytes from `download_as_bytes()`/`download_as_text()`) and scored with `detect_overexposure()`. Nothing written to `data/raw/` — no local FOV caching at any point.
4. The combined 15-FOV sample (5 positive + 10 negative) was shuffled (`random.seed(20260731)`) before scoring; order below reflects that shuffle.

**Tanzania resolution note**: `src/gcs_fov.py` only resolves `LB-*` sample IDs (Liberia). The two Tanzania samples live in a separate bucket, `gs://tanzania_02032026`, under `TZ2025-Box<N>/<sample_id>/`, with a much flatter convention than Liberia's row/col raster: `fluorescent-<fov_id zero-padded to 3 digits>-<sample_id>.png`, `fov_id` 1..324 directly (both slides are 18x18=324-FOV grids, `Quantity=324` in `metadata/fluorescent-scan.txt`). Boxes were found by listing the bucket: `RUB-62501389` → Box2, `RUB-72501756` → Box3. This mapping is not yet in `src/gcs_fov.py` — see Recommendations.

## Summary table

| Slide | FOV | Truth | Result | Contrast ratio |
|---|---|---|---|---|
| RUB-72501756 | 91 | Negative | Negative | 1.41 |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 134 | Positive | Positive | 3.85 |
| RUB-62501389 | 310 | Negative | Negative | 1.32 |
| LB-D3-2025-10-03-125352-2402169466D-thin-2-1 | 134 | Negative | Negative | 1.45 |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 70 | Positive* | Positive | 8.28 |
| RUB-62501389 | 284 | Positive | Positive | 6.85 |
| LB-D3-2025-10-25-150947-250917467-D-thin-3-2 | 233 | Negative | Negative | 2.18 |
| LB-D3-2025-10-25-150947-250917467-D-thin-3-2 | 235 | Positive | Positive | 4.10 |
| LB-D3-2025-10-03-125352-2402169466D-thin-2-1 | 3 | Positive | Positive | 5.50 |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 84 | Negative | Negative | 2.33 |
| RUB-72501756 | 315 | Positive | Positive | 4.23 |
| LB-D3-2025-10-25-150947-250917467-D-thin-3-2 | 307 | Negative | Negative | 1.71 |
| RUB-72501756 | 46 | Negative | Negative | 1.35 |
| LB-D3-2025-10-03-125352-2402169466D-thin-2-1 | 9 | Negative | Negative | 2.52 |
| RUB-62501389 | 125 | Negative | Negative | 1.29 |

*fov 70's truth was originally recorded as `Negative` (random draw from the informal negative-control set); reclassified to `Positive` after the preview confirmed a genuine halo — see below.

Full data (incl. baseline/peak/area_fraction/solidity) in `extended-test-fov9-13-073126.csv`. A plain slide/fov/truth/result table (this table plus the addendum row below, with fov 70's truth corrected) is in `summary-table-073126.csv`.

### Addendum: fov 62 (flagged difficult case)

| Slide | FOV | Truth | Result | Contrast ratio |
|---|---|---|---|---|
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 62 | Positive | **Negative** | 2.41 |

Added on request as a known-positive "difficult case" from the same slide as the fov 70 mislabeled-negative above. This one is a **genuine false negative**: the preview (`data/results/preview/fov62_check__preview.png`) shows a soft, diffuse glow across the upper third of the frame — the low-contrast end of the artifact spectrum the README describes ("ranging from a soft diffuse glow to a sharply saturated disc") — well below the sharp-disc cases the detector catches confidently. Ratio 2.41 sits just under `RATIO_THRESHOLD=3.0`, in the gap the README's calibration table describes as "clean" based on only 8+8 examples; this case shows that gap isn't universally clean once genuinely faint halos are included.

### Addendum: fov 35 (untested, no CSV label)

| Slide | FOV | Truth | Result | Contrast ratio |
|---|---|---|---|---|
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 35 | Negative† | Positive | 3.75 |

†Not in the labels CSV; truth assigned here from a visual read of the preview (`data/results/preview/fov35_check__preview.png`), not confirmed by an annotator — flag for review if that matters for how this row gets used.

The preview shows a bright, thin, curved streak (reads like a hair or fiber across the slide) plus a small bright fleck near the top border — **not** the round/diffuse overexposure halo the detector is designed for. Solidity is 0.79, notably lower than every confirmed halo case in this batch (0.94-0.998), consistent with an elongated artifact rather than the halo's coherent round shape. Ratio 3.75 still clears `RATIO_THRESHOLD=3.0` because the streak is bright enough to survive the heavy blur. This looks like a **genuine false positive** — a different artifact type (contaminant fiber, not illumination halo) that the ratio-only decision rule doesn't distinguish from the real target. The `area_fraction`/`solidity` fields are computed for exactly this kind of QC but aren't currently used as a hard gate (per README's own calibration notes) — this case is a concrete argument for reconsidering that.

Confirmed by the annotator: fov 35's ground truth is `Negative`.

### Addendum: fovs 31-34 (same slide, confirmed-negative row) — the fiber spans multiple tiles

| Slide | FOV | Truth | Result | Contrast ratio | Solidity |
|---|---|---|---|---|---|
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 31 | Negative | Negative | 2.18 | 0.81 |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 32 | Negative | **Positive** | 3.93 | 1.00 |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 33 | Negative | Negative | 2.28 | 0.77 |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 34 | Negative | **Positive** | 4.00 | 0.99 |

FOVs 31-35 are five adjacent tiles in the same raster row (columns 13-17, row 2). Previews for fov 32 and fov 34 (`data/results/preview/fov32_check__preview.png`, `fov34_check__preview.png`) show the *same* bright fiber/hair, just crossing into different tiles — it's one physical contaminant lying across the slide, wide enough to clip the corner of several neighboring FOVs. Where it grazes a corner lightly (fov 31, fov 33) the ratio stays under threshold; where more of it falls in-frame (fov 32, fov 34, fov 35) the ratio clears 3.0, all with solidity ~0.99-1.00 (a straight/curved fiber segment can look just as convex as a round halo when only a *segment* of it dominates one tile — solidity alone doesn't reliably separate the two once the artifact is nearly linear within the frame; fov 35's lower solidity, 0.79, came from having *two* separate bright components in-frame at once, not from the fiber's shape itself).

This is now 3 confirmed false positives from a single physical cause: a fiber contaminant that the detector's low-pass/ratio logic — tuned to distinguish a round illumination halo from small scattered puncta — has no mechanism for telling apart from the real target once it's bright and large enough in one tile.

## FP/FN analysis

- **False negatives: 0/5 (0%)** on the original CSV-labeled positives — every labeled `Overexposed` FOV was caught, with contrast ratios (3.85-6.85) comfortably above `RATIO_THRESHOLD=3.0`.
- **False positives: 0/9 (0%)** among the random negative-control draws, after reclassifying fov 70.

**fov 70 was initially flagged as a false positive (ratio 8.28) but its ground truth was wrong, not the detector.** A preview render (`data/results/preview/fov70_fp_check__preview.png`) shows a sharply-bordered, frame-clipped bright disc — textbook halo artifact per the README's own description, visually indistinguishable from the confirmed positives. The negative-control methodology assumes an unlabeled FOV is a true negative, but the labels CSV was never an exhaustive per-FOV review — annotators tagged FOVs they happened to flag, not every FOV on every slide. Truth has been corrected to `Positive` in both CSVs; with that correction the detector's call (`Positive`) is right. Same caveat the README already flags for the original 8 informal negatives ("informal ... just a sanity check").

Net read across the 16-FOV core set (5 CSV positives + 9 confirmed negatives + fov 70 reclassified as a 6th positive + fov 62 as a 7th positive/difficult case): **0 false positives, 1 false negative (fov 62)**.

Adding fov 35 (confirmed Negative) plus fovs 31-34 (confirmed Negative) brings the running total to **3 false positives (fovs 32, 34, 35), 1 false negative (fov 62)** out of 21 — and unlike fov 70, these mismatches look like a real detector limitation, not a labeling gap: one physical fiber/hair contaminant, bright enough in 3 of its 5 spanned tiles to clear the ratio threshold, that the detector's round-halo-vs-puncta logic has no way to distinguish from the real target.

## Recommendations

1. **Spot-check informal negatives before trusting an FP rate.** Any random draw that lands on an actual unflagged halo will look like a false positive until someone looks at the image — as happened here. A quick preview render (`save_preview`) of every disagreement should be routine before reporting FP/FN numbers from unlabeled negative sampling.
2. **Extend `src/gcs_fov.py` (or add a sibling resolver) to cover Tanzania (`RUB-*`) sample IDs** using the `tanzania_02032026` bucket convention documented above, since this data source will keep coming up as the labels CSV grows past Liberia-only rows. Worth also confirming whether Uganda (`PBC-*`, row 14, not tested here) uses the same or yet another convention before it's needed.
3. This batch is still small (5 positives, 10 negatives, +1 flagged difficult case); it corroborates the existing `RATIO_THRESHOLD=3.0` calibration but doesn't materially change the confidence interval on it. The README's "Future directions" point about fitting the threshold on a larger, *properly* labeled negative set still stands.
4. **Faint/diffuse halos (fov 62) are a real edge case the ratio threshold isn't tuned for.** All 5 rows-9-13 positives and both fov-70/fov-284-style strong halos score well clear of the 3.0 cutoff; fov 62 (ratio 2.41) shows the detector's margin shrinks a lot for soft, low-contrast glows. Worth deliberately sourcing more low-contrast positive examples (not just sharp-disc ones) before trusting `RATIO_THRESHOLD` near its boundary.
5. **Bright linear contaminants (fibers/hairs) are a confirmed, non-hypothetical false-positive class.** Fovs 32/34/35 show the same physical fiber fooling the detector 3 separate times just from this one slide. Since it can span multiple adjacent FOVs, one contaminant costs multiple false triage flags. A shape check beyond solidity alone (e.g. elongation/aspect-ratio of the largest component, since solidity was ~0.99 for these too) is worth adding as a second gate specifically to rule out this failure mode, distinct from the puncta-vs-halo problem the ratio was designed to solve.
