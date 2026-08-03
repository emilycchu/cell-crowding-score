"""Turn raw per-FOV metrics (scripts/score_new_slide.py) into the 5-level density
and crowding/rouleaux ordinal scales, plus a crenation/unusual-cell flag.

Density and crowding thresholds are quintiles of THIS slide's own observed
coverage_fraction / rouleaux_fraction distributions, not universal cutoffs — with
only one slide to calibrate against, slide-relative quintiles is the only
defensible way to spread the labels across the scale. Re-running on a second
slide should re-derive thresholds rather than reuse these.
"""
import argparse
import csv
from pathlib import Path

import numpy as np

DENSITY_LABELS = ["sparse", "monolayer", "slightly dense", "dense", "very dense"]
CROWDING_LABELS = ["no rouleaux", "slight rouleaux", "some rouleaux", "rouleaux", "heavy rouleaux"]

CRENATION_FLAG_THRESHOLD = 0.05   # fraction of isolated cells below the solidity cutoff
CRENATION_MIN_ISOLATED = 100      # below this, flag as "insufficient isolated cells" instead


def quintile_label(value, edges, labels):
    for edge, label in zip(edges, labels):
        if value < edge:
            return label
    return labels[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scores_csv", type=Path)
    parser.add_argument("out_csv", type=Path)
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.scores_csv)))
    coverage = np.array([float(r["coverage_fraction"]) for r in rows])
    rouleaux = np.array([float(r["rouleaux_fraction"]) for r in rows])

    coverage_edges = np.percentile(coverage, [20, 40, 60, 80])
    rouleaux_edges = np.percentile(rouleaux, [20, 40, 60, 80])
    print(f"density (coverage_fraction) quintile edges: {coverage_edges}")
    print(f"crowding (rouleaux_fraction) quintile edges: {rouleaux_edges}")

    out_rows = []
    for r in rows:
        cov = float(r["coverage_fraction"])
        roul = float(r["rouleaux_fraction"])
        cren_frac = float(r["crenation_fraction"])
        n_isolated = int(r["n_isolated"])

        density_label = quintile_label(cov, coverage_edges, DENSITY_LABELS)
        crowding_label = quintile_label(roul, rouleaux_edges, CROWDING_LABELS)

        if n_isolated < CRENATION_MIN_ISOLATED:
            crenation_flag = "insufficient_data"
        elif cren_frac >= CRENATION_FLAG_THRESHOLD:
            crenation_flag = "flagged"
        else:
            crenation_flag = "normal"

        out_rows.append({
            "idx": r["idx"],
            "density_label": density_label,
            "crowding_label": crowding_label,
            "crenation_flag": crenation_flag,
            "coverage_fraction": cov,
            "rouleaux_fraction": roul,
            "crenation_fraction": cren_frac,
            "n_cells": r["n_cells"],
            "n_isolated": n_isolated,
        })

    fieldnames = list(out_rows[0].keys())
    with open(args.out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"wrote {len(out_rows)} rows to {args.out_csv}")
    print("density label counts:", {l: sum(1 for r in out_rows if r["density_label"] == l) for l in DENSITY_LABELS})
    print("crowding label counts:", {l: sum(1 for r in out_rows if r["crowding_label"] == l) for l in CROWDING_LABELS})
    print("crenation flag counts:", {
        k: sum(1 for r in out_rows if r["crenation_flag"] == k)
        for k in ("flagged", "normal", "insufficient_data")
    })


if __name__ == "__main__":
    main()
