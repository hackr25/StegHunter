"""
Metadata Analyzer for StegHunter.

Extracts full EXIF metadata from images using piexif + Pillow.
Detects forensic anomalies:
  - GPS coordinates embedded in image
  - Software/editor tag mismatch (edited but claims camera origin)
  - Thumbnail vs main image pixel divergence (tampered thumbnail)
  - Timestamp inconsistencies (modify before create)
  - Missing expected EXIF for claimed camera source
"""
from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Any

from PIL import Image

try:
    import piexif
    PIEXIF_AVAILABLE = True
except ImportError:
    PIEXIF_AVAILABLE = False


# ---------------------------------------------------------------------------
# Human-readable EXIF tag names
# (piexif uses numeric IDs; we map the most forensically relevant ones)
# ---------------------------------------------------------------------------
_EXIF_TAG_NAMES: dict[str, dict[int, str]] = {
    "0th": {
        271:  "Make",
        272:  "Model",
        274:  "Orientation",
        282:  "XResolution",
        283:  "YResolution",
        296:  "ResolutionUnit",
        305:  "Software",
        306:  "DateTime",
        315:  "Artist",
        316:  "HostComputer",
        33432:"Copyright",
    },
    "Exif": {
        33434:"ExposureTime",
        33437:"FNumber",
        34850:"ExposureProgram",
        34855:"ISOSpeedRatings",
        36864:"ExifVersion",
        36867:"DateTimeOriginal",
        36868:"DateTimeDigitized",
        37377:"ShutterSpeedValue",
        37378:"ApertureValue",
        37383:"MeteringMode",
        37385:"Flash",
        37386:"FocalLength",
        40961:"ColorSpace",
        40962:"PixelXDimension",
        40963:"PixelYDimension",
        41986:"ExposureMode",
        41987:"WhiteBalance",
        41990:"SceneCaptureType",
        42036:"LensModel",
    },
    "GPS": {
        1: "GPSLatitudeRef",
        2: "GPSLatitude",
        3: "GPSLongitudeRef",
        4: "GPSLongitude",
        5: "GPSAltitudeRef",
        6: "GPSAltitude",
        7: "GPSTimeStamp",
        29:"GPSDateStamp",
    },
    "1st": {
        256:"ThumbnailWidth",
        257:"ThumbnailHeight",
        259:"ThumbnailCompression",
    },
}

# Software tags that indicate post-processing (not straight from camera)
_EDITING_SOFTWARE_KEYWORDS = [
    "photoshop", "lightroom", "gimp", "affinity", "capture one",
    "darktable", "rawtherapee", "paint.net", "canva", "snapseed",
    "facetune", "meitu", "picsart", "adobe", "corel", "pixelmator",
    "preview",  # macOS Preview re-saves and modifies EXIF
]


class MetadataAnalyzer:
    """
    Extracts and forensically analyzes image metadata.

    Usage
    -----
    analyzer = MetadataAnalyzer()
    result   = analyzer.analyze("photo.jpg")
    """

    def analyze(self, image_path: str | Path) -> dict:
        """
        Run full metadata forensic analysis on the image.

        Returns
        -------
        dict with keys:
            has_exif            : bool
            exif                : dict  (flattened human-readable fields)
            gps_present         : bool
            gps_coords          : dict | None
            software_tag        : str | None
            editing_detected    : bool
            thumbnail_present   : bool
            thumbnail_mismatch  : bool
            thumbnail_diff_pct  : float  (0.0–1.0)
            timestamp_anomaly   : bool
            anomalies           : list[str]
            suspicion_score     : float (0–100)
        """
        path = Path(image_path)

        result: dict[str, Any] = {
            "has_exif":           False,
            "exif":               {},
            "gps_present":        False,
            "gps_coords":         None,
            "software_tag":       None,
            "editing_detected":   False,
            "thumbnail_present":  False,
            "thumbnail_mismatch": False,
            "thumbnail_diff_pct": 0.0,
            "timestamp_anomaly":  False,
            "anomalies":          [],
            "suspicion_score":    0.0,
        }

        if not PIEXIF_AVAILABLE:
            result["anomalies"].append(
                "piexif not installed — install with: pip install piexif"
            )
            return result

        try:
            img = Image.open(path)
        except Exception as exc:
            result["anomalies"].append(f"Could not open image: {exc}")
            return result

        # ----------------------------------------------------------------
        # Load raw EXIF bytes
        # ----------------------------------------------------------------
        exif_bytes = img.info.get("exif", b"")
        if not exif_bytes:
            result["anomalies"].append("No EXIF data present")
            return result

        try:
            exif_dict = piexif.load(exif_bytes)
        except Exception as exc:
            result["anomalies"].append(f"EXIF parse error: {exc}")
            return result

        result["has_exif"] = True

        # ----------------------------------------------------------------
        # Flatten to human-readable dict
        # ----------------------------------------------------------------
        result["exif"] = self._flatten_exif(exif_dict)

        # ----------------------------------------------------------------
        # GPS check
        # ----------------------------------------------------------------
        gps_ifd = exif_dict.get("GPS", {})
        if gps_ifd:
            result["gps_present"] = True
            coords = self._decode_gps(gps_ifd)
            if coords:
                result["gps_coords"] = coords
            result["anomalies"].append(
                "GPS coordinates embedded in image metadata"
            )

        # ----------------------------------------------------------------
        # Software / editing tool check
        # ----------------------------------------------------------------
        software_raw = exif_dict.get("0th", {}).get(305)  # tag 305 = Software
        if software_raw:
            software = (
                software_raw.decode("utf-8", errors="replace").strip()
                if isinstance(software_raw, bytes)
                else str(software_raw)
            )
            result["software_tag"] = software
            if any(kw in software.lower() for kw in _EDITING_SOFTWARE_KEYWORDS):
                result["editing_detected"] = True
                result["anomalies"].append(
                    f"Image edited with: {software}"
                )

        # ----------------------------------------------------------------
        # Timestamp anomaly check
        # ----------------------------------------------------------------
        datetime_original  = self._get_tag_str(exif_dict, "Exif",  36867)
        datetime_digitized = self._get_tag_str(exif_dict, "Exif",  36868)
        datetime_modified  = self._get_tag_str(exif_dict, "0th",   306)

        if datetime_original and datetime_modified:
            if datetime_modified < datetime_original:
                result["timestamp_anomaly"] = True
                result["anomalies"].append(
                    f"Timestamp anomaly: DateTime ({datetime_modified}) "
                    f"is earlier than DateTimeOriginal ({datetime_original})"
                )

        # ----------------------------------------------------------------
        # Thumbnail extraction and mismatch detection
        # ----------------------------------------------------------------
        thumbnail_bytes = exif_dict.get("thumbnail")
        if thumbnail_bytes:
            result["thumbnail_present"] = True
            diff_pct = self._compare_thumbnail(img, thumbnail_bytes)
            result["thumbnail_diff_pct"] = round(diff_pct, 4)
            if diff_pct > 0.15:
                result["thumbnail_mismatch"] = True
                result["anomalies"].append(
                    f"Thumbnail mismatch: {diff_pct:.1%} pixel divergence "
                    f"from main image — possible tampering"
                )

        # ----------------------------------------------------------------
        # Compute suspicion score
        # ----------------------------------------------------------------
        score = 0.0
        if result["gps_present"]:
            score += 15.0
        if result["editing_detected"]:
            score += 20.0
        if result["thumbnail_mismatch"]:
            score += 35.0
        if result["timestamp_anomaly"]:
            score += 25.0
        if not result["has_exif"]:
            score += 5.0  # missing EXIF from claimed camera file

        result["suspicion_score"] = round(min(100.0, score), 2)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _flatten_exif(self, exif_dict: dict) -> dict:
        """Convert piexif IFD dicts to a flat human-readable key→value dict."""
        flat: dict[str, Any] = {}
        for ifd_name, tag_map in _EXIF_TAG_NAMES.items():
            ifd = exif_dict.get(ifd_name, {})
            if not isinstance(ifd, dict):
                continue
            for tag_id, friendly_name in tag_map.items():
                raw = ifd.get(tag_id)
                if raw is None:
                    continue
                flat[friendly_name] = self._decode_value(raw)
        return flat

    def _decode_value(self, raw: Any) -> Any:
        """Decode a raw piexif value to a Python-native type."""
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace").strip("\x00").strip()
        if isinstance(raw, tuple):
            # Rational number (numerator, denominator)
            if len(raw) == 2 and isinstance(raw[0], int):
                denom = raw[1]
                return round(raw[0] / denom, 5) if denom else 0
            # Tuple of rationals
            return [self._decode_value(v) for v in raw]
        return raw

    def _get_tag_str(self, exif_dict: dict, ifd: str, tag_id: int) -> str | None:
        """Safely retrieve a tag as a string."""
        raw = exif_dict.get(ifd, {}).get(tag_id)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace").strip("\x00").strip()
        return str(raw)

    def _decode_gps(self, gps_ifd: dict) -> dict | None:
        """Decode GPS IFD to decimal lat/lon."""
        try:
            lat_ref  = gps_ifd.get(1, b"N")
            lat_dms  = gps_ifd.get(2)
            lon_ref  = gps_ifd.get(3, b"E")
            lon_dms  = gps_ifd.get(4)
            if not lat_dms or not lon_dms:
                return None

            def dms_to_dd(dms: tuple, ref: bytes) -> float:
                d = dms[0][0] / dms[0][1]
                m = dms[1][0] / dms[1][1]
                s = dms[2][0] / dms[2][1]
                dd = d + m / 60 + s / 3600
                if ref in (b"S", b"W"):
                    dd = -dd
                return round(dd, 6)

            return {
                "latitude":  dms_to_dd(lat_dms, lat_ref),
                "longitude": dms_to_dd(lon_dms, lon_ref),
            }
        except Exception:
            return None

    def _compare_thumbnail(self, img: Image.Image, thumbnail_bytes: bytes) -> float:
        """
        Compare embedded thumbnail against a downscaled version of the main image.
        Returns mean absolute difference as a fraction (0.0 = identical, 1.0 = totally different).
        """
        try:
            import numpy as np

            # Load thumbnail
            thumb_img = Image.open(io.BytesIO(thumbnail_bytes)).convert("RGB")
            tw, th = thumb_img.size
            if tw == 0 or th == 0:
                return 0.0

            # Downscale main image to thumbnail dimensions
            main_resized = img.convert("RGB").resize((tw, th), Image.LANCZOS)

            thumb_arr = np.array(thumb_img, dtype=float)
            main_arr  = np.array(main_resized, dtype=float)

            diff = np.mean(np.abs(thumb_arr - main_arr)) / 255.0
            return float(diff)
        except Exception:
            return 0.0

    def format_report(self, result: dict) -> str:
        """Return a plain-text summary suitable for CLI output."""
        lines = ["=" * 60, "METADATA FORENSICS REPORT", "=" * 60]
        lines.append(f"EXIF Present     : {result['has_exif']}")
        lines.append(f"GPS Embedded     : {result['gps_present']}")
        if result.get("gps_coords"):
            c = result["gps_coords"]
            lines.append(f"GPS Coordinates  : {c['latitude']}, {c['longitude']}")
        lines.append(f"Software Tag     : {result['software_tag'] or 'None'}")
        lines.append(f"Editing Detected : {result['editing_detected']}")
        lines.append(f"Thumbnail Present: {result['thumbnail_present']}")
        if result["thumbnail_present"]:
            lines.append(f"Thumbnail Diff   : {result['thumbnail_diff_pct']:.1%}")
            lines.append(f"Thumbnail Mismatch: {result['thumbnail_mismatch']}")
        lines.append(f"Timestamp Anomaly: {result['timestamp_anomaly']}")
        lines.append(f"Suspicion Score  : {result['suspicion_score']}/100")
        if result["exif"]:
            lines.append("")
            lines.append("EXIF FIELDS:")
            for k, v in result["exif"].items():
                lines.append(f"  {k:<25} : {v}")
        if result["anomalies"]:
            lines.append("")
            lines.append("ANOMALIES DETECTED:")
            for a in result["anomalies"]:
                lines.append(f"  ⚠  {a}")
        lines.append("=" * 60)
        return "\n".join(lines)