# Pairwise technique correlations — initial dataset (13 FOVs)

Companion to `report.md` (per-technique vs. manual severity label). This looks at how
the four techniques correlate **with each other**, to flag redundancy for composite-score
weighting.

Axis choice (which technique is x vs y) does not affect `r`, `r²`, or `ρ` — these are
symmetric statistics. It only affects which variable the overlaid regression line treats
as the predictor, so the correlation-strength conclusions below hold regardless of plot
orientation.

## Pairwise correlation matrix

| Pair | r | r² | ρ |
|---|---|---|---|
| Edge density (unmasked) vs GLCM contrast | 0.956 | 0.914 | 0.945 |
| Edge density (unmasked) vs LBP entropy | 0.736 | 0.542 | 0.588 |
| GLCM contrast vs LBP entropy | 0.661 | 0.437 | 0.560 |
| Otsu coverage vs GLCM contrast | 0.278 | 0.078 | 0.264 |
| Otsu coverage vs Edge density (unmasked) | 0.174 | 0.030 | 0.209 |
| Otsu coverage vs LBP entropy | 0.002 | 0.000 | 0.176 |

For reference, each technique's correlation with the manual density+overlap severity label
(from `report.md`): Otsu coverage r=0.36 (weak), edge density unmasked r=0.81 (strong),
GLCM contrast r=0.70 (strong), LBP entropy r=0.78 (strong). Edge density *masked* r=-0.21
(weak) is excluded here since the pipeline uses the unmasked variant.

## Findings

**Edge density (unmasked) and GLCM contrast are near-duplicates.** r²=0.91 — they share
91% of their variance on this dataset. Both are independently strong predictors of the
severity label (r=0.81 and r=0.70), which is exactly what you'd expect from two textures/
edge-roughness measures responding to the same underlying image statistic. Weighting both
at 0.2 each effectively gives ~0.4 combined weight to one signal, double-counting it
relative to the other two features.

**LBP entropy is a partial repeat of both, not a full one.** It shares 44-54% of variance
with edge density and GLCM contrast (r²=0.44-0.54) — correlated, but retains meaningfully
more independent information than the edge-density/GLCM pair does with each other.

**Otsu coverage is essentially orthogonal to the other three** (r²=0.00-0.08) — it isn't
a repeat of anything. But it's also the weakest individual predictor of severity (r=0.36),
and it currently carries the *largest* composite weight (0.4 in `FeatureWeights`), while
edge density/GLCM/LBP entropy — the three strong predictors — split the remaining 0.6.

## Composite-score implications

Current weights (`src/composite.py`): `coverage=0.4, edge_density=0.2, glcm_contrast=0.2,
lbp_entropy=0.2`. Two things stand out as worth fixing when the weights get tuned against
labels (per the README's open item):

1. **Collapse or down-weight the edge-density/GLCM pair.** Since they're near-duplicates,
   keeping both at full weight amounts to over-weighting one signal. Either drop GLCM
   contrast (edge density has the higher standalone label correlation *and* is cheaper to
   compute — no gray-level co-occurrence matrix), or fold both into one feature (e.g.
   their average) before weighting, rather than treating them as two independent votes.
2. **Otsu coverage's 0.4 weight looks too high given this data** — it's the weakest
   single predictor of severity, so giving it the largest share of the composite pulls the
   score toward its noisiest input. This is directional, not a fitted result; actual
   weights should come from regressing the composite against the manual labels (as the
   README's "tune composite score weights" item calls for), not from pairwise correlation
   alone — pairwise correlation tells you what's redundant, not what's optimal.

None of the four techniques are exact repeats of each other, so there's no case for
dropping one outright — but edge density and GLCM contrast are close enough (r²=0.91)
that carrying both at independent weight is the main redundancy worth correcting.
