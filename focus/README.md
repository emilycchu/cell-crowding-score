# Focus Score (exploratory)

A first pass at scoring how in-focus a thin-smear FOV is, computed **per quadrant** (not
just once for the whole image) so that partial-focus FOVs -- e.g. the bottom half slightly
soft while the rest is sharp -- show up as a difference between quadrants rather than
averaging out.

This is deliberately exploratory: several candidate metrics are computed side by side
instead of committing to one, and the annotator's own `focus_level` labels
(`data/labels/focus-spot-examples-080426.csv`) are carried through the output only as a
passive reference column -- nothing here uses them to threshold or calibrate anything.

## Method

`src/focus_metrics.py::score_fov` splits the image into a 2x2 grid (`tl`/`tr`/`bl`/`br`) and
computes, on the whole image and each quadrant:

| Metric | What it measures |
|---|---|
| `laplacian_variance` | Variance of the Laplacian -- the standard no-reference blur metric. |
| `tenengrad` | Mean squared Sobel gradient magnitude -- a second gradient-energy metric. |
| `fft_high_freq_ratio` | Fraction of 2D FFT power at/above 25% of Nyquist radius -- frequency-domain view of the same question. |
| `edge_width` | Median (local contrast / gradient magnitude) across Canny edge pixels, in pixels -- how wide the intensity transition is *across* real edges, specifically targeting blur rather than generic high-frequency energy. |
| `coverage_fraction` | Fraction of pixels above an Otsu threshold (same foreground convention as `crowding-crenation/src/segmentation.py`) -- context only, not a focus measure: an empty/background-heavy quadrant will score low on every sharpness metric for a reason that has nothing to do with focus. |

Each metric also gets a `*_quadrant_range` (max - min across the 4 quadrants), as a simple
non-uniformity flag for FOVs whose focus isn't consistent across the frame.

## Findings from this pass

**Mild blur doesn't cleanly track the `unfocused` label across sites, but severe blur
does.** The first 15-FOV round only had mildly-annotated LB `unfocused` examples, and those
didn't separate from TZ/UG `focused` examples on any metric -- every LB FOV scored a *higher*
Laplacian variance (203–339) than every TZ FOV labeled `focused` (56–112) and most UG FOVs
too. Viewing the images directly explains why: the TZ/UG `focused` examples show crisp,
well-separated RBC discs, while the LB examples show a denser, mottled, grainy texture with
less distinct cell boundaries -- visually softer, but that fine-grained texture still
generates plenty of raw high-frequency energy, which a generic variance-of-high-pass metric
can't tell apart from true edge sharpness. This tracked with something closer to a
site/staining/instrument difference between LB and TZ/UG than with focus itself.

A second round added 5 more LB FOVs, including the first 3 labeled `completely unfocused`
(a new, more severe label than plain `unfocused`) plus one more `unfocused` example. **These
finally separate cleanly from everything else on every energy-based metric**, LB included:

| Group | n | whole-image `laplacian_variance` |
|---|---|---|
| `completely unfocused` (all LB) | 3 | 35 – 39 |
| `unfocused`, FOV 88 (LB) | 1 | 41 |
| everything else (LB `unfocused`, TZ, UG) | 16 | 56 – 339 |

So the metric *does* track real focus loss -- it just needs the blur to be severe enough to
overcome the LB/TZ/UG site-level texture gap, and the same whole-image cutoff (~56 on
`laplacian_variance`, ~1445 on `tenengrad`) separates severe from mild blur *within* LB too,
not just LB-vs-elsewhere -- 8 other LB FOVs labeled plain `unfocused` score well above it.
Three further things showed up only at this severity level:
- **`edge_width` going undefined is a real signal, but an inconsistent one.** Only 2 of the 4
  severely-blurred FOVs (`...-D-Only-1-3` FOV 8, `...-D-thin-1-3` FOV 100) trigger it (fewer
  than 20 Canny edge pixels detected anywhere in the frame); the other 2 (`...-D-Only-1-1`
  FOV 48, FOV 88) still report a numeric `edge_width` indistinguishable from the mild-blur LB
  group. Treat it as a bonus flag when it fires, not a primary detector.
- **`fft_high_freq_ratio` does *not* extend to the frequency domain the way it looks like it
  should.** It's conceptually the same "how much fine detail is left" question as the other
  two energy metrics, but the 4 severely-blurred FOVs score 0.106-0.508 on it -- spanning
  nearly the entire dataset's range instead of clustering low like `laplacian_variance`/
  `tenengrad` do. Don't use it as a severe-blur filter.
- **`coverage_fraction` becomes unstable, not just low**, on severely blurred FOVs: per-quadrant
  values swing between ~0 and ~1 with no spatial pattern (e.g. FOV 88's quadrants are 0.005,
  0.99, 0.004, 1.00). Otsu assumes a bimodal brightness histogram, and severe blur flattens
  the image enough that the histogram loses that structure -- so the threshold lands almost
  arbitrarily. Don't trust `coverage_fraction` on FOVs already flagged as severely blurred by
  the other metrics.

**Practical implication: don't compare the raw whole-image metrics across sites/slides for
mild blur** -- the *within-FOV* quadrant-to-quadrant range remains the more trustworthy
signal for that case, since it's relative within one image rather than absolute across
different scanners/staining batches. The two largest `laplacian_variance__quadrant_range`
values in the whole dataset are `DPSP-1070-AS-1` FOV 219 (UG, labeled `focused`; range 181,
top-left 264 vs. bottom-right 83) and `PBC-603-1` FOV 62 (UG, labeled `focused`; range 160,
top-left 307 vs. bottom-right 147) -- real, visually-confirmable within-FOV sharpness
gradients, exactly the kind of case quadrant scoring is meant to catch. The caveat: both are
labeled overall-`focused`, so quadrant range answers "is this FOV spatially uniform," not
"is this FOV in focus" -- it's a complementary gate, not a standalone classifier.

Only 1 of the 19 sampled slides so far has more than one labeled FOV
(`LB-D3-2025-10-24-144750-250232728-D-thin-4-1`, FOV 1 and FOV 22, both `unfocused`), and its
two FOVs land in the same mild-`unfocused` band as each other (`laplacian_variance` 281 and
326) -- consistent with blur being a slide-level property, but one repeated slide isn't
enough to confirm that generalizes.

None of this is a working detector yet. See `data/results/focus-080426/summary.md` for the
full per-quadrant breakdown of every FOV scored so far, including a "Conclusions" section
that derives the severe-blur cutoff and mild-blur site-overlap numbers directly from the data
(`focus-scores.csv` has the raw numbers, `previews/` has the annotated images), and
`scripts/summarize_focus.py` to regenerate it after adding more labeled FOVs.

## Usage

```bash
pip install -r requirements.txt
gcloud auth application-default login   # once, for GCS access to all three buckets

# Fetch the labeled reference FOVs from GCS (cached under data/raw/focus-spot/, gitignored;
# already-cached FOVs are skipped, so this is safe to rerun after adding new labeled rows)
python scripts/fetch_reference_images.py data/labels/focus-spot-examples-080426.csv

# Compute quadrant + whole-image focus metrics for each -> data/results/focus-080426/focus-scores.csv
python scripts/score_focus.py data/labels/focus-spot-examples-080426.csv data/results/focus-080426/focus-scores.csv

# Render a quadrant-grid preview per FOV with metrics annotated -> data/results/focus-080426/previews/
python scripts/visualize_focus.py data/labels/focus-spot-examples-080426.csv data/results/focus-080426/previews

# Render the human-readable per-quadrant markdown summary -> data/results/focus-080426/summary.md
python scripts/summarize_focus.py data/results/focus-080426/focus-scores.csv data/results/focus-080426/summary.md
```

## GCS bucket layout

All three buckets store FOVs the same way: a per-slide folder containing
`dpc-<fov_id:03d>-<slide-folder-name>.png` (grayscale, `uint8`, 2800x2800):

- **LB** (`gs://liberia-2025`): `processedData4SS/LB25-<batch>/<folder>/` -- folder name
  doesn't match `sample_id` exactly (punctuation varies by slide), so it's located by its
  unique `<date>-<time>-<numeric_id>` substring, the same technique
  `fluorescence/src/gcs_fov.py` uses for the raw `_Blue` fluorescence folder (just a
  different tree, and no channel-suffix filter).
- **TZ** (`gs://tanzania_02032026`): `TZ2025-Box<1-5>/<sample_id>/` -- which box holds a
  given sample isn't derivable from the ID, so each of the 5 boxes is checked in turn.
- **UG** (`gs://malaria-annotation-web`): `samples/<sample_id>/data/` -- direct, no lookup.

`src/gcs_fov.py` resolves all three. It reuses `fluorescence/src/gcs_fov.py::parse_sample_id`
(a pure sample-ID regex parser) via a direct file-path import, rather than re-deriving that
regex -- but it does *not* import `crowding-crenation/src/pipeline.py`'s near-identical
`GCSPath`/`load_image` helper, even though it does the same job: that module's relative
imports pull in its whole composite/features/segmentation stack (and scipy/skimage) to reach
one small function, and every sibling project (including this one) names its package `src`,
which collides in Python's module cache if more than one gets imported by path into the same
process. The download+decode step is reimplemented locally instead (~10 lines).

## Repository layout

```
src/
  gcs_fov.py        sample_id/fov_id/country -> gs:// DPC image resolution across LB/TZ/UG
  focus_metrics.py  quadrant split + the 5 candidate metrics + score_fov() aggregator
scripts/
  fetch_reference_images.py   download labeled FOVs from GCS into data/raw/focus-spot/ (gitignored)
  score_focus.py               batch-score cached FOVs -> data/results/focus-080426/focus-scores.csv
  visualize_focus.py            per-FOV quadrant-grid preview PNGs -> data/results/focus-080426/previews/
  summarize_focus.py            focus-scores.csv -> human-readable data/results/focus-080426/summary.md
data/
  labels/   focus-spot-examples-080426.csv (gitignored -- contains real patient sample IDs)
  raw/      downloaded FOV images (gitignored)
  results/  focus-080426/ -- score CSV, markdown summary, preview images
```

## Future directions

- **Investigate the LB-vs-TZ/UG gap directly** rather than just working around it -- is it
  staining, a different scan resolution/optics, or something else? That would clarify
  whether cross-site comparison can be rescued (e.g. per-site normalization) or should be
  abandoned in favor of purely relative, within-slide scoring, at least for mild blur (severe
  blur already separates cleanly -- see Findings above).
- **A metric that's actually blur-specific, not texture-general, for the mild-blur case.**
  `edge_width` was a first attempt but didn't cleanly separate the mildly-`unfocused` LB
  group from TZ/UG either (see `focus-scores.csv`) -- possibly because its raw-pixel units
  are just as confounded by site/staining scale as the energy-based metrics. It does go
  usefully undefined on some of the most severe cases, though not all of them consistently
  (see Findings). `fft_high_freq_ratio` looked like a promising second frequency-domain
  candidate but turned out to be unreliable even at the severe-blur end, so it's currently the
  weakest of the five metrics rather than a lead worth pursuing further as-is. A
  calibrated/normalized version of `edge_width`, or a metric built from the known physical RBC
  diameter at this resolution, is worth trying next for the mild-blur gap specifically.
- **Get more labeled negatives, ideally within a single site/slide, at the mild-blur end.**
  Every plain `unfocused` example so far is LB and almost every `focused`/`unsure` example is
  TZ/UG -- label and country are almost perfectly confounded for mild blur, which is exactly
  what makes that gap impossible to disentangle from real focus differences using this data
  alone. `completely unfocused` finally broke the confound because it's severe enough to
  dominate the site-level gap, not because the confound was resolved. Relatedly, only one
  slide in the current data has more than one labeled FOV -- more repeats per slide would turn
  the "blur looks like a slide-level property" observation from a single data point into
  something testable.
- **A coverage_fraction fallback for severely blurred FOVs**, since Otsu becomes unreliable
  right where it would otherwise be useful for flagging "this quadrant is just background."
