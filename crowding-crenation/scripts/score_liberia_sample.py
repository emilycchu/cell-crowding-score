"""Score a random sample of FOVs from a Liberia slide group (gs://liberia-2025) with the
current 4-technique pipeline + composite score, and write one combined CSV.

Usage:
    python scripts/score_liberia_sample.py negatives
    python scripts/score_liberia_sample.py positives
"""
import argparse
import csv
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from liberia_groups import GROUPS
from src.pipeline import list_image_paths, score_image

SAMPLE_SIZE = 20
SEED = 42
MAX_WORKERS = 8
FIELDNAMES = ["slide", "fov", "coverage", "edge_density", "glcm_contrast", "lbp_entropy", "composite_score"]


def _row_for(slide, path, result):
    f = result["features"]
    return {
        "slide": slide,
        "fov": path.name,
        "coverage": round(f["coverage"], 4),
        "edge_density": round(f["edge_density"], 4),
        "glcm_contrast": round(f["glcm_contrast"], 2),
        "lbp_entropy": round(f["lbp_entropy"], 4),
        "composite_score": round(result["score"], 4),
    }


def score_sample(slides):
    rng = random.Random(SEED)

    # Sequential: sample selection, so row order matches a sequential run for a fixed SEED.
    tasks = []
    for slide, gcs_dir in slides.items():
        paths = list_image_paths(gcs_dir)
        sample = rng.sample(paths, min(SAMPLE_SIZE, len(paths)))
        for path in sample:
            tasks.append((slide, path))

    # Parallel: score_image() itself, writing into pre-sized slots so output order stays
    # sequential-run-identical regardless of which thread finishes first.
    rows = [None] * len(tasks)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_index = {executor.submit(score_image, path): i for i, (slide, path) in enumerate(tasks)}
        done = 0
        for future in as_completed(future_to_index):
            i = future_to_index[future]
            slide, path = tasks[i]
            result = future.result()
            rows[i] = _row_for(slide, path, result)
            done += 1
            print(f"[{done}/{len(tasks)}] [{slide}] {path.name}: composite={rows[i]['composite_score']}")

    return rows


def write_csv(rows, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score a random FOV sample for a Liberia slide group.")
    parser.add_argument("group", choices=sorted(GROUPS))
    args = parser.parse_args()

    group = GROUPS[args.group]
    rows = score_sample(group["slides"])
    csv_path = group["results_dir"] / "composite-scores.csv"
    write_csv(rows, csv_path)
    print(f"Wrote {len(rows)} rows to {csv_path}")
