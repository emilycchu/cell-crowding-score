"""Generate a findings report comparing each image-processing technique against a
combined ordinal severity score (density rank + overlap rank), with one scatter
plot per technique and outliers flagged via linear-fit residuals.

Usage:
    python scripts/generate_report.py
"""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATASET = "initial-dataset-071626"
LABELS_DIR = Path(f"data/labels/{DATASET}")
RESULTS_DIR = Path(f"data/results/{DATASET}")
PLOTS_DIR = RESULTS_DIR / "plots"

DENSITY_ORDER = ["monolayer", "slightly dense", "dense", "very dense"]
OVERLAP_ORDER = ["no rouleaux", "slight rouleaux", "some rouleaux", "rouleaux", "heavy rouleaux"]

# name, csv file, column, unit ("%" or "")
TECHNIQUES = [
    ("Otsu coverage", "otsu.csv", "coverage_pct", "%"),
    ("Edge density (with mask)", "edge-density.csv", "edge_density_masked_pct", "%"),
    ("Edge density (without mask)", "edge-density.csv", "edge_density_unmasked_pct", "%"),
    ("GLCM contrast", "glcm-contrast.csv", "glcm_contrast", ""),
    ("LBP entropy", "lbp-entropy.csv", "lbp_entropy", ""),
]

OUTLIER_Z = 1.5

# dataviz reference palette (references/palette.md)
COLOR_POINT = "#2a78d6"
COLOR_OUTLIER = "#d03b3b"
COLOR_TREND = "#2a78d6"
COLOR_GRID = "#e1e0d9"
COLOR_AXIS = "#c3c2b7"
COLOR_MUTED = "#898781"
COLOR_PRIMARY = "#0b0b0b"
COLOR_SECONDARY = "#52514e"
COLOR_SURFACE = "#fcfcfb"


def load_fovs():
    with open(LABELS_DIR / "fovs.csv", newline="") as f:
        return list(csv.DictReader(f))


def load_metric_csv(filename):
    with open(RESULTS_DIR / filename, newline="") as f:
        return {row["filename"]: row for row in csv.DictReader(f)}


def combined_score(row):
    return DENSITY_ORDER.index(row["density"]) + OVERLAP_ORDER.index(row["overlap"])


def jittered_x(records):
    """Deterministic horizontal jitter so FOVs sharing a combined score don't overlap."""
    by_score = {}
    for rec in records:
        by_score.setdefault(rec["combined_score"], []).append(rec)
    for score, group in by_score.items():
        group.sort(key=lambda r: int(r["fov"]))
        n = len(group)
        offsets = np.linspace(-0.15, 0.15, n) if n > 1 else [0.0]
        for rec, offset in zip(group, offsets):
            rec["x"] = score + offset


def find_outliers(records):
    x = np.array([r["combined_score"] for r in records], dtype=float)
    y = np.array([r["value"] for r in records], dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    predicted = slope * x + intercept
    residuals = y - predicted
    std = residuals.std(ddof=1)
    for rec, resid in zip(records, residuals):
        rec["residual"] = resid
        rec["is_outlier"] = std > 0 and abs(resid) > OUTLIER_Z * std
    r = np.corrcoef(x, y)[0, 1]
    return slope, intercept, std, r


def plot_technique(name, unit, records, slope, intercept, corr, out_path):
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    xs = np.array([0, 7])
    ax.plot(xs, slope * xs + intercept, color=COLOR_TREND, alpha=0.35, linewidth=2, zorder=1)

    normal = [r for r in records if not r["is_outlier"]]
    outliers = [r for r in records if r["is_outlier"]]

    ax.scatter(
        [r["x"] for r in normal],
        [r["value"] for r in normal],
        s=70,
        color=COLOR_POINT,
        edgecolors=COLOR_SURFACE,
        linewidths=1.5,
        zorder=2,
    )
    ax.scatter(
        [r["x"] for r in outliers],
        [r["value"] for r in outliers],
        s=90,
        color=COLOR_OUTLIER,
        edgecolors=COLOR_SURFACE,
        linewidths=1.5,
        zorder=3,
    )
    for r in outliers:
        ax.annotate(
            f"FOV {r['fov']}",
            (r["x"], r["value"]),
            textcoords="offset points",
            xytext=(8, 6),
            fontsize=9,
            color=COLOR_PRIMARY,
        )

    fig.suptitle(name, x=0.015, y=0.995, ha="left", color=COLOR_PRIMARY, fontsize=14, fontweight="bold")
    ax.set_title(
        f"slope = {slope:.2f}  ·  r = {corr:.2f}  ·  r² = {corr ** 2:.2f}",
        color=COLOR_SECONDARY,
        fontsize=10,
        loc="left",
        pad=10,
    )
    ax.set_xlabel("Combined severity (density rank 0-3 + overlap rank 0-4)", color=COLOR_SECONDARY, fontsize=10)
    ylabel = f"{name} ({unit.strip() or 'raw value'})" if unit else f"{name} (raw value)"
    ax.set_ylabel(ylabel, color=COLOR_SECONDARY, fontsize=10)

    ax.set_xticks(range(8))
    ax.tick_params(colors=COLOR_MUTED, labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(COLOR_AXIS)
    ax.grid(True, axis="y", color=COLOR_GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


def main():
    fovs = load_fovs()
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    report_sections = []
    outlier_tally = {}

    for name, csv_file, column, unit in TECHNIQUES:
        metric_rows = load_metric_csv(csv_file)
        records = []
        for row in fovs:
            metric_row = metric_rows.get(row["filename"])
            if metric_row is None:
                raise ValueError(f"No {name} result for {row['filename']}")
            records.append(
                {
                    "fov": row["fov"],
                    "filename": row["filename"],
                    "crenated": row["crenated"].strip().lower() == "yes",
                    "combined_score": combined_score(row),
                    "value": float(metric_row[column]),
                }
            )

        jittered_x(records)
        slope, intercept, std, r = find_outliers(records)

        slug = name.lower().replace(" ", "-").replace("(", "").replace(")", "")
        plot_path = PLOTS_DIR / f"{slug}.png"
        plot_technique(name, unit, records, slope, intercept, r, plot_path)

        outliers = [r_ for r_ in records if r_["is_outlier"]]
        for o in outliers:
            outlier_tally.setdefault(o["fov"], []).append(name)

        direction = "increases" if slope > 0 else "decreases"
        strength = (
            "strong" if abs(r) >= 0.7 else "moderate" if abs(r) >= 0.4 else "weak"
        )
        lines = [
            f"## {name}",
            "",
            f"![{name}](plots/{slug}.png)",
            "",
            f"- Trend: value {direction} with combined severity (slope={slope:.2f}, r={r:.2f}, r²={r ** 2:.2f}, {strength} correlation).",
        ]
        if outliers:
            outlier_desc = "; ".join(
                f"FOV {o['fov']} ({o['filename']}, value={o['value']:.2f}, "
                f"combined score={o['combined_score']}, residual={o['residual']:.2f}"
                + (", crenated" if o["crenated"] else "")
                + ")"
                for o in outliers
            )
            lines.append(f"- **Outliers** (|residual| > {OUTLIER_Z} sd from the linear trend): {outlier_desc}.")
        else:
            lines.append(f"- No points exceeded the {OUTLIER_Z} sd residual threshold.")
        report_sections.append("\n".join(lines))

    cross_outliers = {fov: techs for fov, techs in outlier_tally.items() if len(techs) >= 2}
    cross_section_lines = ["## Cross-technique outliers", ""]
    if cross_outliers:
        cross_section_lines.append(
            "FOVs flagged as outliers in more than one technique -- these disagree with their "
            "assigned density/overlap label across multiple independent signals, and are the best "
            "candidates for a manual visual re-check:"
        )
        cross_section_lines.append("")
        for fov, techs in sorted(cross_outliers.items(), key=lambda kv: -len(kv[1])):
            cross_section_lines.append(f"- **FOV {fov}**: outlier in {', '.join(techs)}")
    else:
        cross_section_lines.append("No FOV was flagged as an outlier in more than one technique.")

    report = "\n\n".join(
        [
            "# Initial dataset: per-technique findings report",
            "Dataset: `data/raw/initial-dataset-071626` (13 FOVs). "
            "Each technique's raw output is plotted against a combined ordinal severity score: "
            f"density rank ({', '.join(f'{d}={i}' for i, d in enumerate(DENSITY_ORDER))}) "
            f"plus overlap rank ({', '.join(f'{o}={i}' for i, o in enumerate(OVERLAP_ORDER))}), "
            "giving an integer range of 0-7. Points sharing a combined score are jittered "
            "horizontally for readability only -- the underlying x value is the integer score. "
            f"Outliers are points whose residual from a per-technique linear fit exceeds "
            f"{OUTLIER_Z} standard deviations.",
            "\n\n".join(report_sections),
            "\n".join(cross_section_lines),
        ]
    )

    report_path = RESULTS_DIR / "report.md"
    report_path.write_text(report)
    print(f"Wrote report to {report_path}")
    print(f"Wrote {len(TECHNIQUES)} plots to {PLOTS_DIR}")


if __name__ == "__main__":
    main()
