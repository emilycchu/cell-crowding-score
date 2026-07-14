"""Combine individual crowding-related features into a single composite score."""
from dataclasses import dataclass

DEFAULT_RANGES = {
    "coverage": (0.0, 1.0),
    "edge_density": (0.0, 1.0),
    "glcm_contrast": (0.0, 200.0),
    "lbp_entropy": (0.0, 6.0),
}


@dataclass
class FeatureWeights:
    coverage: float = 0.4
    edge_density: float = 0.2
    glcm_contrast: float = 0.2
    lbp_entropy: float = 0.2


def normalize(value, min_value, max_value):
    if max_value <= min_value:
        return 0.0
    return min(1.0, max(0.0, (value - min_value) / (max_value - min_value)))


def composite_score(features, weights=None, ranges=None):
    """Weighted average of min-max normalized features, scaled to [0, 1]."""
    weights = weights or FeatureWeights()
    ranges = ranges or DEFAULT_RANGES

    score = 0.0
    total_weight = 0.0
    for name, value in features.items():
        if name not in ranges:
            continue
        weight = getattr(weights, name, 0.0)
        score += weight * normalize(value, *ranges[name])
        total_weight += weight

    if total_weight == 0.0:
        return 0.0
    return score / total_weight
