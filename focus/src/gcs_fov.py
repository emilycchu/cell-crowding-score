"""Resolve (sample_id, fov_id, country) to its raw DPC image across three GCS buckets and
load it.

All three buckets store FOVs the same way: a per-slide folder containing
dpc-<fov_id:03d>-<slide-folder-name>.png (already grayscale uint8, 2800x2800):
  - LB: gs://liberia-2025/processedData4SS/LB25-<batch>/<folder>/ -- folder name doesn't
    match sample_id exactly (punctuation varies slide to slide), so it's located the same
    way fluorescence/src/gcs_fov.py locates the raw _Blue folder: by the unique
    <date>-<time>-<numeric_id> substring, just under processedData4SS instead of
    rawData4SS/*_Blue (and with no suffix filter -- processedData4SS folders aren't named
    with a channel suffix).
  - TZ: gs://tanzania_02032026/TZ2025-Box<1-5>/<sample_id>/ -- box isn't knowable from the
    sample_id alone, so each box is checked in turn (only 5 exist, confirmed by listing the
    bucket root).
  - UG: gs://malaria-annotation-web/samples/<sample_id>/data/ -- direct, no lookup needed.

Reuses fluorescence/src/gcs_fov.py's parse_sample_id (a pure sample_id regex parser with no
project-specific dependencies) via a direct file-path import, rather than re-deriving that
regex. The actual gs:// blob download+decode step is a ~10-line helper, reimplemented
locally below rather than importing crowding-crenation/src/pipeline.py's version of the same
thing -- that module's relative imports pull in its whole composite/features/segmentation
stack (and scipy/skimage) just to reach one small function, and every sibling project
(including this one) names its package `src`, which collides in Python's module cache if
more than one gets imported by path into the same process.
"""
import importlib.util
import re
import threading
from pathlib import Path

import cv2
import numpy as np

_FLUORESCENCE_GCS_FOV = Path(__file__).resolve().parent.parent.parent / "fluorescence" / "src" / "gcs_fov.py"


def _load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parse_sample_id = _load_module_from_path("_fluorescence_gcs_fov", _FLUORESCENCE_GCS_FOV).parse_sample_id

LB_BUCKET = "liberia-2025"
TZ_BUCKET = "tanzania_02032026"
UG_BUCKET = "malaria-annotation-web"
TZ_BOXES = range(1, 6)  # TZ2025-Box1..Box5 -- confirmed to be the full set in the bucket

_client_local = threading.local()


def _client():
    client = getattr(_client_local, "client", None)
    if client is None:
        from google.cloud import storage

        client = storage.Client()
        _client_local.client = client
    return client


def _download_gray(bucket, blob_name):
    data = _client().bucket(bucket).blob(blob_name).download_as_bytes()
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Could not decode image: gs://{bucket}/{blob_name}")
    return image


def find_slide_dpc_folder(sample_id, bucket=LB_BUCKET):
    """Locate an LB slide's processedData4SS folder by its unique <date>-<time>-<id>
    substring (folder punctuation isn't reconstructible from sample_id alone -- see module
    docstring).
    """
    batch, date, time, numeric_id = parse_sample_id(sample_id)
    needle = f"{date}-{time}-{numeric_id}"
    prefix = f"processedData4SS/LB25-{batch}/"
    client = _client()
    it = client.list_blobs(bucket, prefix=prefix, delimiter="/")
    list(it)  # populate .prefixes
    matches = [p for p in it.prefixes if needle in p]
    if not matches:
        raise FileNotFoundError(f"No processedData4SS folder found for {sample_id!r} under {prefix}")
    if len(matches) > 1:
        raise RuntimeError(f"Ambiguous processedData4SS folder match for {sample_id!r}: {matches}")
    return matches[0]


def find_tz_box(sample_id, bucket=TZ_BUCKET):
    """Find which TZ2025-Box<N> folder holds this sample_id."""
    client = _client()
    for box in TZ_BOXES:
        prefix = f"TZ2025-Box{box}/{sample_id}/"
        if next(iter(client.list_blobs(bucket, prefix=prefix, max_results=1)), None) is not None:
            return f"TZ2025-Box{box}"
    raise FileNotFoundError(f"No TZ2025-Box<N> folder found containing sample {sample_id!r}")


def resolve_fov_blob_name(sample_id, fov_id, country):
    """Return (bucket, blob_name) for one labeled FOV's dpc-*.png image."""
    country = country.upper()
    if country == "LB":
        folder = find_slide_dpc_folder(sample_id)
        folder_name = folder.rstrip("/").rsplit("/", 1)[-1]
        return LB_BUCKET, f"{folder}dpc-{fov_id:03d}-{folder_name}.png"
    if country == "TZ":
        box = find_tz_box(sample_id)
        return TZ_BUCKET, f"{box}/{sample_id}/dpc-{fov_id:03d}-{sample_id}.png"
    if country == "UG":
        return UG_BUCKET, f"samples/{sample_id}/data/dpc-{fov_id:03d}-{sample_id}.png"
    raise ValueError(f"Unknown country code: {country!r}")


def load_fov_image(sample_id, fov_id, country):
    """Download and decode the raw DPC image for one labeled FOV. Returns (image, blob_uri)."""
    bucket, blob_name = resolve_fov_blob_name(sample_id, fov_id, country)
    image = _download_gray(bucket, blob_name)
    return image, f"gs://{bucket}/{blob_name}"


def local_cache_name(sample_id, fov_id):
    """Filesystem-safe cache filename for a labeled FOV."""
    safe_sample = re.sub(r"[^A-Za-z0-9_.-]", "_", sample_id)
    return f"{safe_sample}__fov{fov_id}.png"
