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
5. **Bright linear contaminants (fibers/hairs) are a confirmed, non-hypothetical false-positive class.** Fovs 32/34/35 show the same physical fiber fooling the detector 3 separate times just from this one slide. Since it can span multiple adjacent FOVs, one contaminant costs multiple false triage flags. A shape check beyond solidity alone (e.g. elongation/aspect-ratio of the largest component, since solidity was ~0.99 for these too) is worth adding as a second gate specifically to rule out this failure mode, distinct from the puncta-vs-halo problem the ratio was designed to solve. **Addressed 2026-08-04 — see Update below.**

## Update (2026-08-04): FFT-anisotropy check, tested against fovs 31-35

`src/overexposure.py` now runs a second-stage check on top of the ratio gate, specifically to
catch the fiber/hair false positives flagged in Recommendation 5 above.

### How it works

Recommendation 5 suggested a shape check beyond solidity, but the fiber contaminant in
fovs 31-35 defeats shape metrics on the halo mask's *outline*: once a hair curves through the
frame or only a segment of it dominates one tile, its outline blob-ifies enough to look about
as convex as a real (often corner-clipped) halo (solidity ~0.99-1.00 for both, see fovs 32/34
above). Increasing the blur kernel doesn't separate them either — a point punctum's peak
collapses as ~1/sigma^2 under 2D blur (it spreads over an area), but a line only spreads
perpendicular to itself, so its peak falls off as ~1/sigma, much closer to how a real halo
survives blur. No kernel size opens a clean gap between "hair" and "halo" on outline shape or
blur decay alone.

What does separate them is the orientation of the *pixel-intensity texture inside* the
candidate region, not its outline: a halo's brightness falls off smoothly in every direction
(an isotropic 2D FFT power spectrum), while a hair or fiber concentrates energy along one
orientation no matter how it curves (an anisotropic spectrum). `_fft_anisotropy()` computes
this directly — window the candidate region (padded 15% around its bounding box) with a 2D
Hann window, take the FFT power spectrum, and measure how concentrated that power is around
one orientation using the circular-statistics resultant-vector trick for an axial (mod π, not
mod 2π) quantity: sum `power * exp(2i*angle)` over an annulus that excludes the DC bin, then
take `|sum| / sum(power)`. That ratio is ~0 for isotropic power (halo) and → 1 for power
concentrated on one axis (fiber).

This check only runs on candidates that already pass `RATIO_THRESHOLD` — it doesn't need to
separate real halos from ordinary negatives (whose mask outlines are noise, not real
structure, and score unreliably on this metric), only halos from fiber debris that already
cleared the ratio gate. If `anisotropy > ANISOTROPY_THRESHOLD (0.35)`, the candidate is
demoted back to `present=False, confidence=0.0`.

### Test: fovs 31-35 re-scored with the updated detector

Same 5 adjacent FOVs from `LB-D3-2025-10-22-131729-250917745-D-thin-2-3` flagged in the
"fiber spans multiple tiles" addendum above, re-run through the current `detect_overexposure()`
(ratio gate + anisotropy check together, not staged separately in the code — "pre-anisotropy"
below just replays the ratio-only decision for comparison):

| Slide | FOV | Truth | Result (ratio only) | Result (current) | Contrast ratio | Anisotropy |
|---|---|---|---|---|---|---|
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 31 | Negative | Negative | Negative | 2.18 | — (below ratio gate, not evaluated) |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 32 | Negative | **Positive** | Negative | 3.93 | 0.421 |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 33 | Negative | Negative | Negative | 2.28 | — (below ratio gate, not evaluated) |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 34 | Negative | **Positive** | Negative | 4.00 | 0.765 |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 35 | Negative | **Positive** | Negative | 3.75 | 0.571 |

All 3 fiber-driven false positives (32, 34, 35) are now correctly demoted to `Negative`, with
anisotropy (0.421-0.765) sitting well clear of the 0.35 threshold. Fovs 31 and 33 were already
correctly negative on the ratio alone (the fiber only grazes their corner) — anisotropy is
never evaluated for them since they don't clear the ratio gate.

### Test: true positives (regression check)

The concern with adding a second gate is demoting real halos, not just catching fake ones. Re-ran
the current detector against the 8 original calibration positives (`data/labels/fluorescent-spot-examples.csv`
rows 1-8) plus fov 70 from the same slide as the fiber cases (a strong, unambiguous halo,
reclassified `Positive` earlier in this document):

| Slide | FOV | Truth | Result | Contrast ratio | Anisotropy |
|---|---|---|---|---|---|
| LB-D10-2025-12-30-083614-0250901VFPCHC-2-1 | 210 | Positive | Positive | 17.35 | 0.141 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 125 | Positive | Positive | 13.23 | 0.315 |
| LB-D10-2025-12-30-083614-0250901VFPCHC-2-1 | 227 | Positive | Positive | 11.45 | 0.099 |
| LB-D3-2025-10-22-131729-250917745-D-thin-2-3 | 70 | Positive | Positive | 8.28 | 0.140 |
| LB-D10-2025-12-30-084453-0250071VFPCHC-2-2 | 200 | Positive | Positive | 7.95 | 0.131 |
| LB-D3-2025-10-03-104211-250917371-D-thin-2-3 | 4 | Positive | Positive | 5.86 | 0.144 |
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 153 | Positive | Positive | 6.36 | 0.121 |
| LB-D3-2025-10-03-124025-2404175445D-thin-2-3 | 114 | Positive | Positive | 3.78 | 0.072 |
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 154 | Positive | Positive | 3.65 | 0.097 |

All 9 stay `Positive` — anisotropy ranges 0.072-0.315 for every real halo tested, clear of the
0.35 threshold, none demoted. **Caveat**: this is not an independent hold-out — these are the
same 9 real-halo examples (8 original calibration positives + fov 70) the `overexposure.py`
module docstring already cites as the anisotropy calibration set (alongside fovs 32/34/35 as
the hair-debris side). This confirms the check does what it was tuned to do; it isn't new
evidence the threshold generalizes beyond this slide set.

Fov 62 (the known faint-halo false negative flagged earlier in this document) is unaffected by
this change, as expected: its contrast ratio (2.41) never clears `RATIO_THRESHOLD`, so the
anisotropy check — which only runs on ratio-gate survivors — never executes for it. It remains
`present=False`. That's a separate, still-open gap (see Recommendation 4 above), not something
this update was meant to touch.

Full data (incl. baseline/peak/solidity, and the ratio-only vs. current result for every row) in
`anisotropy-update-test-080426.csv`. Previews with the updated (now green, i.e. `Negative`)
contours for fovs 32/34/35 are in `data/results/preview_new/`.

### Updated FP/FN tally

Substituting these results into the running tally from the "fiber spans multiple tiles" section
above: of the 21 FOVs tracked across this document (5 CSV positives + 9 confirmed negatives +
fov 70 + fov 62 + fov 35 + fovs 31-34), false positives drop from **3 (fovs 32, 34, 35) to 0**;
the one false negative (fov 62) is unchanged and still open.
