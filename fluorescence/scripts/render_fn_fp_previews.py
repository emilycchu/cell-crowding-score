"""Render annotated preview thumbnails for every FN/FP row (in either the baseline or
diffuse-fov-folded-in variant) from run_overexposed_diverse_test.py's results.csv, streamed
fresh from GCS (no disk cache of the raw FOV).

Buckets a row into exactly one of:
  A_rescued       spot_truth=yes, present_base=False, present_folded=True
                  (a real halo the ratio gate missed, correctly rescued by folding in)
  B_still_missed  spot_truth=yes, present_base=False, present_folded=False
                  (a real halo missed by both variants)
  C_fp_baseline   spot_truth=no,  present_base=True
                  (a false positive already in production today; folding in can't fix it,
                  since it only ever turns present False->True)
  D_fp_new        spot_truth=no,  present_base=False, present_folded=True
                  (a false positive introduced only by folding the diffuse-fov step in)

Usage:
    python scripts/render_fn_fp_previews.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2

from src.gcs_fov_multi import load_fov_image
from src.overexposure import detect_overexposure, mask_to_full_resolution

RESULTS_CSV = Path(__file__).resolve().parent.parent / "data" / "results" / "overexposed-diverse-080726" / "results.csv"
PREVIEW_DIR = Path(__file__).resolve().parent.parent / "data" / "results" / "overexposed-diverse-080726" / "previews"


def to_bool(v):
    return v.strip().lower() == "true"


def bucket_row(r):
    truth_yes = r["spot_truth"] == "yes"
    pb, pf = to_bool(r["present_base"]), to_bool(r["present_folded"])
    if truth_yes and not pb and pf:
        return "A_rescued"
    if truth_yes and not pb and not pf:
        return "B_still_missed"
    if not truth_yes and pb:
        return "C_fp_baseline"
    if not truth_yes and not pb and pf:
        return "D_fp_new"
    return None


def preview_filename(sample_id, fov_id):
    import re
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", sample_id)
    return f"{safe}__fov{fov_id}__preview.png"


def render(image, result, row, bucket, out_path):
    h, w = image.shape[:2]
    scale = 700 / max(h, w)
    preview = cv2.resize(image, (int(w * scale), int(h * scale)))

    mask_full = mask_to_full_resolution(result.mask, image.shape)
    mask_preview = cv2.resize(mask_full, (preview.shape[1], preview.shape[0]), interpolation=cv2.INTER_NEAREST)
    contours, _ = cv2.findContours(mask_preview, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    color = (0, 0, 255) if result.present else (0, 255, 0)
    cv2.drawContours(preview, contours, -1, color, 2)

    def put(y, text):
        cv2.putText(preview, text, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    put(20, f"{bucket}  truth={row['spot_truth']}  notes={row['notes'] or '(none)'}")
    put(42, f"present_base={row['present_base']}  present_folded={row['present_folded']}")
    put(64, f"ratio={result.contrast_ratio:.2f}  diffuse_radius={result.diffuse_radius:.0f}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), preview)


def main():
    rows = list(csv.DictReader(open(RESULTS_CSV)))
    manifest = []
    for row in rows:
        bucket = bucket_row(row)
        if bucket is None:
            continue
        sample_id, fov_id, country = row["sample_id"], int(row["fov_id"]), row["country"]
        print(f"[{bucket}] {sample_id} fov={fov_id} ({country})")
        image, _ = load_fov_image(sample_id, fov_id, country)
        result = detect_overexposure(image)
        out_name = preview_filename(sample_id, fov_id)
        render(image, result, row, bucket, PREVIEW_DIR / out_name)
        manifest.append({"bucket": bucket, "file": out_name, **row})

    manifest_path = PREVIEW_DIR / "manifest.csv"
    with open(manifest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        writer.writeheader()
        writer.writerows(manifest)
    print(f"\nWrote {len(manifest)} previews to {PREVIEW_DIR}, manifest at {manifest_path}")


if __name__ == "__main__":
    main()
