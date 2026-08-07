"""Resolve (sample_id, fov_id, country) to its raw fluorescence image across all three
labeled countries' GCS buckets, and load it -- no local disk caching.

LB already has its own tile-grid addressing (raw _Blue Scan.txt tiles, see gcs_fov.py) --
this delegates to that unchanged. TZ and UG both store the fluorescence channel directly as
fluorescent-<fov_id:03d>-<sample_id>.png under a per-sample folder (confirmed by listing the
buckets directly; the same layout focus/src/gcs_fov.py uses for its dpc-*.png files, just a
different filename prefix):
  - TZ: gs://tanzania_02032026/TZ2025-Box<1-5>/<sample_id>/fluorescent-<fov_id:03d>-<sample_id>.png
    (box isn't derivable from sample_id alone, so each of the 5 is checked in turn)
  - UG: gs://malaria-annotation-web/samples/<sample_id>/data/fluorescent-<fov_id:03d>-<sample_id>.png

Reuses focus/src/gcs_fov.py's find_tz_box (a bucket-agnostic box-finder with no heavy
transitive deps) via a direct file-path import rather than re-deriving the same box-probing
loop -- see the cross-project-imports convention this repo follows. Everything else here
(the actual byte download/decode) is new since it targets a different filename prefix than
focus's dpc-*.png.
"""
import importlib.util
import threading
from pathlib import Path

import cv2
import numpy as np

from src.gcs_fov import load_fov_image as _load_lb_fov_image

_FOCUS_GCS_FOV = Path(__file__).resolve().parent.parent.parent / "focus" / "src" / "gcs_fov.py"


def _load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


find_tz_box = _load_module_from_path("_focus_gcs_fov", _FOCUS_GCS_FOV).find_tz_box

TZ_BUCKET = "tanzania_02032026"
UG_BUCKET = "malaria-annotation-web"

_client_local = threading.local()

_COUNTRY_ALIASES = {
    "liberia": "lb", "lb": "lb",
    "tanzania": "tz", "tz": "tz",
    "uganda": "ug", "ug": "ug",
}


def _client():
    client = getattr(_client_local, "client", None)
    if client is None:
        from google.cloud import storage

        client = storage.Client()
        _client_local.client = client
    return client


def _download_color(bucket, blob_name):
    data = _client().bucket(bucket).blob(blob_name).download_as_bytes()
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not decode image: gs://{bucket}/{blob_name}")
    return image


def load_fov_image(sample_id, fov_id, country):
    """Download and decode one labeled FOV's raw fluorescence image, streamed directly from
    GCS (no disk cache). Returns (image_bgr, blob_uri).
    """
    key = _COUNTRY_ALIASES.get(country.strip().lower())
    if key is None:
        raise ValueError(f"Unknown country: {country!r}")

    if key == "lb":
        image, blob_name = _load_lb_fov_image(sample_id, fov_id)
        return image, f"gs://liberia-2025/{blob_name}"
    if key == "tz":
        box = find_tz_box(sample_id, bucket=TZ_BUCKET)
        blob_name = f"{box}/{sample_id}/fluorescent-{fov_id:03d}-{sample_id}.png"
        return _download_color(TZ_BUCKET, blob_name), f"gs://{TZ_BUCKET}/{blob_name}"
    if key == "ug":
        blob_name = f"samples/{sample_id}/data/fluorescent-{fov_id:03d}-{sample_id}.png"
        return _download_color(UG_BUCKET, blob_name), f"gs://{UG_BUCKET}/{blob_name}"
    raise AssertionError(key)  # unreachable, all _COUNTRY_ALIASES values handled above
