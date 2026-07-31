"""Resolve a (sample_id, fov_id) pair from data/labels/*.csv to its raw fluorescence
(Blue-channel) image in gs://liberia-2025, and load it.

Only raw scan acquisition metadata (Scan.txt, written by the scanner itself) and the raw
per-tile images it references are used here -- nothing under detection_results/ or any
other precomputed-model output in the bucket is read. That keeps this a "first thing you
preprocess after imaging" step rather than something downstream of Cellpose/detector runs.

Sample IDs encode the scan folder name with punctuation stripped, e.g.:
    LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4
      -> rawData4SS/LB25-D10/2025-12-29/2025-12-29-150312-0171084-(VFPCHC)-+2.4_Blue

Folder punctuation ((), +, .) isn't always reconstructible from the sample_id alone (it's
inconsistent across slides), so slides are matched by locating the "_Blue" folder under the
right batch/date whose name contains the sample's <date>-<time>-<numeric id> segment --
that numeric id is unique enough to make this unambiguous.

fov_id does not index the slide's own saved-tile grid directly. Per-slide Scan.txt reports
RowCount/ColumnCount for the tiles actually saved (e.g. 10x13=130), but fov_id is addressed
into a fixed-width virtual raster with a column stride of 18 (confirmed against every slide
in this dataset -- slides with ColumnCount=18 decode directly, and the one slide with
ColumnCount=13 only produces in-bounds rows when decoded with stride 18, matching the other
slides scanned by the same instrument). So:
    col = ((fov_id - 1) % 18) + 1
    row = ((fov_id - 1) // 18) + 1
mapping to the tile file IMG<row>x<col>.bmp (zero-padded per Scan.txt's ImageIndexWidth).
"""
import re
import threading
from pathlib import PurePosixPath

import cv2
import numpy as np

BUCKET = "liberia-2025"
RASTER_COL_STRIDE = 18  # virtual raster width fov_id is addressed into; see module docstring

_SAMPLE_ID_RE = re.compile(
    r"^LB-(?P<batch>D\d+)-(?P<date>\d{4}-\d{2}-\d{2})-(?P<time>\d{6})-(?P<id>\d+)"
)

_client_local = threading.local()


def _client():
    client = getattr(_client_local, "client", None)
    if client is None:
        from google.cloud import storage

        client = storage.Client()
        _client_local.client = client
    return client


def parse_sample_id(sample_id):
    """Pull (batch, date, time, numeric_id) out of a sample_id like
    'LB-D10-2025-12-29-150312-0171084-VFPCHC-2-4'.
    """
    m = _SAMPLE_ID_RE.match(sample_id)
    if not m:
        raise ValueError(f"sample_id does not match the expected LB-<batch>-... format: {sample_id!r}")
    return m.group("batch"), m.group("date"), m.group("time"), m.group("id")


def find_slide_blue_folder(sample_id, bucket=BUCKET):
    """Locate the '_Blue' scan folder for a sample_id by matching its <date>-<time>-<id>
    segment against folder names under the batch/date prefix (see module docstring for why
    substring matching, rather than reconstructing punctuation, is used).
    """
    batch, date, time, numeric_id = parse_sample_id(sample_id)
    needle = f"{date}-{time}-{numeric_id}"
    prefix = f"rawData4SS/LB25-{batch}/{date}/"
    client = _client()
    it = client.list_blobs(bucket, prefix=prefix, delimiter="/")
    list(it)  # populate .prefixes
    matches = [
        p for p in it.prefixes
        if needle in p and p.rstrip("/").endswith("_Blue")
    ]
    if not matches:
        raise FileNotFoundError(f"No '_Blue' folder found for {sample_id!r} under {prefix}")
    if len(matches) > 1:
        raise RuntimeError(f"Ambiguous '_Blue' folder match for {sample_id!r}: {matches}")
    return matches[0]


def _parse_scan_txt(text):
    fields = {}
    for line in text.splitlines():
        if "=" in line and not line.startswith("["):
            key, _, value = line.partition("=")
            fields[key.strip()] = value.strip()
    return fields


def read_scan_metadata(blue_folder, bucket=BUCKET):
    """Read RowCount/ColumnCount/ImageIndexWidth from the Blue-channel folder's own Scan.txt."""
    blob = _client().bucket(bucket).blob(f"{blue_folder.rstrip('/')}/Scan.txt")
    fields = _parse_scan_txt(blob.download_as_text())
    return {
        "row_count": int(fields["RowCount"]),
        "column_count": int(fields["ColumnCount"]),
        "index_width": int(fields.get("ImageIndexWidth", 3)),
    }


def fov_to_row_col(fov_id, row_count, column_count):
    """Decode a fov_id into (row, col) on the saved tile grid, both 1-indexed.

    Tries the slide's own column count first (right when it equals the raster stride),
    then falls back to the fixed raster stride -- whichever decode lands in-bounds for
    this slide's actual RowCount/ColumnCount is the correct one.
    """
    for stride in dict.fromkeys([column_count, RASTER_COL_STRIDE]):
        row = (fov_id - 1) // stride + 1
        col = (fov_id - 1) % stride + 1
        if 1 <= row <= row_count and 1 <= col <= column_count:
            return row, col
    raise ValueError(
        f"fov_id={fov_id} did not decode in-bounds for grid "
        f"{row_count}x{column_count} with strides {column_count} or {RASTER_COL_STRIDE}"
    )


def resolve_fov_blob_name(sample_id, fov_id, bucket=BUCKET):
    """Return the GCS blob name of the raw Blue-channel tile image for one labeled FOV."""
    blue_folder = find_slide_blue_folder(sample_id, bucket=bucket)
    meta = read_scan_metadata(blue_folder, bucket=bucket)
    row, col = fov_to_row_col(fov_id, meta["row_count"], meta["column_count"])
    w = meta["index_width"]
    filename = f"IMG{row:0{w}d}x{col:0{w}d}.bmp"
    return f"{blue_folder.rstrip('/')}/Images/{filename}"


def load_fov_image(sample_id, fov_id, bucket=BUCKET):
    """Download and decode the raw fluorescence (Blue-channel) image for one labeled FOV.

    Returns (image_bgr, blob_name).
    """
    blob_name = resolve_fov_blob_name(sample_id, fov_id, bucket=bucket)
    data = _client().bucket(bucket).blob(blob_name).download_as_bytes()
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not decode image: gs://{bucket}/{blob_name}")
    return image, blob_name


def local_cache_name(sample_id, fov_id):
    """Filesystem-safe cache filename for a labeled FOV."""
    safe_sample = re.sub(r"[^A-Za-z0-9_.-]", "_", sample_id)
    return f"{safe_sample}__fov{fov_id}.png"
