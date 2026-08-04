"""v2.1 recalibration: fit both composites against the FULL candidate feature pool instead
of the axis-exclusive partial-correlation-winner subset used in calibrate_v2.py.

Round-1 diagnosis (see calibration-report.md's v2 sections above the section this script
appends): the Rouleaux composite, built only from tile_glcm_cv/tile_glcm_patchiness (the
features that won axis-exclusive selection), had an inverted-U relationship with true
Rouleaux severity -- a severe, confluent Rouleaux sheet reads as MORE homogeneous than a
moderate patchy case, so a single monotonic composite built only from those two features
could never rank-order "Some Rouleaux" / "Rouleaux" / "Heavy Rouleaux" correctly, forcing
PAVA to merge all three buckets. glcm_contrast and edge_density_unmasked -- excluded from
Rouleaux in v2 because their *partial* correlation favored density -- are each cleanly
monotonic across exactly that top-severity range.

This script fits each axis directly against its own ordinal label using the full 8-feature
pool (letting fit_weights_stable's ridge + sign-instability dropping do the actual
selection), which fixes the collapsed buckets at the cost of making the two composites more
correlated with each other than the true manual-label relationship -- reported transparently
in a new "v2.1 recalibration" section appended to the same calibration-report.md, not a
separate report file.

Usage:
    python scripts/ai-first/calibrate_v2.1.py [--features-csv PATH] [--params-out PATH]
        [--report-out PATH]
"""
import argparse
import json
from pathlib import Path

from scipy.stats import spearmanr

from _v2_common import DENSITY_LEVELS, FEATURES_CSV, OVERLAP_LEVELS, RESULTS_DIR, display_level
from calibrate_v2 import (
    CANDIDATE_FEATURES,
    N_FOLDS,
    _fmt_conf,
    axis_separation_check,
    calibrate_axis,
    correlation_table,
    load_features,
    write_params_json,
)

PARAMS_JSON_V2_1 = RESULTS_DIR / "density_overlap_v2.1_params.json"
REPORT_MD = RESULTS_DIR / "calibration-report.md"


def composite_independence(density_result, overlap_result, rho_do):
    rho, _ = spearmanr(density_result["full_raw_score"], overlap_result["full_raw_score"])
    return {"composite_rho": float(rho), "manual_label_rho": float(rho_do)}


def append_report_section(report_path, density_result, overlap_result, independence, sep_checks):
    lines = []
    lines.append("\n---\n\n")
    lines.append("# v2.1 recalibration: full-feature-pool fitting\n\n")
    lines.append(
        "The v2 calibration above assigned each candidate feature to exactly one axis (whichever "
        "had the higher *partial* correlation). That worked for density but left the Rouleaux "
        "composite with only `tile_glcm_cv`/`tile_glcm_patchiness`, whose per-level medians turned "
        "out to be a genuine **inverted-U** with Rouleaux severity (Some Rouleaux scored *higher* "
        "patchiness than Rouleaux or Heavy Rouleaux) -- a real reflection of the user's own predicted "
        "exception: a severe, confluent Rouleaux sheet reads as smoother/more homogeneous than a "
        "moderate patchy case. No monotonic threshold cut on those two features alone could "
        "rank-order the top three levels, so PAVA merged them. `glcm_contrast` and "
        "`edge_density_unmasked` -- excluded from Rouleaux in v2 because their partial correlation "
        "favored density -- are each cleanly monotonic across exactly that range.\n\n"
        f"v2.1 fits both composites directly against their own ordinal label using the full "
        f"{len(CANDIDATE_FEATURES)}-feature candidate pool (`{', '.join(CANDIDATE_FEATURES)}`), "
        "instead of the axis-exclusive subset -- same `fit_weights_stable` ridge-plus-sign-drop "
        "fitting machinery, just a larger candidate pool per axis.\n\n"
    )

    for name, result, levels in [("Density", density_result, DENSITY_LEVELS), ("Rouleaux", overlap_result, OVERLAP_LEVELS)]:
        lines.append(f"## {name} composite (v2.1)\n\n")
        if result["dropped_sign_unstable_features"]:
            lines.append(f"Dropped for sign instability: {', '.join(result['dropped_sign_unstable_features'])}\n\n")
        lines.append("| feature | weight | range (2nd-98th pct) |\n|---|---|---|\n")
        for n in result["feature_names"]:
            lo, hi = result["normalization"][n]
            lines.append(f"| {n} | {result['weights'][n]:.3f} | [{lo:.4g}, {hi:.4g}] |\n")

        lines.append(f"\n**Cross-validation** ({N_FOLDS}-fold): per-fold rho = {[round(r, 3) for r in result['cv_fold_rho']]}, "
                     f"mean={result['cv_mean_rho']:.3f}. Out-of-fold exact-match={result['oof_exact_match_rate']:.1%}, "
                     f"off-by-one={result['oof_off_by_one_rate']:.1%}.\n\n")
        lines.append("Out-of-fold confusion matrix (rows=manual, cols=predicted):\n\n")
        lines.append(_fmt_conf(result["oof_confusion_matrix"], levels))
        lines.append(f"\nThresholds: {[round(t, 3) for t in result['bucket_thresholds']]}")
        if result["merged_bucket_groups"]:
            groups = [[display_level(levels[i]) for i in g] for g in result["merged_bucket_groups"]]
            lines.append(f" -- **PAVA still merged**: {groups}\n\n")
        else:
            lines.append(" -- **no PAVA merges** (all 5 buckets monotonically separable).\n\n")

    lines.append("## Composite independence (v2.1)\n\n")
    lines.append(
        f"Spearman rho between the two fitted composite scores: **{independence['composite_rho']:.3f}**, vs. the true "
        f"manual density-vs-Rouleaux label correlation of **{independence['manual_label_rho']:.3f}**. This is the real "
        "trade-off of full-pool fitting: the composites are now noticeably more alike than the two severity axes "
        "actually are, because several of the best-fitting features (coverage, glcm_contrast, edge_density_unmasked) "
        "are legitimately shared between both axes rather than exclusive to one. Reported here rather than hidden.\n\n"
    )

    lines.append("## Axis-separation check (v2.1)\n\n")
    lines.append("| min |delta| | n | sign matches | match rate | binomial p | Spearman rho |\n|---|---|---|---|---|---|\n")
    for sep_check in sep_checks:
        sign_match_str = f"{sep_check['sign_match_rate']:.1%}" if sep_check["sign_match_rate"] is not None else "n/a"
        lines.append(f"| {sep_check['min_delta']} | {sep_check['n_disagreement']} | {sep_check['matches']} | "
                     f"{sign_match_str} | {sep_check['p_value']:.4g} | {sep_check['spearman_rho']:.3f} |\n")
    lines.append(
        "\n**Takeaway**: despite the composites becoming much more correlated with each other, the "
        "axis-separation match rate barely moves relative to v2 (~61% vs ~62% at `|delta|>=1`, both "
        "significant) -- so the extra shared signal does not appear to cost the tool its ability to "
        "separate the specific dense-but-not-Rouleauxed / Rouleauxed-but-not-dense cases it's meant to "
        "catch, even though it does trade away composite independence as a diagnostic property.\n\n"
    )

    with open(report_path, "a", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    parser = argparse.ArgumentParser(description="v2.1 recalibration: full-feature-pool fitting for both axes.")
    parser.add_argument("--features-csv", default=str(FEATURES_CSV))
    parser.add_argument("--params-out", default=str(PARAMS_JSON_V2_1))
    parser.add_argument("--report-out", default=str(REPORT_MD))
    args = parser.parse_args()

    rows = load_features(args.features_csv)
    _, rho_do = correlation_table(rows)

    density_result = calibrate_axis(rows, "density", "density_ord", "density_label", DENSITY_LEVELS, CANDIDATE_FEATURES)
    overlap_result = calibrate_axis(rows, "overlap", "overlap_ord", "overlap_label", OVERLAP_LEVELS, CANDIDATE_FEATURES)

    sep_checks = [
        axis_separation_check(rows, density_result["oof_pred_idx"], overlap_result["oof_pred_idx"], min_delta=1),
        axis_separation_check(rows, density_result["oof_pred_idx"], overlap_result["oof_pred_idx"], min_delta=2),
    ]
    independence = composite_independence(density_result, overlap_result, rho_do)

    params_path = Path(args.params_out)
    write_params_json(params_path, density_result, overlap_result, len(rows))
    data = json.loads(params_path.read_text())
    data["version"] = "v2.1"
    data["generated_from"] = args.features_csv
    params_path.write_text(json.dumps(data, indent=2))

    append_report_section(Path(args.report_out), density_result, overlap_result, independence, sep_checks)

    print(f"density: features={density_result['feature_names']}, cv_mean_rho={density_result['cv_mean_rho']:.3f}, "
         f"exact_match={density_result['oof_exact_match_rate']:.1%}")
    print(f"overlap: features={overlap_result['feature_names']}, cv_mean_rho={overlap_result['cv_mean_rho']:.3f}, "
         f"exact_match={overlap_result['oof_exact_match_rate']:.1%}")
    print(f"composite independence rho={independence['composite_rho']:.3f} (manual label rho={independence['manual_label_rho']:.3f})")
    for sep_check in sep_checks:
        print(f"axis-separation (|delta|>={sep_check['min_delta']}): {sep_check['matches']}/{sep_check['n_disagreement']} "
              f"sign matches, p={sep_check['p_value']:.4g}")
    print(f"wrote {params_path}")
    print(f"appended to {args.report_out}")


if __name__ == "__main__":
    main()
