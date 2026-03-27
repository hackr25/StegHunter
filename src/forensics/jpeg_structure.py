"""
JPEG Structure Parser for StegHunter.

Parses raw JPEG binary stream to extract all markers, their offsets,
and payload sizes. Critically detects any data appended after the
EOI marker — a classic steganography embedding technique.
"""
from __future__ import annotations

import struct
from pathlib import Path
from typing import List, Dict, Any


# All standard JPEG markers
JPEG_MARKERS: dict[int, str] = {
    0xFFD8: "SOI  (Start of Image)",
    0xFFD9: "EOI  (End of Image)",
    0xFFE0: "APP0 (JFIF Header)",
    0xFFE1: "APP1 (EXIF / XMP)",
    0xFFE2: "APP2 (ICC Profile)",
    0xFFE3: "APP3",
    0xFFE4: "APP4",
    0xFFE5: "APP5",
    0xFFE6: "APP6",
    0xFFE7: "APP7",
    0xFFE8: "APP8",
    0xFFE9: "APP9",
    0xFFEA: "APP10",
    0xFFEB: "APP11",
    0xFFEC: "APP12",
    0xFFED: "APP13 (IPTC / Photoshop)",
    0xFFEE: "APP14 (Adobe DCT)",
    0xFFEF: "APP15",
    0xFFDB: "DQT  (Quantization Table)",
    0xFFC0: "SOF0 (Baseline DCT)",
    0xFFC1: "SOF1 (Extended Sequential)",
    0xFFC2: "SOF2 (Progressive DCT)",
    0xFFC3: "SOF3 (Lossless)",
    0xFFC4: "DHT  (Huffman Table)",
    0xFFCC: "DAC  (Arithmetic Coding)",
    0xFFDA: "SOS  (Start of Scan)",
    0xFFDD: "DRI  (Restart Interval)",
    0xFFD0: "RST0", 0xFFD1: "RST1", 0xFFD2: "RST2", 0xFFD3: "RST3",
    0xFFD4: "RST4", 0xFFD5: "RST5", 0xFFD6: "RST6", 0xFFD7: "RST7",
    0xFFFE: "COM  (Comment)",
}

# Markers with no length field
NO_LENGTH_MARKERS: frozenset[int] = frozenset({
    0xFFD8, 0xFFD9,
    0xFFD0, 0xFFD1, 0xFFD2, 0xFFD3,
    0xFFD4, 0xFFD5, 0xFFD6, 0xFFD7,
})

# Known steganography tool signatures embedded in JPEG files
STEGO_TOOL_SIGNATURES: list[tuple[bytes, str]] = [
    (b"OutGuess",    "OutGuess"),
    (b"outguess",    "OutGuess"),
    (b"Steghide",    "Steghide"),
    (b"steghide",    "Steghide"),
    (b"OpenStego",   "OpenStego"),
    (b"openstego",   "OpenStego"),
    (b"SilentEye",   "SilentEye"),
    (b"silenteye",   "SilentEye"),
    (b"F5Stego",     "F5"),
    (b"JPEG Stego",  "JPEG Stego"),
    (b"JSteg",       "JSteg"),
    (b"jsteg",       "JSteg"),
    (b"Camouflage",  "Camouflage"),
    (b"Hide4PGP",    "Hide4PGP"),
]


class JPEGStructureParser:
    """
    Parses the binary structure of a JPEG file.

    Usage
    -----
    parser = JPEGStructureParser()
    result = parser.parse("image.jpg")
    """

    def parse(self, filepath: str | Path) -> dict:
        """
        Parse the JPEG file and return a full structure report.

        Returns
        -------
        dict with keys:
            is_valid_jpeg       : bool
            markers             : list of marker dicts
            appended_bytes      : int  (bytes after EOI — suspicious if > 0)
            appended_data       : bytes | None
            stego_tool_found    : str | None
            dqt_tables          : list of quantization tables (64 ints each)
            comment_data        : list of embedded comment strings
            suspicious          : bool
            suspicion_score     : float (0–100)
            suspicion_reasons   : list[str]
        """
        path = Path(filepath)
        data = path.read_bytes()

        result: dict[str, Any] = {
            "is_valid_jpeg": False,
            "markers": [],
            "appended_bytes": 0,
            "appended_data": None,
            "stego_tool_found": None,
            "dqt_tables": [],
            "comment_data": [],
            "suspicious": False,
            "suspicion_score": 0.0,
            "suspicion_reasons": [],
        }

        # Must start with SOI 0xFFD8
        if len(data) < 2 or data[0] != 0xFF or data[1] != 0xD8:
            result["suspicion_reasons"].append("File does not start with JPEG SOI marker")
            result["suspicion_score"] = 30.0
            return result

        result["is_valid_jpeg"] = True
        markers = []
        eoi_offset: int | None = None
        i = 0

        while i < len(data) - 1:
            if data[i] != 0xFF:
                i += 1
                continue

            # Skip fill bytes (0xFF 0xFF ...)
            while i < len(data) - 1 and data[i + 1] == 0xFF:
                i += 1

            if i >= len(data) - 1:
                break

            marker_code = (data[i] << 8) | data[i + 1]
            marker_name = JPEG_MARKERS.get(marker_code, f"UNK_{marker_code:04X}")
            offset = i

            if marker_code in NO_LENGTH_MARKERS:
                payload_size = 0
                payload = b""
                i += 2
            else:
                if i + 3 >= len(data):
                    break
                try:
                    length = struct.unpack(">H", data[i + 2: i + 4])[0]
                except struct.error:
                    break
                # length field includes the 2 length bytes themselves
                payload_size = max(0, length - 2)
                payload_start = i + 4
                payload_end = payload_start + payload_size
                payload = data[payload_start:payload_end]
                i += 2 + length

            markers.append({
                "marker": marker_name,
                "code": f"0x{marker_code:04X}",
                "offset": offset,
                "payload_size": payload_size,
            })

            # Record EOI position
            if marker_code == 0xFFD9:
                eoi_offset = offset
                break  # nothing meaningful after EOI in a valid JPEG

            # Extract DQT tables
            if marker_code == 0xFFDB and payload:
                tables = self._parse_dqt(payload)
                result["dqt_tables"].extend(tables)

            # Extract comment text
            if marker_code == 0xFFFE and payload:
                try:
                    result["comment_data"].append(payload.decode("utf-8", errors="replace"))
                except Exception:
                    pass

        result["markers"] = markers

        # Check for appended data after EOI
        if eoi_offset is not None:
            eoi_end = eoi_offset + 2
            if eoi_end < len(data):
                appended = data[eoi_end:]
                result["appended_bytes"] = len(appended)
                result["appended_data"] = appended[:256]  # first 256 bytes for inspection

        # Scan entire file for steganography tool signatures
        for signature, tool_name in STEGO_TOOL_SIGNATURES:
            if signature in data:
                result["stego_tool_found"] = tool_name
                break

        # Build suspicion score
        score = 0.0
        reasons = []

        if result["appended_bytes"] > 0:
            score += 50.0
            reasons.append(
                f"Data appended after EOI marker: {result['appended_bytes']} bytes"
            )

        if result["stego_tool_found"]:
            score += 40.0
            reasons.append(
                f"Steganography tool signature detected: {result['stego_tool_found']}"
            )

        if result["comment_data"]:
            score += 5.0
            reasons.append(
                f"JPEG comment field present: {len(result['comment_data'])} comment(s)"
            )

        # Unusual number of DQT tables (normal JPEG has 2–4)
        if len(result["dqt_tables"]) > 4:
            score += 10.0
            reasons.append(
                f"Unusual number of quantization tables: {len(result['dqt_tables'])}"
            )

        result["suspicion_score"] = round(min(100.0, score), 2)
        result["suspicion_reasons"] = reasons
        result["suspicious"] = score > 0

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_dqt(self, payload: bytes) -> list[list[int]]:
        """Extract quantization tables from a DQT payload."""
        tables = []
        i = 0
        while i < len(payload):
            if i >= len(payload):
                break
            precision_and_id = payload[i]
            precision = (precision_and_id >> 4) & 0xF  # 0=8-bit, 1=16-bit
            i += 1
            entry_size = 2 if precision == 1 else 1
            table_len = 64
            if i + table_len * entry_size > len(payload):
                break
            table = []
            for _ in range(table_len):
                if entry_size == 2:
                    val = struct.unpack(">H", payload[i: i + 2])[0]
                else:
                    val = payload[i]
                table.append(val)
                i += entry_size
            tables.append(table)
        return tables

    def format_report(self, result: dict) -> str:
        """Return a human-readable text summary of the parse result."""
        lines = []
        lines.append("=" * 60)
        lines.append("JPEG STRUCTURE REPORT")
        lines.append("=" * 60)
        lines.append(f"Valid JPEG     : {result['is_valid_jpeg']}")
        lines.append(f"Total Markers  : {len(result['markers'])}")
        lines.append(f"DQT Tables     : {len(result['dqt_tables'])}")
        lines.append(f"Appended Bytes : {result['appended_bytes']}")
        lines.append(f"Stego Tool     : {result['stego_tool_found'] or 'None detected'}")
        lines.append(f"Suspicion Score: {result['suspicion_score']}/100")
        lines.append("")
        lines.append("MARKERS:")
        lines.append(f"  {'Offset':>10}  {'Code':>6}  {'Size':>8}  Name")
        lines.append(f"  {'-'*10}  {'-'*6}  {'-'*8}  {'-'*30}")
        for m in result["markers"]:
            lines.append(
                f"  {m['offset']:>10}  {m['code']:>6}  "
                f"{m['payload_size']:>8}  {m['marker']}"
            )
        if result["suspicion_reasons"]:
            lines.append("")
            lines.append("SUSPICION FLAGS:")
            for r in result["suspicion_reasons"]:
                lines.append(f"  ⚠  {r}")
        lines.append("=" * 60)
        return "\n".join(lines)