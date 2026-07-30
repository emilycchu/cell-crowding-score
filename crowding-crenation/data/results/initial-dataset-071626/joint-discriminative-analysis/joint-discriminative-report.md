# Joint discriminative power — initial dataset (13 FOVs)

For every pair of techniques, fits a 2-feature linear regression against the manual density+overlap severity score (integer range 0-7) and compares its R² to the better of the two techniques alone. This tests whether combining features captures more of the labeled severity signal than either captures individually — complementary to `pairwise-analysis/pairwise-report.md`, which only checks how much techniques overlap with *each other*, not with the label.

n = 13 FOVs and each joint model has 2 predictors, so adjusted R² is reported alongside raw joint R² to correct for the extra free parameter — with this few points, raw R² alone would overstate any pair's joint fit.

## Solo R² vs. severity

- Edge density: R² = 0.655
- LBP entropy: R² = 0.613
- GLCM contrast: R² = 0.490
- Otsu coverage: R² = 0.133

## Pairwise joint R²

| Pair | R²(A) solo | R²(B) solo | R² joint | adj. R² joint | gain over best solo |
|---|---|---|---|---|---|
| Otsu coverage + LBP entropy | 0.133 | 0.613 | 0.745 | 0.694 | +0.132 |
| Edge density + LBP entropy | 0.655 | 0.613 | 0.731 | 0.678 | +0.077 |
| Edge density + GLCM contrast | 0.655 | 0.490 | 0.717 | 0.660 | +0.062 |
| GLCM contrast + LBP entropy | 0.490 | 0.613 | 0.672 | 0.606 | +0.059 |
| Otsu coverage + Edge density | 0.133 | 0.655 | 0.706 | 0.648 | +0.051 |
| Otsu coverage + GLCM contrast | 0.133 | 0.490 | 0.521 | 0.426 | +0.031 |

## Interpretation

**Most complementary pair: Otsu coverage + LBP entropy** (gain=+0.132, joint R²=0.745 vs. best solo R²=0.613). The two features separate severity better together than either alone by a wide margin, which fits the pairwise-overlap finding that this pair shares very little variance with each other -- they're picking up different aspects of severity.

**Least complementary pair: Otsu coverage + GLCM contrast** (gain=+0.031, joint R²=0.521 vs. best solo R²=0.490). Adding the second feature buys almost nothing here.

Pairs with a large gain (>= 0.10), i.e. genuinely complementary:

- Otsu coverage + LBP entropy (gain=+0.132)

Pairs with a small gain (< 0.04), i.e. one feature adds little over the other:

- Otsu coverage + GLCM contrast (gain=+0.031)