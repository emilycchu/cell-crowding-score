"""Shared constants, label parsing, IO, and feature computation for the v2 density/Rouleaux
pipeline (merge_labels_v2.py, extract_features_v2.py, calibrate_v2.py, plot_results_v2.py,
score_fov_v2.py).

compute_features() is the single source of truth for turning an image into the feature
vector both calibration (extract_features_v2.py) and inference (score_fov_v2.py) consume --
importing it from here in both places guarantees they can never drift apart.

The "overlap" axis is internally named "overlap" (matching the source label CSVs' column
name and the existing repo convention), but is always displayed to the user as "Rouleaux"
(see AXIS_DISPLAY_NAMES / display_level) per project convention for this tool.
"""
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.features.edge_density import edge_density  # noqa: E402
from src.features.glcm_contrast import glcm_contrast  # noqa: E402
from src.features.lbp_entropy import lbp_entropy  # noqa: E402
from src.features.otsu_separability import otsu_separability  # noqa: E402
from src.features.tile_heterogeneity import coefficient_of_variation, patchiness, tile_statistics  # noqa: E402
from src.pipeline import list_image_paths, load_image  # noqa: E402,F401  (re-exported)
from src.segmentation import cell_coverage, correct_illumination, otsu_segment, to_grayscale  # noqa: E402

# --- paths ---
INITIAL_LABELS_CSV = ROOT / "data" / "labels" / "initial-dataset-071626" / "fovs.csv"
INITIAL_IMAGE_DIR = ROOT / "data" / "raw" / "initial-dataset-071626"
TANZANIA_LABELS_CSV = ROOT / "data" / "labels" / "tanzania-073026" / "KTR-72502948-annotated.csv"
TANZANIA_IMAGE_DIR = ROOT / "data" / "raw" / "new" / "KTR-72502948" / "dpc"
TANZANIA_IMAGE_NAME = "dpc-{fov_id:03d}-KTR-72502948.png"

RESULTS_DIR = ROOT / "data" / "results" / "density-rouleaux-v2"
MERGED_LABELS_CSV = RESULTS_DIR / "merged-labels.csv"
FEATURES_CSV = RESULTS_DIR / "features.csv"
PARAMS_JSON = RESULTS_DIR / "density_overlap_v2_params.json"
REPORT_MD = RESULTS_DIR / "calibration-report.md"
PLOTS_DIR = RESULTS_DIR / "plots"

# --- label vocabulary: 5 levels each, "sparser" kept distinct from "monolayer" ---
DENSITY_LEVELS = ["sparser", "monolayer", "slightly dense", "dense", "very dense"]
OVERLAP_LEVELS = ["no rouleaux", "slight rouleaux", "some rouleaux", "rouleaux", "heavy rouleaux"]
DEFAULT_DENSITY_LABEL = "monolayer"
DEFAULT_OVERLAP_LABEL = "no rouleaux"

AXIS_LEVELS = {"density": DENSITY_LEVELS, "overlap": OVERLAP_LEVELS}
AXIS_DISPLAY_NAMES = {"density": "Density", "overlap": "Rouleaux"}

# Tanzania free-text tag -> our lowercase level vocabulary. Deliberately NOT reusing
# scripts/compare_tanzania_labels.py's fold_density(), which folds "Sparser" into
# "Monolayer" -- this task wants sparser as a genuine 5th level.
DENSITY_TAGS = {
    "Sparser": "sparser",
    "Monolayer": "monolayer",
    "Slightly Dense": "slightly dense",
    "Dense": "dense",
    "Very Dense": "very dense",
}
OVERLAP_TAGS = {
    "Slight Rouleaux": "slight rouleaux",
    "Some Rouleaux": "some rouleaux",
    "Rouleaux": "rouleaux",
    "Heavy Rouleaux": "heavy rouleaux",
}

# tile-grid feature parameters (see src/features/tile_heterogeneity.py)
TILE_GRID_SIZE = 7
TILE_GLCM_LEVELS = 32

# dataviz palette (references/palette.md), matching scripts/tanzania_comparison.py
JITTER_SEED = 7
COLOR_MINE = "#2a78d6"
COLOR_GRID = "#e1e0d9"
COLOR_AXIS = "#c3c2b7"
COLOR_MUTED = "#898781"
COLOR_PRIMARY = "#0b0b0b"
COLOR_SECONDARY = "#52514e"
COLOR_SURFACE = "#fcfcfb"


def density_ordinal(label):
    return DENSITY_LEVELS.index(label.strip().lower())


def overlap_ordinal(label):
    return OVERLAP_LEVELS.index(label.strip().lower())


def display_level(label):
    """'slightly dense' -> 'Slightly Dense', 'no rouleaux' -> 'No Rouleaux'."""
    return label.title()


def parse_tanzania_tags(tags_str):
    """Parse the Tanzania annotated CSV's free-text `tags` column into (density_label,
    overlap_label). The density tag is always present in this dataset (a missing one is a
    real data bug, so this raises); the overlap tag defaults to "no rouleaux" when absent.
    Other tags (Crenated, Unfocused, Artifact, Other Dimples) are ignored.
    """
    parts = [p.strip() for p in tags_str.split(",")]
    density_label = None
    overlap_label = None
    for p in parts:
        if p in DENSITY_TAGS:
            density_label = DENSITY_TAGS[p]
        elif p in OVERLAP_TAGS:
            overlap_label = OVERLAP_TAGS[p]
    if density_label is None:
        raise ValueError(f"no density tag found in {tags_str!r}")
    return density_label, overlap_label or DEFAULT_OVERLAP_LABEL


def read_csv_dicts(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def write_csv_dicts(path, fieldnames, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compute_features(image):
    """The full candidate feature vector for one FOV image (BGR, as returned by load_image).

    Shared by extract_features_v2.py (calibration) and score_fov_v2.py (inference) so the
    two can never compute features differently.
    """
    gray = to_grayscale(image)
    mask, otsu_threshold = otsu_segment(image)
    coverage = cell_coverage(mask)
    eta = otsu_separability(image)
    saturation_score = float(np.clip(coverage * (1.0 - eta), 0.0, 1.0))

    corrected = correct_illumination(gray, blur_ksize=301)

    def _tile_glcm_contrast(tile):
        quantized = (tile.astype(np.uint16) * TILE_GLCM_LEVELS // 256).astype(np.uint8)
        return glcm_contrast(quantized, levels=TILE_GLCM_LEVELS)

    tile_contrasts = tile_statistics(corrected, grid_size=TILE_GRID_SIZE, stat_fn=_tile_glcm_contrast)

    return {
        "coverage": coverage,
        "otsu_threshold": float(otsu_threshold),
        "otsu_separability": eta,
        "saturation_score": saturation_score,
        "lbp_entropy": lbp_entropy(image),
        "glcm_contrast": glcm_contrast(image),
        "edge_density_unmasked": edge_density(image),
        "tile_glcm_cv": coefficient_of_variation(tile_contrasts),
        "tile_glcm_patchiness": patchiness(tile_contrasts),
    }


def apply_saturation_override(label, features, override_cfg):
    """No-op passthrough while override_cfg is None or disabled (today's behavior, per
    project decision to keep the saturation signal data-driven rather than a hard rule).

    To switch to a hard override later: set override_cfg = {"enabled": true,
    "feature": "saturation_score", "threshold": <fitted cutoff>, "max_label": <top bucket
    label for this axis>} in density_overlap_v2_params.json -- no code restructuring needed.
    """
    if not override_cfg or not override_cfg.get("enabled"):
        return label
    if features.get(override_cfg["feature"], 0.0) >= override_cfg["threshold"]:
        return override_cfg["max_label"]
    return label
