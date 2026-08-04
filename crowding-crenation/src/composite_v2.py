"""Generic, axis-agnostic weighted composite + bucketing.

Unlike src/composite.py's FeatureWeights (a dataclass hardcoded to the four "four-step"
feature names), this is plain dict-based: the density and Rouleaux/overlap composites use
different, independently-fit feature sets, so a fixed set of dataclass fields doesn't fit
either one cleanly. Both scripts/ai-first/calibrate_v2.py (to score the calibration set)
and scripts/ai-first/score_fov_v2.py (to score new images) import this module so the exact
same scoring logic is used in both places.
"""


def normalize(value, min_value, max_value):
    if max_value <= min_value:
        return 0.0
    return min(1.0, max(0.0, (value - min_value) / (max_value - min_value)))


def weighted_composite(features, weights, ranges):
    """Weighted average of min-max normalized features, scaled to [0, 1].

    features: dict of {name: raw value}
    weights: dict of {name: weight}
    ranges: dict of {name: (min, max)}
    """
    score = 0.0
    total_weight = 0.0
    for name, weight in weights.items():
        if name not in features or name not in ranges:
            continue
        score += weight * normalize(features[name], *ranges[name])
        total_weight += weight

    if total_weight == 0.0:
        return 0.0
    return score / total_weight


def bucket(score, thresholds, labels):
    """Cut a continuous score into one of len(thresholds) + 1 ordinal labels.

    thresholds must be ascending; score < thresholds[0] -> labels[0], etc.
    """
    if len(labels) != len(thresholds) + 1:
        raise ValueError("labels must have exactly one more entry than thresholds")

    for i, t in enumerate(thresholds):
        if score < t:
            return labels[i]
    return labels[-1]
