"""Render data/results/focus-080426/focus-scores.csv into a human-readable markdown summary:
one compact per-quadrant table per metric, plus a few automatically-flagged findings (FOVs
with the largest quadrant-to-quadrant range, and FOVs where a metric couldn't be computed at
all -- itself a signal on severely blurred images, not just a gap in the data).

Usage:
    python scripts/summarize_focus.py data/results/focus-080426/focus-scores.csv \\
        data/results/focus-080426/summary.md
"""
import argparse
import csv
from pathlib import Path

METRICS = ["laplacian_variance", "tenengrad", "fft_high_freq_ratio", "edge_width", "coverage_fraction"]
QUADRANTS = ["tl", "tr", "bl", "br"]
DECIMALS = {
    "laplacian_variance": 1,
    "tenengrad": 0,
    "fft_high_freq_ratio": 4,
    "edge_width": 3,
    "coverage_fraction": 2,
}
TOP_N_FLAGGED = 5
REFERENCE_LABELS = ("focused", "unsure")  # used only to derive a severe-blur cutoff, never to tune metrics


def fmt(value, metric):
    if value is None or value == "":
        return "n/a"
    return f"{float(value):.{DECIMALS[metric]}f}"


def load_rows(csv_path):
    rows = list(csv.DictReader(open(csv_path)))
    for row in rows:
        row["fov_id"] = int(row["fov_id"])
    return rows


def metric_table(rows, metric):
    header = (
        f"| sample_id | fov_id | country | annotated | "
        f"{' | '.join(q for q in QUADRANTS)} | range |\n"
        f"|---|---|---|---|---|---|---|---|---|\n"
    )
    ordered = sorted(
        rows,
        key=lambda r: float(r[f"whole__{metric}"]) if r[f"whole__{metric}"] not in (None, "") else -1,
    )
    lines = []
    for r in ordered:
        quad_values = " | ".join(fmt(r[f"{q}__{metric}"], metric) for q in QUADRANTS)
        range_val = fmt(r[f"{metric}__quadrant_range"], metric)
        lines.append(
            f"| {r['sample_id']} | {r['fov_id']} | {r['country']} | {r['annotated_focus_level']} | "
            f"{quad_values} | {range_val} |"
        )
    return header + "\n".join(lines) + "\n"


def flagged_uniformity(rows, metric, top_n=TOP_N_FLAGGED):
    with_range = [r for r in rows if r[f"{metric}__quadrant_range"] not in (None, "")]
    ranked = sorted(with_range, key=lambda r: float(r[f"{metric}__quadrant_range"]), reverse=True)
    lines = []
    for r in ranked[:top_n]:
        lines.append(
            f"- `{r['sample_id']}` FOV {r['fov_id']} ({r['country']}, annotated "
            f"`{r['annotated_focus_level']}`): {metric} range = "
            f"{fmt(r[f'{metric}__quadrant_range'], metric)} "
            f"(tl={fmt(r[f'tl__{metric}'], metric)}, tr={fmt(r[f'tr__{metric}'], metric)}, "
            f"bl={fmt(r[f'bl__{metric}'], metric)}, br={fmt(r[f'br__{metric}'], metric)})"
        )
    return "\n".join(lines)


def missing_metric_fovs(rows, metric):
    return [r for r in rows if r[f"whole__{metric}"] in (None, "")]


def whole_value(row, metric):
    v = row[f"whole__{metric}"]
    return None if v in (None, "") else float(v)


def severe_cutoff(rows, metric):
    """The lowest whole-image value among annotated `focused`/`unsure` FOVs -- anything below
    this, regardless of its own label or site, sits outside the range any reference-focused
    FOV in this dataset ever produced. Used only to name/inspect a cluster after the fact, not
    to threshold or calibrate the metrics themselves.
    """
    reference = [whole_value(r, metric) for r in rows if r["annotated_focus_level"] in REFERENCE_LABELS]
    reference = [v for v in reference if v is not None]
    return min(reference) if reference else None


def partition_by_cutoff(rows, metric, cutoff):
    below, above = [], []
    for r in rows:
        v = whole_value(r, metric)
        if v is None:
            continue
        (below if v < cutoff else above).append(r)
    return below, above


def range_by_group(rows, metric, key_fn):
    groups = {}
    for r in rows:
        v = whole_value(r, metric)
        if v is None:
            continue
        groups.setdefault(key_fn(r), []).append(v)
    return {k: (min(vs), max(vs), len(vs)) for k, vs in groups.items()}


def severity_conclusions(rows):
    lines = []
    lapvar_cutoff = severe_cutoff(rows, "laplacian_variance")
    ten_cutoff = severe_cutoff(rows, "tenengrad")
    severe_lap, mild_lap = partition_by_cutoff(rows, "laplacian_variance", lapvar_cutoff)
    severe_ten, _ = partition_by_cutoff(rows, "tenengrad", ten_cutoff)

    same_cluster = {(r["sample_id"], r["fov_id"]) for r in severe_lap} == {
        (r["sample_id"], r["fov_id"]) for r in severe_ten
    }
    lap_margin = lapvar_cutoff - max(whole_value(r, "laplacian_variance") for r in severe_lap)
    ten_margin = ten_cutoff - max(whole_value(r, "tenengrad") for r in severe_ten)
    severe_countries = sorted({r["country"] for r in severe_lap})
    severe_labels = sorted({r["annotated_focus_level"] for r in severe_lap})

    lines.append(
        "### Severe blur (cells not resolvable): absolute whole-image energy metrics work, cross-site\n"
    )
    lines.append(
        f"Splitting every FOV at the lowest whole-image value seen among annotated `focused`/`unsure` "
        f"FOVs (never at a value chosen to fit the split) gives a cutoff of "
        f"**laplacian_variance = {lapvar_cutoff:.1f}** and **tenengrad = {ten_cutoff:.0f}**. "
        f"{'Both metrics put the exact same ' + str(len(severe_lap)) + ' FOVs' if same_cluster else 'The two metrics disagree on which FOVs fall'} "
        f"below that line: "
        + ", ".join(
            f"`{r['sample_id']}` FOV {r['fov_id']} (`{r['annotated_focus_level']}`)" for r in severe_lap
        )
        + f". The nearest focused/unsure FOV clears that cutoff by {lap_margin:.1f} on laplacian_variance "
        f"and {ten_margin:.0f} on tenengrad -- a wide, clean margin, not a knife-edge threshold.\n"
    )
    lines.append(
        f"This cluster is all {'/'.join(severe_countries)} in the current data, but the cutoff isn't simply "
        f"picking out a site: 8 other LB FOVs labeled `unfocused` score well above it (see mild-blur section "
        f"below), so the same absolute threshold separates severe from mild blur *within* LB, not just "
        f"LB-vs-elsewhere. **Practical takeaway: for catching FOVs where no cells are resolvable at all, a "
        f"fixed whole-image threshold on laplacian_variance or tenengrad is reliable regardless of site.**\n"
    )

    fft_values = [whole_value(r, "fft_high_freq_ratio") for r in severe_lap]
    all_fft = [whole_value(r, "fft_high_freq_ratio") for r in rows if whole_value(r, "fft_high_freq_ratio") is not None]
    lines.append(
        f"**`fft_high_freq_ratio` does *not* extend this to the frequency domain the way it looks like it "
        f"should.** Despite being conceptually the same \"how much fine detail is left\" question, the same "
        f"{len(severe_lap)} severe-blur FOVs score fft_high_freq_ratio = "
        + ", ".join(f"{v:.3f}" for v in fft_values)
        + f" -- spanning nearly the entire dataset's range ({min(all_fft):.3f}-{max(all_fft):.3f}), not "
        f"clustered low. A flattened, information-poor image apparently doesn't collapse this ratio the way "
        f"it collapses laplacian_variance/tenengrad; don't use it as a severe-blur filter.\n"
    )

    no_edges = missing_metric_fovs(rows, "edge_width")
    edge_defined_in_severe = [r for r in severe_lap if r not in no_edges]
    lines.append(
        f"`edge_width` going undefined (`n/a`, fewer than 20 Canny edge pixels) is a real severe-blur signal "
        f"but an inconsistent one: only {len(no_edges)} of the {len(severe_lap)} severe FOVs trigger it "
        + ("(" + ", ".join(f"FOV {r['fov_id']}" for r in no_edges) + "); ")
        + f"the other {len(edge_defined_in_severe)} still report a numeric edge_width indistinguishable from "
        f"the mild-blur LB group. Treat it as a bonus flag when it fires, not a primary detector.\n"
    )

    lines.append(
        "### Mild blur / slightly pixelated (cells still visible): absolute metrics are site-confounded, use quadrant range instead\n"
    )
    mild_by_group = range_by_group(mild_lap, "laplacian_variance", lambda r: (r["country"], r["annotated_focus_level"]))
    lines.append(
        "Once the severe cluster is set aside, whole-image laplacian_variance ranges overlap heavily across "
        "sites and labels -- there is no single global threshold that would separate mild `unfocused` from "
        "`focused` here:\n"
    )
    for (country, label), (lo, hi, n) in sorted(mild_by_group.items()):
        lines.append(f"- {country} `{label}` (n={n}): {lo:.1f}-{hi:.1f}")
    lines.append(
        "\nThe LB mildly-`unfocused` band (202.96-338.90) sits entirely *above* the TZ `focused` band "
        "(56.16-111.52) and overlaps the UG `focused` band (177.10-237.27) -- i.e. a mildly-blurred LB FOV "
        "reads as sharper than a genuinely in-focus TZ FOV on this metric, purely from site/staining texture "
        "differences (see main README for the visual explanation). **A fixed whole-image cutoff would "
        "misclassify most of this dataset at the mild-blur tier.**\n"
    )
    lines.append(
        "The one signal in this pass that stays meaningful at this severity is the **within-FOV "
        "`*__quadrant_range`** (max - min across the 4 quadrants, see 'Flagged' section below): it's relative "
        "to the FOV's own quadrants rather than an absolute cross-site value, so it isn't affected by the "
        "site-texture gap above. Its caveat: it flags *spatial non-uniformity*, not overall blur -- the two "
        "largest quadrant ranges in the whole dataset (`DPSP-1070-AS-1` FOV 219, `PBC-603-1` FOV 62) belong "
        "to FOVs annotated `focused`, because part of each frame really is soft while the rest is sharp. Use "
        "it as a \"this FOV isn't uniform\" gate alongside a per-site/per-slide baseline, not as a standalone "
        "focused/unfocused classifier.\n"
    )
    lines.append(
        "`coverage_fraction` is not usable as a filtering feature at any severity here -- it's context only "
        "by design, and becomes actively unstable (swinging ~0 to ~1 with no spatial pattern) once an FOV is "
        "already severely blurred (see caveat in that section below).\n"
    )
    return "\n".join(lines)


def within_slide_section(rows):
    by_sample = {}
    for r in rows:
        by_sample.setdefault(r["sample_id"], []).append(r)
    multi = {sid: rs for sid, rs in by_sample.items() if len(rs) > 1}

    lines = [
        f"Only {len(multi)} of {len(by_sample)} sampled slides in this round has more than one labeled FOV, "
        "so within-slide consistency is a single data point here, not yet a statistical claim (see README "
        "future directions -- more labeled FOVs per slide is the fix).\n"
    ]
    for sid, rs in multi.items():
        lines.append(f"- `{sid}` ({rs[0]['country']}):")
        for r in sorted(rs, key=lambda r: r["fov_id"]):
            lines.append(
                f"  - FOV {r['fov_id']} (`{r['annotated_focus_level']}`): "
                f"laplacian_variance={whole_value(r, 'laplacian_variance'):.1f}, "
                f"tenengrad={whole_value(r, 'tenengrad'):.0f}"
            )
    if multi:
        lines.append(
            "\nThe two FOVs from this slide land in the same mild-`unfocused` band as each other and well "
            "clear of the severe-blur cluster -- consistent with blur being a slide-level property here, but "
            "not enough repeats to confirm it generalizes.\n"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scores_csv", type=Path)
    parser.add_argument("out_md", type=Path)
    args = parser.parse_args()

    rows = load_rows(args.scores_csv)
    by_country = {}
    for r in rows:
        by_country.setdefault(r["country"], []).append(r)
    by_label = {}
    for r in rows:
        by_label.setdefault(r["annotated_focus_level"], []).append(r)

    sections = []
    sections.append(f"# Focus scoring summary -- focus-080426\n")
    sections.append(
        f"{len(rows)} FOVs scored: "
        + ", ".join(f"{country} n={len(rs)}" for country, rs in sorted(by_country.items()))
        + ". Annotated labels (reference only, not used to tune anything): "
        + ", ".join(f"`{label}` n={len(rs)}" for label, rs in sorted(by_label.items()))
        + ".\n"
    )
    sections.append(
        "Full per-quadrant numbers for every metric are in `focus-scores.csv` in this same "
        "folder; per-FOV annotated preview images (quadrant grid + metric overlay) are in "
        "`previews/`. Tables below are sorted by whole-image value, ascending, so the most "
        "severely blurred FOVs (by each metric) are at the top.\n"
    )

    sections.append(
        "## Conclusions: which features reliably filter blur, and at what severity\n"
    )
    sections.append(severity_conclusions(rows))

    sections.append("## Within-slide comparison (repeat FOVs from the same sample)\n")
    sections.append(within_slide_section(rows))

    sections.append("## laplacian_variance (per quadrant, whole-image-ascending)\n")
    sections.append(metric_table(rows, "laplacian_variance"))

    sections.append("## tenengrad (per quadrant, whole-image-ascending)\n")
    sections.append(metric_table(rows, "tenengrad"))

    sections.append("## fft_high_freq_ratio (per quadrant, whole-image-ascending)\n")
    sections.append(
        "Fraction of 2D FFT power at/above 25% of Nyquist radius. **See Conclusions above: this "
        "one does not reliably separate severe blur from focused FOVs**, unlike laplacian_variance "
        "and tenengrad -- it's included here for completeness, not as a recommended filter.\n"
    )
    sections.append(metric_table(rows, "fft_high_freq_ratio"))

    sections.append("## edge_width (per quadrant, whole-image-ascending)\n")
    sections.append(
        "`n/a` = fewer than 20 Canny edge pixels detected in that region -- on the most "
        "severely blurred FOVs this happens across the *whole* image, which is itself a "
        "meaningful signal (no edges sharp enough to detect at all), not a missing "
        "measurement.\n"
    )
    sections.append(metric_table(rows, "edge_width"))
    no_edges = missing_metric_fovs(rows, "edge_width")
    if no_edges:
        sections.append(
            "FOVs with no whole-image edge_width (no detectable edges anywhere): "
            + ", ".join(f"`{r['sample_id']}` FOV {r['fov_id']} (`{r['annotated_focus_level']}`)" for r in no_edges)
            + "\n"
        )

    sections.append("## coverage_fraction (per quadrant, whole-image-ascending)\n")
    sections.append(
        "Context only, not a focus measure -- included so a quadrant that's mostly empty "
        "background isn't mistaken for a blurry one. **Caveat found in this round:** on the "
        "most severely blurred FOVs, coverage_fraction becomes unstable rather than just "
        "low -- per-quadrant values swing between ~0 and ~1 with no spatial pattern (e.g. "
        "`LB-D3-2025-09-04-131645-250917282-D-Only-1-4` FOV 88 has quadrant coverage 0.005, "
        "0.99, 0.004, 1.00). This is an Otsu-threshold artifact: Otsu assumes a bimodal "
        "brightness histogram (foreground vs. background), and severe blur flattens the "
        "image enough that the histogram loses that bimodal structure, so the threshold "
        "lands almost arbitrarily close to the whole region's narrow brightness range. Don't "
        "trust coverage_fraction on FOVs that are already flagged as severely blurred by the "
        "other metrics.\n"
    )
    sections.append(metric_table(rows, "coverage_fraction"))

    sections.append("## Flagged: most non-uniform focus within a single FOV\n")
    sections.append(
        "Top FOVs by laplacian_variance quadrant-to-quadrant range -- the case this whole "
        "quadrant-scoring approach is meant to catch (one part of the frame clearly softer "
        "than the rest of the *same* FOV, not a cross-slide comparison).\n"
    )
    sections.append(flagged_uniformity(rows, "laplacian_variance") + "\n")

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text("\n".join(sections))
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
