"""Compare manual (E. Chu) FOV labels against the program's automated labels for
the Tanzania slide KTR-72502948.

Manual labels (data/labels/tanzania-073026/KTR-72502948-annotated.csv) are a
free-text `tags` column; this script parses it into the same three axes the
program reports in data/new/KTR-72502948/fov_labels.csv: density, rouleaux
(overlap), and crenation.

Parsing rules (per project convention, matching COL_ORDER in
build_result_summary.py):
  - density: one of Sparser/Monolayer/Slightly Dense/Dense/Very Dense. Sparser
    (and the program's "sparse") are folded into Monolayer -- too few FOVs of
    either to justify a 5th bucket, and it makes the two label sets comparable.
  - rouleaux: one of Slight/Some/(plain) Rouleaux/Heavy Rouleaux; an absent tag
    means "no rouleaux" (minimum).
  - crenation: presence of the "Crenated" tag; absent means not crenated.
    Other free-text tags (Unfocused, Artifact, Other Dimples) aren't part of
    either program axis and are ignored here.

Usage:
    python scripts/compare_tanzania_labels.py
"""
import csv
import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent.parent
MANUAL_CSV = ROOT / "data" / "labels" / "tanzania-073026" / "KTR-72502948-annotated.csv"
PROGRAM_CSV = ROOT / "data" / "new" / "KTR-72502948" / "fov_labels.csv"
OUT_DIR = ROOT / "data" / "results" / "tanzania-073026"

DENSITY_TAGS = {"Sparser", "Monolayer", "Slightly Dense", "Dense", "Very Dense"}
ROULEAUX_TAGS = {"Slight Rouleaux", "Some Rouleaux", "Rouleaux", "Heavy Rouleaux"}
CRENATED_TAG = "Crenated"

DENSITY_ORDER = ["monolayer", "slightly dense", "dense", "very dense"]
ROULEAUX_ORDER = ["no rouleaux", "slight rouleaux", "some rouleaux", "rouleaux", "heavy rouleaux"]
CRENATION_ORDER = ["Not crenated", "Crenated"]

JITTER_SEED = 7

# dataviz reference palette (references/palette.md), categorical slots 1-2
COLOR_MINE = "#2a78d6"
COLOR_PROGRAM = "#eb6834"
COLOR_GRID = "#e1e0d9"
COLOR_AXIS = "#c3c2b7"
COLOR_MUTED = "#898781"
COLOR_PRIMARY = "#0b0b0b"
COLOR_SECONDARY = "#52514e"
COLOR_SURFACE = "#fcfcfb"


def fold_density(label):
    label = label.strip().lower()
    if label in ("sparser", "sparse"):
        return "monolayer"
    return label


def parse_manual_tags(tags_str):
    parts = [p.strip() for p in tags_str.split(",")]
    density = None
    rouleaux = None
    crenated = False
    for p in parts:
        if p in DENSITY_TAGS:
            density = p
        elif p in ROULEAUX_TAGS:
            rouleaux = p
        elif p == CRENATED_TAG:
            crenated = True
    if density is None:
        raise ValueError(f"no density tag found in {tags_str!r}")
    return {
        "density": fold_density(density),
        "rouleaux": rouleaux.lower() if rouleaux else "no rouleaux",
        "crenated": crenated,
    }


def load_manual(path):
    rows = list(csv.DictReader(open(path)))
    out = {}
    for r in rows:
        parsed = parse_manual_tags(r["tags"])
        out[int(r["fov_id"])] = parsed
    return out


def load_program(path):
    rows = list(csv.DictReader(open(path)))
    out = {}
    for r in rows:
        out[int(r["idx"])] = {
            "density": fold_density(r["density_label"]),
            "rouleaux": r["crowding_label"].strip().lower(),
            "crenated": r["crenation_flag"].strip().lower() == "flagged",
        }
    return out


def counts_by_order(records, key, order):
    c = {k: 0 for k in order}
    for rec in records:
        c[rec[key]] += 1
    return c


def plot_breakdown(mine, program, out_path):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)

    panels = [
        ("Density", DENSITY_ORDER, "density", [l.capitalize() for l in DENSITY_ORDER]),
        ("Overlap (rouleaux)", ROULEAUX_ORDER, "rouleaux", [l.capitalize() for l in ROULEAUX_ORDER]),
        (
            "Crenation",
            [False, True],
            "crenated",
            CRENATION_ORDER,
        ),
    ]

    for ax, (title, order, key, tick_labels) in zip(axes, panels):
        ax.set_facecolor(COLOR_SURFACE)
        mine_counts = [counts_by_order(mine, key, order)[k] if key != "crenated"
                       else sum(1 for r in mine if r[key] == k) for k in order]
        program_counts = [counts_by_order(program, key, order)[k] if key != "crenated"
                           else sum(1 for r in program if r[key] == k) for k in order]

        x = range(len(order))
        width = 0.36
        bars_mine = ax.bar(
            [xi - width / 2 for xi in x], mine_counts, width,
            color=COLOR_MINE, label="Mine", zorder=3,
        )
        bars_program = ax.bar(
            [xi + width / 2 for xi in x], program_counts, width,
            color=COLOR_PROGRAM, label="Program", zorder=3,
        )
        for bars in (bars_mine, bars_program):
            for b in bars:
                ax.annotate(
                    str(int(b.get_height())),
                    (b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    fontsize=8,
                    color=COLOR_SECONDARY,
                )

        ax.set_xticks(list(x))
        ax.set_xticklabels(tick_labels, rotation=20, ha="right", fontsize=9)
        ax.tick_params(colors=COLOR_MUTED, labelsize=9)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(COLOR_AXIS)
        ax.grid(True, axis="y", color=COLOR_GRID, linewidth=1, zorder=0)
        ax.set_axisbelow(True)
        ax.set_title(title, loc="left", color=COLOR_PRIMARY, fontsize=12, fontweight="bold", pad=10)
        ax.set_ylabel("FOV count", color=COLOR_SECONDARY, fontsize=9)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=COLOR_MINE),
        plt.Rectangle((0, 0), 1, 1, color=COLOR_PROGRAM),
    ]
    fig.legend(handles, ["Mine", "Program"], loc="upper right", frameon=False, fontsize=10)
    fig.suptitle(
        "KTR-72502948 (Tanzania) — manual vs. program label breakdown",
        x=0.015, y=0.99, ha="left", color=COLOR_PRIMARY, fontsize=15, fontweight="bold",
    )
    fig.text(
        0.015, 0.945,
        f"n = {len(mine)} FOVs each. Sparse/sparser folded into monolayer. "
        "Program density/rouleaux buckets are slide-relative quintiles (~equal counts by construction).",
        color=COLOR_SECONDARY, fontsize=9,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


def plot_overlap_vs_density(mine, program, out_path):
    rng = random.Random(JITTER_SEED)
    x_index = {k: i for i, k in enumerate(ROULEAUX_ORDER)}
    y_index = {k: i for i, k in enumerate(DENSITY_ORDER)}

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=150)
    fig.patch.set_facecolor(COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    def scatter_group(records, color, x_shift, marker, label, crenated_filter):
        xs, ys = [], []
        for r in records:
            if r["crenated"] != crenated_filter:
                continue
            base_x = x_index[r["rouleaux"]]
            base_y = y_index[r["density"]]
            xs.append(base_x + x_shift + rng.uniform(-0.09, 0.09))
            ys.append(base_y + rng.uniform(-0.16, 0.16))
        ax.scatter(
            xs, ys, s=26, marker=marker, color=color, alpha=0.5,
            linewidths=0, zorder=3, label=label,
        )

    scatter_group(mine, COLOR_MINE, -0.15, "o", "Mine — not crenated", False)
    scatter_group(mine, COLOR_MINE, -0.15, "^", "Mine — crenated", True)
    scatter_group(program, COLOR_PROGRAM, 0.15, "o", "Program — not crenated", False)
    scatter_group(program, COLOR_PROGRAM, 0.15, "^", "Program — crenated", True)

    ax.set_xticks(range(len(ROULEAUX_ORDER)))
    ax.set_xticklabels([l.capitalize() for l in ROULEAUX_ORDER], fontsize=10)
    ax.set_xlim(-0.5, len(ROULEAUX_ORDER) - 0.5)
    for i in range(1, len(ROULEAUX_ORDER)):
        ax.axvline(i - 0.5, color=COLOR_GRID, linewidth=1, zorder=0)

    ax.set_yticks(range(len(DENSITY_ORDER)))
    density_tick_labels = ["Monolayer (+sparser)"] + [l.capitalize() for l in DENSITY_ORDER[1:]]
    ax.set_yticklabels(density_tick_labels, fontsize=10)
    ax.set_ylim(-0.5, len(DENSITY_ORDER) - 0.5)
    for i in range(1, len(DENSITY_ORDER)):
        ax.axhline(i - 0.5, color=COLOR_GRID, linewidth=1, zorder=0)

    ax.tick_params(colors=COLOR_MUTED)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(COLOR_AXIS)
    ax.set_axisbelow(True)

    ax.set_xlabel("Overlap (rouleaux level)", color=COLOR_SECONDARY, fontsize=11)
    ax.set_ylabel("Density", color=COLOR_SECONDARY, fontsize=11)

    color_legend = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLOR_MINE, markersize=8, label="Mine"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLOR_PROGRAM, markersize=8, label="Program"),
    ]
    shape_legend = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLOR_MUTED, markersize=8, label="Not crenated"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor=COLOR_MUTED, markersize=8, label="Crenated"),
    ]
    leg1 = ax.legend(handles=color_legend, title="Source", loc="upper left", frameon=False, fontsize=9)
    ax.add_artist(leg1)
    ax.legend(handles=shape_legend, title="Crenation", loc="upper right", frameon=False, fontsize=9)

    fig.suptitle(
        "KTR-72502948 (Tanzania) — overlap vs. density, mine vs. program",
        x=0.015, y=0.98, ha="left", color=COLOR_PRIMARY, fontsize=14, fontweight="bold",
    )
    ax.set_title(
        f"n = {len(mine)} FOVs each, jittered within each cell to show spread",
        loc="left", color=COLOR_SECONDARY, fontsize=10, pad=10,
    )

    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out_path, facecolor=COLOR_SURFACE)
    plt.close(fig)


def main():
    manual = load_manual(MANUAL_CSV)
    program = load_program(PROGRAM_CSV)

    common_ids = sorted(set(manual) & set(program))
    if len(common_ids) != len(manual) or len(common_ids) != len(program):
        print(
            f"warning: manual has {len(manual)} FOVs, program has {len(program)}, "
            f"{len(common_ids)} in common"
        )

    mine = [manual[i] for i in common_ids]
    prog = [program[i] for i in common_ids]

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    plot_breakdown(mine, prog, OUT_DIR / "label-comparison-summary.png")
    plot_overlap_vs_density(mine, prog, OUT_DIR / "overlap-vs-density-scatter.png")

    merged_path = OUT_DIR / "merged-labels.csv"
    with open(merged_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "fov_id", "mine_density", "mine_rouleaux", "mine_crenated",
            "program_density", "program_rouleaux", "program_crenated",
        ])
        for i in common_ids:
            writer.writerow([
                i, manual[i]["density"], manual[i]["rouleaux"], manual[i]["crenated"],
                program[i]["density"], program[i]["rouleaux"], program[i]["crenated"],
            ])

    print(f"Wrote {OUT_DIR / 'label-comparison-summary.png'}")
    print(f"Wrote {OUT_DIR / 'overlap-vs-density-scatter.png'}")
    print(f"Wrote {merged_path}")
    print("mine density counts:", counts_by_order(mine, "density", DENSITY_ORDER))
    print("mine rouleaux counts:", counts_by_order(mine, "rouleaux", ROULEAUX_ORDER))
    print("mine crenated:", sum(1 for r in mine if r["crenated"]), "/", len(mine))
    print("program density counts:", counts_by_order(prog, "density", DENSITY_ORDER))
    print("program rouleaux counts:", counts_by_order(prog, "rouleaux", ROULEAUX_ORDER))
    print("program crenated:", sum(1 for r in prog if r["crenated"]), "/", len(prog))


if __name__ == "__main__":
    main()
