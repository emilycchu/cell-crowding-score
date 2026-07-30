"""Compare the experimental downsampled LBP entropy variant against the original on the
13-FOV labeled set: correlation, drift, and speedup. Read-only -- reports numbers, does
not decide or apply anything. See src/features/lbp_entropy_fast.py for why this variant
is not wired into the production path.

Usage:
    python scripts/compare_lbp_entropy_fast.py
"""
import csv
import sys
import time
from pathlib import Path

from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.features.lbp_entropy import lbp_entropy
from src.features.lbp_entropy_fast import lbp_entropy_downsampled
from src.pipeline import list_image_paths, load_image

DATASET = "initial-dataset-071626"
INPUT_DIR = Path(f"data/raw/{DATASET}")
OUTPUT_CSV = Path(f"data/results/{DATASET}/lbp-entropy-fast-comparison.csv")
DOWNSAMPLE_FACTORS = (2, 4)

FIELDNAMES = ["filename", "lbp_entropy_original", "time_original_s"]
for ds in DOWNSAMPLE_FACTORS:
    FIELDNAMES += [f"lbp_entropy_ds{ds}", f"time_ds{ds}_s", f"abs_diff_ds{ds}"]


def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    value = fn(*args, **kwargs)
    return value, time.perf_counter() - start


def compare_on_directory(directory):
    paths = list_image_paths(directory)

    rows = []
    for path in paths:
        image = load_image(path)
        original, time_original = timed(lbp_entropy, image)
        row = {
            "filename": path.name,
            "lbp_entropy_original": round(original, 4),
            "time_original_s": round(time_original, 4),
        }
        for ds in DOWNSAMPLE_FACTORS:
            value, elapsed = timed(lbp_entropy_downsampled, image, downsample=ds)
            row[f"lbp_entropy_ds{ds}"] = round(value, 4)
            row[f"time_ds{ds}_s"] = round(elapsed, 4)
            row[f"abs_diff_ds{ds}"] = round(abs(value - original), 4)
        rows.append(row)
    return rows


def write_csv(rows, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows):
    originals = [row["lbp_entropy_original"] for row in rows]
    original_times = [row["time_original_s"] for row in rows]
    for ds in DOWNSAMPLE_FACTORS:
        values = [row[f"lbp_entropy_ds{ds}"] for row in rows]
        diffs = [row[f"abs_diff_ds{ds}"] for row in rows]
        times = [row[f"time_ds{ds}_s"] for row in rows]
        r = pearsonr(originals, values).statistic
        rho = spearmanr(originals, values).statistic
        mean_speedup = sum(o / t for o, t in zip(original_times, times)) / len(rows)
        print(
            f"downsample={ds}: r={r:.4f} rho={rho:.4f} "
            f"max_abs_diff={max(diffs):.4f} mean_abs_diff={sum(diffs) / len(diffs):.4f} "
            f"mean_speedup={mean_speedup:.1f}x"
        )


def main():
    rows = compare_on_directory(INPUT_DIR)
    write_csv(rows, OUTPUT_CSV)
    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")
    print_summary(rows)


if __name__ == "__main__":
    main()
