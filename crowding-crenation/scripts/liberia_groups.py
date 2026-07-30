"""Slide-group config shared by score_liberia_sample.py, plot_liberia_composite.py,
and plot_liberia_techniques.py.
"""
from pathlib import Path

RESULTS_ROOT = Path(__file__).resolve().parent.parent / "data" / "results" / "libera-elwa-072826"

GROUPS = {
    "negatives": {
        "results_dir": RESULTS_ROOT / "negatives",
        "subtitle": "Liberia LB25-D12, ELWA negatives",
        "slides": {
            "250817118": "gs://liberia-2025/rawData4SS/LB25-D12/2026-03-04/2026-03-04-090110-250817118-(ELWA)-Negative.2/Images",
            "250817119": "gs://liberia-2025/rawData4SS/LB25-D12/2026-03-04/2026-03-04-114809-250817119(ELWA)-Negative.2/Images",
            "25071550": "gs://liberia-2025/rawData4SS/LB25-D12/2026-03-04/2026-03-04-155719-25071550-(ELWA)-Negative.2/Images",
            "25033489": "gs://liberia-2025/rawData4SS/LB25-D12/2026-03-05/2026-03-05-162353-25033489-(ELWA)-Negative.2/Images",
        },
    },
    "positives": {
        "results_dir": RESULTS_ROOT / "positives",
        "subtitle": "Liberia LB25-D3, ELWA positives",
        "slides": {
            "250810915": "gs://liberia-2025/rawData4SS/LB25-D3/2025-09-02/2025-09-02-121144-250810915-D-Only-(3+).1/Images",
            "190968326": "gs://liberia-2025/rawData4SS/LB25-D3/2025-09-27/2025-09-27-113818-190968326-(D-thin)-3+.4/Images",
            "250917371": "gs://liberia-2025/rawData4SS/LB25-D3/2025-10-03/2025-10-03-104211-250917371-(D-thin)-2+.3/Images",
            "250912792": "gs://liberia-2025/rawData4SS/LB25-D3/2025-10-03/2025-10-03-122127-250912792(D-thin)-3+.4/Images",
        },
    },
}

# dataviz reference palette (references/palette.md), categorical slots 1-4, assigned by slide position
SLIDE_COLOR_SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]


def slide_colors(group):
    slides = list(GROUPS[group]["slides"])
    return dict(zip(slides, SLIDE_COLOR_SLOTS))
