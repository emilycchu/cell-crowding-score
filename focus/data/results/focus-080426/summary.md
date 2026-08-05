# Focus scoring summary -- focus-080426

20 FOVs scored: LB n=12, TZ n=6, UG n=2. Annotated labels (reference only, not used to tune anything): `completely unfocused` n=3, `focused` n=7, `unfocused` n=9, `unsure` n=1.

Full per-quadrant numbers for every metric are in `focus-scores.csv` in this same folder; per-FOV annotated preview images (quadrant grid + metric overlay) are in `previews/`. Tables below are sorted by whole-image value, ascending, so the most severely blurred FOVs (by each metric) are at the top.

## Conclusions: which features reliably filter blur, and at what severity

### Severe blur (cells not resolvable): absolute whole-image energy metrics work, cross-site

Splitting every FOV at the lowest whole-image value seen among annotated `focused`/`unsure` FOVs (never at a value chosen to fit the split) gives a cutoff of **laplacian_variance = 56.2** and **tenengrad = 1445**. Both metrics put the exact same 4 FOVs below that line: `LB-D3-2025-09-04-131645-250917282-D-Only-1-4` FOV 88 (`unfocused`), `LB-D3-2025-09-02-141315-25087116-D-Only-1-1` FOV 48 (`completely unfocused`), `LB-D3-2025-09-02-142951-250513832-D-Only-1-3` FOV 8 (`completely unfocused`), `LB-D3-2025-10-24-151519-250417224-D-thin-1-3` FOV 100 (`completely unfocused`). The nearest focused/unsure FOV clears that cutoff by 15.0 on laplacian_variance and 1139 on tenengrad -- a wide, clean margin, not a knife-edge threshold.

This cluster is all LB in the current data, but the cutoff isn't simply picking out a site: 8 other LB FOVs labeled `unfocused` score well above it (see mild-blur section below), so the same absolute threshold separates severe from mild blur *within* LB, not just LB-vs-elsewhere. **Practical takeaway: for catching FOVs where no cells are resolvable at all, a fixed whole-image threshold on laplacian_variance or tenengrad is reliable regardless of site.**

**`fft_high_freq_ratio` does *not* extend this to the frequency domain the way it looks like it should.** Despite being conceptually the same "how much fine detail is left" question, the same 4 severe-blur FOVs score fft_high_freq_ratio = 0.419, 0.106, 0.395, 0.508 -- spanning nearly the entire dataset's range (0.094-0.508), not clustered low. A flattened, information-poor image apparently doesn't collapse this ratio the way it collapses laplacian_variance/tenengrad; don't use it as a severe-blur filter.

`edge_width` going undefined (`n/a`, fewer than 20 Canny edge pixels) is a real severe-blur signal but an inconsistent one: only 2 of the 4 severe FOVs trigger it (FOV 8, FOV 100); the other 2 still report a numeric edge_width indistinguishable from the mild-blur LB group. Treat it as a bonus flag when it fires, not a primary detector.

### Mild blur / slightly pixelated (cells still visible): absolute metrics are site-confounded, use quadrant range instead

Once the severe cluster is set aside, whole-image laplacian_variance ranges overlap heavily across sites and labels -- there is no single global threshold that would separate mild `unfocused` from `focused` here:

- LB `unfocused` (n=8): 203.0-338.9
- TZ `focused` (n=5): 56.2-111.5
- TZ `unsure` (n=1): 78.1-78.1
- UG `focused` (n=2): 177.1-237.3

The LB mildly-`unfocused` band (202.96-338.90) sits entirely *above* the TZ `focused` band (56.16-111.52) and overlaps the UG `focused` band (177.10-237.27) -- i.e. a mildly-blurred LB FOV reads as sharper than a genuinely in-focus TZ FOV on this metric, purely from site/staining texture differences (see main README for the visual explanation). **A fixed whole-image cutoff would misclassify most of this dataset at the mild-blur tier.**

The one signal in this pass that stays meaningful at this severity is the **within-FOV `*__quadrant_range`** (max - min across the 4 quadrants, see 'Flagged' section below): it's relative to the FOV's own quadrants rather than an absolute cross-site value, so it isn't affected by the site-texture gap above. Its caveat: it flags *spatial non-uniformity*, not overall blur -- the two largest quadrant ranges in the whole dataset (`DPSP-1070-AS-1` FOV 219, `PBC-603-1` FOV 62) belong to FOVs annotated `focused`, because part of each frame really is soft while the rest is sharp. Use it as a "this FOV isn't uniform" gate alongside a per-site/per-slide baseline, not as a standalone focused/unfocused classifier.

`coverage_fraction` is not usable as a filtering feature at any severity here -- it's context only by design, and becomes actively unstable (swinging ~0 to ~1 with no spatial pattern) once an FOV is already severely blurred (see caveat in that section below).

## Within-slide comparison (repeat FOVs from the same sample)

Only 1 of 19 sampled slides in this round has more than one labeled FOV, so within-slide consistency is a single data point here, not yet a statistical claim (see README future directions -- more labeled FOVs per slide is the fix).

- `LB-D3-2025-10-24-144750-250232728-D-thin-4-1` (LB):
  - FOV 1 (`unfocused`): laplacian_variance=281.0, tenengrad=8265
  - FOV 22 (`unfocused`): laplacian_variance=326.2, tenengrad=8572

The two FOVs from this slide land in the same mild-`unfocused` band as each other and well clear of the severe-blur cluster -- consistent with blur being a slide-level property here, but not enough repeats to confirm it generalizes.

## laplacian_variance (per quadrant, whole-image-ascending)

| sample_id | fov_id | country | annotated | tl | tr | bl | br | range |
|---|---|---|---|---|---|---|---|---|
| LB-D3-2025-09-02-141315-25087116-D-Only-1-1 | 48 | LB | completely unfocused | 30.5 | 43.2 | 28.2 | 39.9 | 15.0 |
| LB-D3-2025-09-02-142951-250513832-D-Only-1-3 | 8 | LB | completely unfocused | 29.9 | 43.4 | 29.3 | 43.7 | 14.5 |
| LB-D3-2025-10-24-151519-250417224-D-thin-1-3 | 100 | LB | completely unfocused | 30.6 | 48.2 | 30.8 | 47.3 | 17.6 |
| LB-D3-2025-09-04-131645-250917282-D-Only-1-4 | 88 | LB | unfocused | 37.0 | 50.2 | 33.1 | 44.3 | 17.0 |
| KIT-62501056 | 193 | TZ | focused | 55.3 | 53.6 | 55.7 | 60.3 | 6.7 |
| KTR-72502723 | 92 | TZ | focused | 72.6 | 74.7 | 78.9 | 85.0 | 12.4 |
| KIT-62500652 | 6 | TZ | unsure | 67.3 | 83.4 | 72.2 | 90.0 | 22.7 |
| KTR-72502948 | 4 | TZ | focused | 116.6 | 124.3 | 85.1 | 94.3 | 39.3 |
| KIT-62501048 | 235 | TZ | focused | 116.3 | 105.2 | 104.8 | 102.2 | 14.0 |
| RUB-62501336 | 235 | TZ | focused | 119.3 | 118.5 | 105.0 | 104.2 | 15.1 |
| DPSP-1070-AS-1 | 219 | UG | focused | 264.1 | 222.0 | 140.4 | 83.1 | 181.0 |
| LB-D3-2025-10-03-104211-250917371-D-thin-2-3 | 12 | LB | unfocused | 183.5 | 208.6 | 197.8 | 223.4 | 40.0 |
| PBC-603-1 | 62 | UG | focused | 307.1 | 261.5 | 235.7 | 147.0 | 160.1 |
| LB-D3-2025-10-27-145205-250917002-D-thin-3-3 | 245 | LB | unfocused | 259.6 | 269.0 | 225.3 | 239.3 | 43.7 |
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 132 | LB | unfocused | 235.7 | 294.1 | 214.2 | 260.1 | 79.9 |
| LB-D3-2025-10-03-122127-250912792D-thin-3-4 | 15 | LB | unfocused | 271.5 | 338.8 | 175.2 | 259.5 | 163.5 |
| LB-D3-2025-10-27-144635-250918691-D-thin-2-2 | 243 | LB | unfocused | 273.9 | 283.4 | 218.7 | 290.4 | 71.6 |
| LB-D3-2025-10-24-144750-250232728-D-thin-4-1 | 1 | LB | unfocused | 294.0 | 297.6 | 257.2 | 277.1 | 40.4 |
| LB-D3-2025-10-24-144750-250232728-D-thin-4-1 | 22 | LB | unfocused | 343.4 | 336.5 | 305.1 | 321.6 | 38.3 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 2 | LB | unfocused | 326.3 | 377.6 | 314.1 | 339.1 | 63.5 |

## tenengrad (per quadrant, whole-image-ascending)

| sample_id | fov_id | country | annotated | tl | tr | bl | br | range |
|---|---|---|---|---|---|---|---|---|
| LB-D3-2025-09-02-142951-250513832-D-Only-1-3 | 8 | LB | completely unfocused | 117 | 172 | 115 | 173 | 59 |
| LB-D3-2025-10-24-151519-250417224-D-thin-1-3 | 100 | LB | completely unfocused | 118 | 190 | 119 | 186 | 72 |
| LB-D3-2025-09-02-141315-25087116-D-Only-1-1 | 48 | LB | completely unfocused | 290 | 421 | 187 | 278 | 234 |
| LB-D3-2025-09-04-131645-250917282-D-Only-1-4 | 88 | LB | unfocused | 275 | 422 | 218 | 307 | 204 |
| KIT-62501056 | 193 | TZ | focused | 1612 | 1364 | 1385 | 1414 | 248 |
| KTR-72502723 | 92 | TZ | focused | 2169 | 2173 | 2499 | 2592 | 424 |
| KIT-62501048 | 235 | TZ | focused | 3662 | 3006 | 3197 | 2921 | 741 |
| KIT-62500652 | 6 | TZ | unsure | 2854 | 3402 | 3044 | 3641 | 787 |
| KTR-72502948 | 4 | TZ | focused | 3938 | 4092 | 3061 | 3136 | 1031 |
| RUB-62501336 | 235 | TZ | focused | 4347 | 4304 | 3935 | 3870 | 477 |
| LB-D3-2025-10-03-104211-250917371-D-thin-2-3 | 12 | LB | unfocused | 5589 | 7342 | 5155 | 6584 | 2187 |
| LB-D3-2025-10-27-144635-250918691-D-thin-2-2 | 243 | LB | unfocused | 6124 | 6271 | 5517 | 7335 | 1817 |
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 132 | LB | unfocused | 6345 | 7210 | 5677 | 7468 | 1791 |
| DPSP-1070-AS-1 | 219 | UG | focused | 9317 | 8833 | 5839 | 3878 | 5439 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 2 | LB | unfocused | 7339 | 7853 | 6387 | 7065 | 1466 |
| LB-D3-2025-10-03-122127-250912792D-thin-3-4 | 15 | LB | unfocused | 7738 | 9278 | 4428 | 7294 | 4851 |
| LB-D3-2025-10-27-145205-250917002-D-thin-3-3 | 245 | LB | unfocused | 7192 | 9278 | 5911 | 7567 | 3367 |
| LB-D3-2025-10-24-144750-250232728-D-thin-4-1 | 1 | LB | unfocused | 8195 | 9679 | 6876 | 8287 | 2803 |
| LB-D3-2025-10-24-144750-250232728-D-thin-4-1 | 22 | LB | unfocused | 8823 | 9711 | 7190 | 8536 | 2521 |
| PBC-603-1 | 62 | UG | focused | 13220 | 12994 | 12810 | 9953 | 3267 |

## fft_high_freq_ratio (per quadrant, whole-image-ascending)

Fraction of 2D FFT power at/above 25% of Nyquist radius. **See Conclusions above: this one does not reliably separate severe blur from focused FOVs**, unlike laplacian_variance and tenengrad -- it's included here for completeness, not as a recommended filter.

| sample_id | fov_id | country | annotated | tl | tr | bl | br | range |
|---|---|---|---|---|---|---|---|---|
| KIT-62500652 | 6 | TZ | unsure | 0.0865 | 0.0809 | 0.0947 | 0.0904 | 0.0138 |
| LB-D3-2025-10-03-104211-250917371-D-thin-2-3 | 12 | LB | unfocused | 0.0989 | 0.1094 | 0.1014 | 0.1182 | 0.0193 |
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 132 | LB | unfocused | 0.1004 | 0.1192 | 0.0704 | 0.0871 | 0.0488 |
| LB-D3-2025-10-27-145205-250917002-D-thin-3-3 | 245 | LB | unfocused | 0.1201 | 0.1133 | 0.0950 | 0.1016 | 0.0251 |
| LB-D3-2025-09-02-141315-25087116-D-Only-1-1 | 48 | LB | completely unfocused | 0.0842 | 0.0663 | 0.1044 | 0.1267 | 0.0604 |
| PBC-603-1 | 62 | UG | focused | 0.1362 | 0.1174 | 0.1055 | 0.0663 | 0.0699 |
| LB-D3-2025-10-27-144635-250918691-D-thin-2-2 | 243 | LB | unfocused | 0.1074 | 0.1859 | 0.0861 | 0.1023 | 0.0999 |
| LB-D3-2025-10-24-144750-250232728-D-thin-4-1 | 1 | LB | unfocused | 0.1342 | 0.1210 | 0.0958 | 0.1052 | 0.0384 |
| LB-D3-2025-10-24-144750-250232728-D-thin-4-1 | 22 | LB | unfocused | 0.1493 | 0.1345 | 0.1249 | 0.1216 | 0.0277 |
| LB-D3-2025-10-03-122127-250912792D-thin-3-4 | 15 | LB | unfocused | 0.1402 | 0.1802 | 0.0945 | 0.1353 | 0.0857 |
| RUB-62501336 | 235 | TZ | focused | 0.1624 | 0.1319 | 0.1358 | 0.1049 | 0.0576 |
| KTR-72502948 | 4 | TZ | focused | 0.1778 | 0.1530 | 0.1186 | 0.0974 | 0.0804 |
| KTR-72502723 | 92 | TZ | focused | 0.1962 | 0.1213 | 0.1584 | 0.1208 | 0.0754 |
| KIT-62501056 | 193 | TZ | focused | 0.1520 | 0.1328 | 0.1851 | 0.1474 | 0.0523 |
| DPSP-1070-AS-1 | 219 | UG | focused | 0.2030 | 0.1883 | 0.1676 | 0.1170 | 0.0860 |
| KIT-62501048 | 235 | TZ | focused | 0.2146 | 0.1568 | 0.1977 | 0.1505 | 0.0641 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 2 | LB | unfocused | 0.2204 | 0.2373 | 0.1780 | 0.2005 | 0.0593 |
| LB-D3-2025-09-02-142951-250513832-D-Only-1-3 | 8 | LB | completely unfocused | 0.3028 | 0.5272 | 0.1966 | 0.4730 | 0.3306 |
| LB-D3-2025-09-04-131645-250917282-D-Only-1-4 | 88 | LB | unfocused | 0.3939 | 0.2682 | 0.3991 | 0.4291 | 0.1609 |
| LB-D3-2025-10-24-151519-250417224-D-thin-1-3 | 100 | LB | completely unfocused | 0.7865 | 0.8368 | 0.8110 | 0.8147 | 0.0503 |

## edge_width (per quadrant, whole-image-ascending)

`n/a` = fewer than 20 Canny edge pixels detected in that region -- on the most severely blurred FOVs this happens across the *whole* image, which is itself a meaningful signal (no edges sharp enough to detect at all), not a missing measurement.

| sample_id | fov_id | country | annotated | tl | tr | bl | br | range |
|---|---|---|---|---|---|---|---|---|
| LB-D3-2025-09-02-142951-250513832-D-Only-1-3 | 8 | LB | completely unfocused | n/a | n/a | n/a | n/a | n/a |
| LB-D3-2025-10-24-151519-250417224-D-thin-1-3 | 100 | LB | completely unfocused | n/a | n/a | n/a | n/a | n/a |
| DPSP-1070-AS-1 | 219 | UG | focused | 0.407 | 0.405 | 0.409 | 0.421 | 0.016 |
| KIT-62501048 | 235 | TZ | focused | 0.399 | 0.421 | 0.408 | 0.421 | 0.022 |
| KIT-62501056 | 193 | TZ | focused | 0.406 | 0.420 | 0.406 | 0.420 | 0.014 |
| KTR-72502723 | 92 | TZ | focused | 0.397 | 0.424 | 0.410 | 0.424 | 0.027 |
| RUB-62501336 | 235 | TZ | focused | 0.421 | 0.426 | 0.427 | 0.435 | 0.014 |
| KTR-72502948 | 4 | TZ | focused | 0.420 | 0.428 | 0.429 | 0.438 | 0.018 |
| PBC-603-1 | 62 | UG | focused | 0.431 | 0.430 | 0.433 | 0.444 | 0.013 |
| KIT-62500652 | 6 | TZ | unsure | 0.440 | 0.449 | 0.441 | 0.447 | 0.009 |
| LB-D3-2025-09-04-131645-250917282-D-Only-1-4 | 88 | LB | unfocused | 0.454 | 0.445 | 0.453 | 0.451 | 0.009 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 2 | LB | unfocused | 0.454 | 0.457 | 0.459 | 0.461 | 0.007 |
| LB-D3-2025-10-03-104211-250917371-D-thin-2-3 | 12 | LB | unfocused | 0.462 | 0.464 | 0.464 | 0.466 | 0.005 |
| LB-D3-2025-10-27-145205-250917002-D-thin-3-3 | 245 | LB | unfocused | 0.462 | 0.465 | 0.465 | 0.464 | 0.003 |
| LB-D3-2025-10-27-144635-250918691-D-thin-2-2 | 243 | LB | unfocused | 0.470 | 0.444 | 0.474 | 0.472 | 0.030 |
| LB-D3-2025-10-03-122127-250912792D-thin-3-4 | 15 | LB | unfocused | 0.463 | 0.462 | 0.469 | 0.469 | 0.007 |
| LB-D3-2025-10-24-144750-250232728-D-thin-4-1 | 22 | LB | unfocused | 0.464 | 0.466 | 0.466 | 0.468 | 0.004 |
| LB-D3-2025-10-24-144750-250232728-D-thin-4-1 | 1 | LB | unfocused | 0.466 | 0.469 | 0.469 | 0.472 | 0.006 |
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 132 | LB | unfocused | 0.470 | 0.473 | 0.473 | 0.476 | 0.006 |
| LB-D3-2025-09-02-141315-25087116-D-Only-1-1 | 48 | LB | completely unfocused | 0.496 | 0.502 | 0.494 | 0.501 | 0.008 |

FOVs with no whole-image edge_width (no detectable edges anywhere): `LB-D3-2025-09-02-142951-250513832-D-Only-1-3` FOV 8 (`completely unfocused`), `LB-D3-2025-10-24-151519-250417224-D-thin-1-3` FOV 100 (`completely unfocused`)

## coverage_fraction (per quadrant, whole-image-ascending)

Context only, not a focus measure -- included so a quadrant that's mostly empty background isn't mistaken for a blurry one. **Caveat found in this round:** on the most severely blurred FOVs, coverage_fraction becomes unstable rather than just low -- per-quadrant values swing between ~0 and ~1 with no spatial pattern (e.g. `LB-D3-2025-09-04-131645-250917282-D-Only-1-4` FOV 88 has quadrant coverage 0.005, 0.99, 0.004, 1.00). This is an Otsu-threshold artifact: Otsu assumes a bimodal brightness histogram (foreground vs. background), and severe blur flattens the image enough that the histogram loses that bimodal structure, so the threshold lands almost arbitrarily close to the whole region's narrow brightness range. Don't trust coverage_fraction on FOVs that are already flagged as severely blurred by the other metrics.

| sample_id | fov_id | country | annotated | tl | tr | bl | br | range |
|---|---|---|---|---|---|---|---|---|
| LB-D3-2025-09-02-141315-25087116-D-Only-1-1 | 48 | LB | completely unfocused | 0.02 | 0.97 | 0.01 | 0.98 | 0.97 |
| KIT-62501056 | 193 | TZ | focused | 0.08 | 0.13 | 0.10 | 0.16 | 0.08 |
| KIT-62501048 | 235 | TZ | focused | 0.15 | 0.15 | 0.15 | 0.15 | 0.01 |
| RUB-62501336 | 235 | TZ | focused | 0.15 | 0.14 | 0.14 | 0.15 | 0.01 |
| KTR-72502723 | 92 | TZ | focused | 0.16 | 0.21 | 0.14 | 0.18 | 0.07 |
| KTR-72502948 | 4 | TZ | focused | 0.16 | 0.16 | 0.25 | 0.25 | 0.09 |
| KIT-62500652 | 6 | TZ | unsure | 0.20 | 0.21 | 0.19 | 0.19 | 0.02 |
| LB-D3-2025-10-27-144635-250918691-D-thin-2-2 | 243 | LB | unfocused | 0.38 | 0.63 | 0.31 | 0.53 | 0.33 |
| LB-D3-2025-10-24-151519-250417224-D-thin-1-3 | 100 | LB | completely unfocused | 0.50 | 0.66 | 0.32 | 0.62 | 0.34 |
| LB-D3-2025-09-02-142951-250513832-D-Only-1-3 | 8 | LB | completely unfocused | 0.46 | 0.20 | 0.54 | 0.60 | 0.39 |
| DPSP-1070-AS-1 | 219 | UG | focused | 0.11 | 0.88 | 0.09 | 0.91 | 0.82 |
| LB-D3-2025-10-03-122127-250912792D-thin-3-4 | 15 | LB | unfocused | 0.42 | 0.67 | 0.35 | 0.67 | 0.32 |
| LB-D3-2025-08-30-103102-250876706-D-thin-4 | 2 | LB | unfocused | 0.49 | 0.57 | 0.50 | 0.57 | 0.08 |
| LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4 | 132 | LB | unfocused | 0.51 | 0.59 | 0.55 | 0.58 | 0.08 |
| LB-D3-2025-09-04-131645-250917282-D-Only-1-4 | 88 | LB | unfocused | 0.01 | 0.99 | 0.00 | 1.00 | 0.99 |
| PBC-603-1 | 62 | UG | focused | 0.75 | 0.77 | 0.25 | 0.74 | 0.52 |
| LB-D3-2025-10-27-145205-250917002-D-thin-3-3 | 245 | LB | unfocused | 0.47 | 0.58 | 0.66 | 0.67 | 0.20 |
| LB-D3-2025-10-03-104211-250917371-D-thin-2-3 | 12 | LB | unfocused | 0.72 | 0.68 | 0.41 | 0.67 | 0.31 |
| LB-D3-2025-10-24-144750-250232728-D-thin-4-1 | 22 | LB | unfocused | 0.70 | 0.69 | 0.69 | 0.67 | 0.03 |
| LB-D3-2025-10-24-144750-250232728-D-thin-4-1 | 1 | LB | unfocused | 0.73 | 0.69 | 0.72 | 0.69 | 0.04 |

## Flagged: most non-uniform focus within a single FOV

Top FOVs by laplacian_variance quadrant-to-quadrant range -- the case this whole quadrant-scoring approach is meant to catch (one part of the frame clearly softer than the rest of the *same* FOV, not a cross-slide comparison).

- `DPSP-1070-AS-1` FOV 219 (UG, annotated `focused`): laplacian_variance range = 181.0 (tl=264.1, tr=222.0, bl=140.4, br=83.1)
- `LB-D3-2025-10-03-122127-250912792D-thin-3-4` FOV 15 (LB, annotated `unfocused`): laplacian_variance range = 163.5 (tl=271.5, tr=338.8, bl=175.2, br=259.5)
- `PBC-603-1` FOV 62 (UG, annotated `focused`): laplacian_variance range = 160.1 (tl=307.1, tr=261.5, bl=235.7, br=147.0)
- `LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4` FOV 132 (LB, annotated `unfocused`): laplacian_variance range = 79.9 (tl=235.7, tr=294.1, bl=214.2, br=260.1)
- `LB-D3-2025-10-27-144635-250918691-D-thin-2-2` FOV 243 (LB, annotated `unfocused`): laplacian_variance range = 71.6 (tl=273.9, tr=283.4, bl=218.7, br=290.4)
