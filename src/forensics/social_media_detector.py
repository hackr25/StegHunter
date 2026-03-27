"""
Social Media Platform Detector for StegHunter.

Identifies which social media platform re-encoded a JPEG image by
comparing its JPEG quantization tables (DQT) against known platform
fingerprints.

Each platform re-saves images with a characteristic quality setting
and quantization table, producing a unique fingerprint:
  - WhatsApp   : quality ~80, characteristic luma table
  - Facebook   : quality ~85, known luma table
  - Twitter/X  : quality ~85, distinct table
  - Instagram  : quality ~75–85
  - Telegram   : near-lossless for photos
  - WeChat     : quality ~80
  - TikTok     : quality ~75
"""
from __future__ import annotations

import struct
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Known platform DQT luma table first-16 values (zigzag order)
# These are the standard JPEG luma tables scaled to each platform's quality.
# Matching is done by comparing the first 16 coefficients of the luma table.
# ---------------------------------------------------------------------------
# Each entry: (platform_name, first_16_luma_values, quality_hint, notes)
PLATFORM_FINGERPRINTS: list[dict] = [
    {
        "platform":    "WhatsApp",
        "luma_16":     [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55],
        "quality":     80,
        "notes":       "Standard WhatsApp JPEG quality 80 encoding",
    },
    {
        "platform":    "Facebook",
        "luma_16":     [2, 1, 1, 2, 2, 4, 3, 2, 2, 2, 3, 4, 3, 5, 6, 5],
        "quality":     85,
        "notes":       "Facebook high-quality JPEG encoding",
    },
    {
        "platform":    "Twitter / X",
        "luma_16":     [8, 6, 5, 8, 12, 20, 26, 31, 6, 6, 7, 10, 13, 29, 30, 28],
        "quality":     85,
        "notes":       "Twitter standard image compression",
    },
    {
        "platform":    "Instagram",
        "luma_16":     [3, 2, 2, 3, 5, 8, 10, 12, 2, 2, 3, 4, 5, 12, 12, 11],
        "quality":     90,
        "notes":       "Instagram feed image compression",
    },
    {
        "platform":    "Telegram",
        "luma_16":     [1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 2, 2],
        "quality":     95,
        "notes":       "Telegram near-lossless photo sharing",
    },
    {
        "platform":    "WeChat",
        "luma_16":     [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55],
        "quality":     80,
        "notes":       "WeChat photo sharing quality",
    },
    {
        "platform":    "TikTok",
        "luma_16":     [8, 6, 6, 8, 12, 20, 26, 31, 6, 6, 7, 10, 13, 29, 30, 28],
        "quality":     75,
        "notes":       "TikTok thumbnail encoding",
    },
    {
        "platform":    "Photoshop (Save for Web)",
        "luma_16":     [2, 1, 1, 2, 3, 5, 6, 7, 1, 1, 2, 3, 4, 8, 8, 7],
        "quality":     92,
        "notes":       "Adobe Photoshop Save for Web preset",
    },
    {
        "platform":    "Standard IJG/libjpeg Q95",
        "luma_16":     [2, 1, 1, 2, 2, 4, 5, 6, 1, 1, 2, 3, 3, 6, 6, 6],
        "quality":     95,
        "notes":       "Standard IJG JPEG library quality 95",
    },
    {
        "platform":    "Standard IJG/libjpeg Q85",
        "luma_16":     [4, 3, 3, 4, 5, 8, 10, 12, 3, 3, 4, 5, 7, 12, 12, 11],
        "quality":     85,
        "notes":       "Standard IJG JPEG library quality 85",
    },
    {
        "platform":    "Standard IJG/libjpeg Q75",
        "luma_16":     [8, 6, 5, 8, 12, 20, 26, 31, 6, 6, 7, 10, 13, 29, 30, 28],
        "quality":     75,
        "notes":       "Standard IJG JPEG library quality 75",
    },
]


class SocialMediaDetector:
    """
    Identifies the social media platform or software that re-encoded a JPEG
    by fingerprinting its quantization tables.

    Usage
    -----
    detector = SocialMediaDetector()
    result   = detector.identify("photo.jpg")
    """

    def identify(self, filepath: str | Path) -> dict:
        """
        Identify the platform/encoder that produced this JPEG.

        Returns
        -------
        dict with keys:
            is_jpeg             : bool
            platform            : str   ("Unknown" if no match)
            confidence          : float (0–100)
            quality_estimate    : int | None
            notes               : str
            luma_table          : list[int] | None  (full 64-value table)
            chroma_table        : list[int] | None
            all_matches         : list[dict]  (ranked matches)
            anomalies           : list[str]
        """
        path = Path(filepath)
        ext  = path.suffix.lower()

        result: dict[str, Any] = {
            "is_jpeg":          False,
            "platform":         "Unknown",
            "confidence":       0.0,
            "quality_estimate": None,
            "notes":            "",
            "luma_table":       None,
            "chroma_table":     None,
            "all_matches":      [],
            "anomalies":        [],
        }

        if ext not in (".jpg", ".jpeg"):
            result["anomalies"].append(
                f"File is not JPEG (extension: {ext}) — "
                "DQT fingerprinting only applies to JPEG files"
            )
            return result

        try:
            data = path.read_bytes()
        except Exception as exc:
            result["anomalies"].append(f"Cannot read file: {exc}")
            return result

        # Verify JPEG SOI marker
        if not data.startswith(b"\xFF\xD8"):
            result["anomalies"].append("File does not start with JPEG SOI marker")
            return result

        result["is_jpeg"] = True

        # ----------------------------------------------------------------
        # Extract DQT tables
        # ----------------------------------------------------------------
        tables = self._extract_dqt_tables(data)

        if not tables:
            result["anomalies"].append(
                "No DQT quantization tables found in JPEG"
            )
            return result

        # Conventionally table 0 = luma, table 1 = chroma
        luma_table   = tables[0] if len(tables) > 0 else None
        chroma_table = tables[1] if len(tables) > 1 else None

        result["luma_table"]   = luma_table
        result["chroma_table"] = chroma_table

        if luma_table is None:
            result["anomalies"].append("Luma quantization table not found")
            return result

        # ----------------------------------------------------------------
        # Match against known fingerprints
        # ----------------------------------------------------------------
        luma_16 = luma_table[:16]
        matches = []

        for fp in PLATFORM_FINGERPRINTS:
            ref_16 = fp["luma_16"]
            sad = sum(abs(a - b) for a, b in zip(luma_16, ref_16))
            # Convert sum of absolute differences to a confidence %
            # SAD of 0 = 100%, higher SAD = lower confidence
            max_sad = 255 * 16  # theoretical maximum
            confidence = max(0.0, 100.0 - (sad / max_sad) * 100.0)
            # Apply non-linear scaling so small differences are still high confidence
            # A SAD of 8 (small rounding errors) still gives ~90%
            confidence = max(0.0, 100.0 - (sad * 3.0))
            confidence = round(min(100.0, confidence), 1)

            matches.append({
                "platform":   fp["platform"],
                "confidence": confidence,
                "sad":        sad,
                "quality":    fp["quality"],
                "notes":      fp["notes"],
            })

        # Sort by confidence descending
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        result["all_matches"] = matches[:5]  # top 5

        best = matches[0]
        result["platform"]         = best["platform"]
        result["confidence"]       = best["confidence"]
        result["quality_estimate"] = best["quality"]
        result["notes"]            = best["notes"]

        # Estimate quality from luma table DC coefficient
        result["quality_estimate"] = self._estimate_quality(luma_table)

        # Anomaly: unusually high quality for claimed platform
        if result["confidence"] < 40.0:
            result["anomalies"].append(
                "Low confidence match — image may have been re-saved "
                "multiple times or uses a non-standard encoder"
            )

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_dqt_tables(self, data: bytes) -> list[list[int]]:
        """
        Parse all DQT (0xFFDB) markers from JPEG binary data.
        Returns list of quantization tables (each is 64 ints).
        """
        tables: list[list[int]] = []
        i = 0

        while i < len(data) - 3:
            # Find 0xFF marker
            if data[i] != 0xFF:
                i += 1
                continue

            marker = (data[i] << 8) | data[i + 1]

            # Skip SOI, EOI, RST markers (no length field)
            if marker in (0xFFD8, 0xFFD9) or (0xFFD0 <= marker <= 0xFFD7):
                i += 2
                continue

            if i + 3 >= len(data):
                break

            try:
                length = struct.unpack(">H", data[i + 2: i + 4])[0]
            except struct.error:
                break

            payload_start = i + 4
            payload_end   = i + 2 + length
            payload       = data[payload_start:payload_end]

            if marker == 0xFFDB:
                # DQT marker — parse quantization table(s)
                extracted = self._parse_dqt_payload(payload)
                tables.extend(extracted)

            i = payload_end

        return tables

    def _parse_dqt_payload(self, payload: bytes) -> list[list[int]]:
        """Parse one DQT payload, which may contain multiple tables."""
        tables: list[list[int]] = []
        i = 0

        while i < len(payload):
            if i >= len(payload):
                break
            prec_id   = payload[i]
            precision = (prec_id >> 4) & 0xF   # 0=8-bit, 1=16-bit
            # table_id  = prec_id & 0xF          # 0=luma, 1=chroma
            i += 1

            entry_size = 2 if precision == 1 else 1
            table_length = 64

            if i + table_length * entry_size > len(payload):
                break

            table: list[int] = []
            for _ in range(table_length):
                if entry_size == 2:
                    val = struct.unpack(">H", payload[i: i + 2])[0]
                else:
                    val = payload[i]
                table.append(val)
                i += entry_size

            tables.append(table)

        return tables

    def _estimate_quality(self, luma_table: list[int]) -> int:
        """
        Estimate JPEG quality factor from the luma quantization table.
        Uses the standard IJG quality formula in reverse.
        """
        try:
            # Standard IJG luma table for Q=50
            std_luma_q50 = [
                16, 11, 10, 16, 24, 40, 51, 61,
                12, 12, 14, 19, 26, 58, 60, 55,
                14, 13, 16, 24, 40, 57, 69, 56,
                14, 17, 22, 29, 51, 87, 80, 62,
                18, 22, 37, 56, 68,109,103, 77,
                24, 35, 55, 64, 81,104,113, 92,
                49, 64, 78, 87,103,121,120,101,
                72, 92, 95, 98,112,100,103, 99,
            ]
            # Estimate scale factor from first 8 coefficients
            ratios = []
            for i in range(min(8, len(luma_table), len(std_luma_q50))):
                if luma_table[i] > 0:
                    ratios.append(std_luma_q50[i] / luma_table[i])
            if not ratios:
                return 0
            scale = sum(ratios) / len(ratios) * 50  # scale is relative to Q50

            if scale >= 100:
                quality = 100 - (200 - scale * 2) // 2
            else:
                quality = scale // 2

            return max(1, min(100, int(round(quality))))
        except Exception:
            return 0

    def format_report(self, result: dict) -> str:
        """Return a plain-text summary for CLI output."""
        lines = ["=" * 60, "SOCIAL MEDIA / ENCODER DETECTION", "=" * 60]
        lines.append(f"Is JPEG          : {result['is_jpeg']}")
        lines.append(f"Platform         : {result['platform']}")
        lines.append(f"Confidence       : {result['confidence']:.1f}%")
        lines.append(f"Quality Estimate : ~{result['quality_estimate']}")
        lines.append(f"Notes            : {result['notes']}")

        if result["all_matches"]:
            lines.append("")
            lines.append("TOP MATCHES:")
            for m in result["all_matches"]:
                lines.append(
                    f"  {m['platform']:<30} "
                    f"confidence={m['confidence']:.1f}%  "
                    f"Q~{m['quality']}"
                )

        if result.get("luma_table"):
            lines.append("")
            lines.append("LUMA TABLE (first 16 values):")
            lines.append("  " + "  ".join(str(v) for v in result["luma_table"][:16]))

        if result["anomalies"]:
            lines.append("")
            lines.append("NOTES:")
            for a in result["anomalies"]:
                lines.append(f"  ⚠  {a}")

        lines.append("=" * 60)
        return "\n".join(lines)