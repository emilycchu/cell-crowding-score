"""Build a result-summary grid image: same row/column layout as initial-dataset-visual.png,
with FOV ids, slide ids, and per-technique results dropped into the matching boxes.

Columns whose name ends in "_pct" are rendered as a percentage; any other column
is rendered as a raw value (2 decimal places) -- use this for metrics like GLCM
contrast that aren't naturally a 0-100% quantity.

Usage:
    python scripts/build_result_summary.py \
        data/labels/initial-dataset-071626/fovs.csv \
        data/results/initial-dataset-071626/initial-result-summary.png \
        --metric coverage:data/results/initial-dataset-071626/otsu.csv:coverage_pct \
        --metric "glcm contrast":data/results/initial-dataset-071626/glcm-contrast.csv:glcm_contrast
"""
import argparse
import csv
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROW_ORDER = ["no rouleaux", "slight rouleaux", "some rouleaux", "rouleaux", "heavy rouleaux"]
COL_ORDER = ["monolayer", "slightly dense", "dense", "very dense"]

ROW_LABEL_W = 150
HEADER_H = 60
LINE_H = 20
BOX_PAD_V = 10
BOX_PAD_H = 12
BOX_GAP = 16
CELL_PAD = 20
CRENATED_LABEL_H = 22

LIBERIA_SLIDE_RE = re.compile(r"(LB-D\d+)-(\d{4}-\d{2}-\d{2})")


def load_fonts():
    try:
        header_font = ImageFont.truetype("arial.ttf", 20)
        box_font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arialbd.ttf", 14)
    except OSError:
        header_font = box_font = small_font = ImageFont.load_default()
    return header_font, box_font, small_font


def load_fovs(fovs_csv):
    with open(fovs_csv, newline="") as f:
        return list(csv.DictReader(f))


def load_metric_csv(path):
    with open(path, newline="") as f:
        return {row["filename"]: row for row in csv.DictReader(f)}


def parse_metric_specs(specs):
    metrics = []
    for spec in specs:
        label, path, column = spec.rsplit(":", 2)
        metrics.append((label, load_metric_csv(path), column))
    return metrics


def abbreviate_slide_id(row):
    slide_id = row["slide_id"]
    if row["country"] == "liberia":
        match = LIBERIA_SLIDE_RE.match(slide_id)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
    return slide_id


def build_grid(fovs, metrics):
    grid = {(r, c): [] for r in ROW_ORDER for c in COL_ORDER}
    for row in fovs:
        key = (row["overlap"], row["density"])
        if key not in grid:
            raise ValueError(f"Unexpected overlap/density combo: {key} for {row['filename']}")

        metric_values = []
        for label, values_by_filename, column in metrics:
            values = values_by_filename.get(row["filename"])
            if values is None:
                raise ValueError(f"No {label} result found for {row['filename']}")
            metric_values.append((label, float(values[column]), column.endswith("_pct")))

        grid[key].append(
            {
                "fov": row["fov"],
                "slide": abbreviate_slide_id(row),
                "crenated": row["crenated"].strip().lower() == "yes",
                "metrics": metric_values,
            }
        )
    return grid


def max_items_per_cell(grid):
    return max((len(items) for items in grid.values()), default=1) or 1


def box_height(n_metrics):
    n_lines = 2 + n_metrics  # FOV id, slide id, one line per metric
    return n_lines * LINE_H + 2 * BOX_PAD_V


def format_metric(label, value, is_pct):
    return f"{value:.1f}% {label}" if is_pct else f"{value:.2f} {label}"


def item_lines(item):
    lines = [f"FOV {item['fov']}", item["slide"]]
    lines += [format_metric(label, value, is_pct) for label, value, is_pct in item["metrics"]]
    return lines


def measure_box_width(grid, box_font):
    scratch = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    max_line_w = 0
    for items in grid.values():
        for item in items:
            for line in item_lines(item):
                max_line_w = max(max_line_w, scratch.textlength(line, font=box_font))
    return int(max_line_w) + 2 * BOX_PAD_H


def draw_box(draw, x, y, item, box_w, box_h, box_font, small_font):
    draw.rectangle([x, y, x + box_w, y + box_h], outline="black", width=1)

    text_y = y + BOX_PAD_V
    for line in item_lines(item):
        draw.text((x + box_w / 2, text_y), line, font=box_font, fill="black", anchor="mt")
        text_y += LINE_H

    if item["crenated"]:
        draw.text(
            (x + box_w / 2, y + box_h + 4),
            "crenated",
            font=small_font,
            fill="red",
            anchor="mt",
        )


def render(grid, n_metrics, out_path):
    header_font, box_font, small_font = load_fonts()
    n_items = max_items_per_cell(grid)
    box_h = box_height(n_metrics)
    box_w = measure_box_width(grid, box_font)

    cell_w = n_items * box_w + (n_items - 1) * BOX_GAP + 2 * CELL_PAD
    cell_h = box_h + CRENATED_LABEL_H + 2 * CELL_PAD

    width = ROW_LABEL_W + len(COL_ORDER) * cell_w
    height = HEADER_H + len(ROW_ORDER) * cell_h

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    for c, col_name in enumerate(COL_ORDER):
        cx = ROW_LABEL_W + c * cell_w + cell_w / 2
        draw.text((cx, HEADER_H / 2), col_name, font=header_font, fill="black", anchor="mm")

    for r, row_name in enumerate(ROW_ORDER):
        ry = HEADER_H + r * cell_h + cell_h / 2
        draw.text((ROW_LABEL_W / 2, ry), row_name, font=header_font, fill="black", anchor="mm")

    draw.line([(ROW_LABEL_W, 0), (ROW_LABEL_W, height)], fill="black", width=2)
    draw.line([(0, HEADER_H), (width, HEADER_H)], fill="black", width=2)
    for r in range(1, len(ROW_ORDER)):
        y = HEADER_H + r * cell_h
        draw.line([(0, y), (width, y)], fill="lightgray", width=1)
    for c in range(1, len(COL_ORDER)):
        x = ROW_LABEL_W + c * cell_w
        draw.line([(x, 0), (x, height)], fill="lightgray", width=1)

    for r, row_name in enumerate(ROW_ORDER):
        for c, col_name in enumerate(COL_ORDER):
            items = grid[(row_name, col_name)]
            cell_x0 = ROW_LABEL_W + c * cell_w + CELL_PAD
            cell_y0 = HEADER_H + r * cell_h + CELL_PAD
            for i, item in enumerate(items):
                x = cell_x0 + i * (box_w + BOX_GAP)
                y = cell_y0
                draw_box(draw, x, y, item, box_w, box_h, box_font, small_font)

    img.save(out_path)


def main():
    parser = argparse.ArgumentParser(description="Build the result-summary grid image.")
    parser.add_argument("fovs_csv")
    parser.add_argument("output_png")
    parser.add_argument(
        "--metric",
        action="append",
        required=True,
        dest="metrics",
        help="label:csv_path:column, repeatable (e.g. coverage:otsu.csv:coverage_pct)",
    )
    args = parser.parse_args()

    fovs = load_fovs(args.fovs_csv)
    metrics = parse_metric_specs(args.metrics)
    grid = build_grid(fovs, metrics)
    render(grid, len(metrics), args.output_png)
    print(f"Wrote result summary to {args.output_png}")


if __name__ == "__main__":
    main()
