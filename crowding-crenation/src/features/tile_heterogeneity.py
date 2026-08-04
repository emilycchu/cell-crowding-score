"""Tile-grid spatial heterogeneity: split an image into a grid and summarize how much a
per-tile statistic (e.g. GLCM contrast) varies across tiles. A single whole-image scalar
can't distinguish a uniformly dense/Rouleauxed FOV from a patchy, unevenly patterned one --
tiling exposes that variation directly.
"""
import numpy as np


def tile_statistics(image, grid_size=7, stat_fn=None):
    """Split image into grid_size x grid_size tiles (by tile *count*, via np.array_split --
    resolution-invariant, not a fixed pixel size, so it means the same thing across images
    of different resolutions) and apply stat_fn to each tile.
    """
    if stat_fn is None:
        raise ValueError("stat_fn is required")

    stats = []
    for row_chunk in np.array_split(image, grid_size, axis=0):
        for tile in np.array_split(row_chunk, grid_size, axis=1):
            if tile.size == 0:
                continue
            stats.append(stat_fn(tile))
    return np.array(stats, dtype=float)


def coefficient_of_variation(tile_stats):
    mean = float(np.mean(tile_stats))
    if abs(mean) < 1e-9:
        return 0.0
    return float(np.std(tile_stats) / mean)


def patchiness(tile_stats):
    """(max - median) / median -- catches a small number of outlier tiles (e.g. a small
    localized Rouleaux cluster) that barely move the whole-grid mean or coefficient of
    variation.
    """
    med = float(np.median(tile_stats))
    if abs(med) < 1e-9:
        return 0.0
    return float((np.max(tile_stats) - med) / med)
