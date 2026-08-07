"""Build confusion matrices and FN/FP tallies from run_overexposed_diverse_test.py's
results.csv, for both the diffuse-fov-step-not-folded-in and folded-in variants, each split
into the "all", "background", "diffuse", and "double" subsets (by the labels CSV's `notes`
column).

Ground truth: spot_truth (yes/no, from the annotator's "spot" column -- whether the
overexposed-halo artifact itself is genuinely present). Prediction: predicted_spot_base /
predicted_spot_folded, which are just `present`/`present_folded` directly (see
run_overexposed_diverse_test.py's docstring). A false negative here means the pipeline missed
a real halo (e.g. a faint/diffuse one below RATIO_THRESHOLD); a false positive means it fired
on an ordinary FOV that only looked overexposed (elevated background, debris, etc.).

Usage:
    python scripts/analyze_overexposed_diverse.py data/results/overexposed-diverse-080726/results.csv
"""
import argparse
import csv
from pathlib import Path

SUBSETS = ["all", "background", "diffuse", "double"]
VARIANTS = [("base", "predicted_spot_base"), ("folded", "predicted_spot_folded")]


def confusion(rows, pred_key):
    tp = fn = fp = tn = 0
    for r in rows:
        truth_yes = r["spot_truth"] == "yes"
        pred_yes = r[pred_key].strip().lower() == "true"
        if truth_yes and pred_yes:
            tp += 1
        elif truth_yes and not pred_yes:
            fn += 1
        elif not truth_yes and pred_yes:
            fp += 1
        else:
            tn += 1
    return {"tp": tp, "fn": fn, "fp": fp, "tn": tn, "n": len(rows)}


def subset_rows(rows, subset):
    if subset == "all":
        return [r for r in rows if "error" not in r or not r["error"]]
    return [r for r in rows if r.get("notes", "") == subset and ("error" not in r or not r["error"])]


def format_matrix(stats, label):
    n = stats["n"]
    if n == 0:
        return f"**{label}** (n=0) -- no rows in this subset\n"
    lines = [f"**{label}** (n={n})", "", "| | Predicted: spot | Predicted: no spot |", "|---|---|---|"]
    lines.append(f"| Truth: spot | TP={stats['tp']} | FN={stats['fn']} |")
    lines.append(f"| Truth: no spot | FP={stats['fp']} | TN={stats['tn']} |")
    fn_rate = stats["fn"] / (stats["tp"] + stats["fn"]) if (stats["tp"] + stats["fn"]) else float("nan")
    fp_rate = stats["fp"] / (stats["fp"] + stats["tn"]) if (stats["fp"] + stats["tn"]) else float("nan")
    lines.append("")
    lines.append(f"FN rate: {stats['fn']}/{stats['tp'] + stats['fn']}"
                 f" ({fn_rate:.1%})" if (stats["tp"] + stats["fn"]) else "FN rate: n/a (no spot-positive rows)")
    lines.append(f"FP rate: {stats['fp']}/{stats['fp'] + stats['tn']}"
                 f" ({fp_rate:.1%})" if (stats["fp"] + stats["tn"]) else "FP rate: n/a (no spot-negative rows)")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_csv", type=Path)
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.results_csv)))

    for variant_label, pred_key in VARIANTS:
        heading = "Diffuse-fov step NOT folded in (baseline `present`)" if variant_label == "base" \
            else "Diffuse-fov step folded in (`present_folded`)"
        print(f"\n## {heading}\n")
        for subset in SUBSETS:
            sub_rows = subset_rows(rows, subset)
            stats = confusion(sub_rows, pred_key)
            print(format_matrix(stats, subset))


if __name__ == "__main__":
    main()
