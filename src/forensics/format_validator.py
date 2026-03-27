"""
Format Validator for StegHunter.

Validates image files at the binary level:
  1. Magic bytes vs file extension mismatch detection
  2. Known steganography tool binary signature scan
  3. Printable ASCII string extraction (like Unix `strings`)
  4. Suspicious embedded string detection (URLs, base64 blobs, passwords)
"""
from __future__ import annotations

import re
import string
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Magic byte signatures — maps leading bytes to valid extensions
# ---------------------------------------------------------------------------
MAGIC_SIGNATURES: list[tuple[bytes, list[str], str]] = [
    (b"\xFF\xD8\xFF",           [".jpg", ".jpeg"],          "JPEG"),
    (b"\x89PNG\r\n\x1a\n",     [".png"],                   "PNG"),
    (b"GIF87a",                 [".gif"],                   "GIF87"),
    (b"GIF89a",                 [".gif"],                   "GIF89"),
    (b"BM",                     [".bmp"],                   "BMP"),
    (b"II\x2a\x00",            [".tif", ".tiff"],          "TIFF-LE"),
    (b"MM\x00\x2a",            [".tif", ".tiff"],          "TIFF-BE"),
    (b"RIFF",                   [".webp"],                  "RIFF/WebP"),
    (b"\x00\x00\x01\x00",      [".ico"],                   "ICO"),
    (b"%PDF",                   [".pdf"],                   "PDF"),
    (b"PK\x03\x04",            [".zip", ".docx", ".xlsx"], "ZIP"),
    (b"\x1f\x8b",              [".gz"],                    "GZIP"),
    (b"Rar!\x1a\x07",          [".rar"],                   "RAR"),
    (b"\x7fELF",               [],                         "ELF Binary"),
    (b"MZ",                     [".exe", ".dll"],           "Windows PE"),
]

# ---------------------------------------------------------------------------
# Known steganography / hiding tool binary signatures
# ---------------------------------------------------------------------------
STEGO_TOOL_SIGNATURES: list[tuple[bytes, str]] = [
    (b"OutGuess",       "OutGuess"),
    (b"outguess",       "OutGuess"),
    (b"Steghide",       "Steghide"),
    (b"steghide",       "Steghide"),
    (b"OpenStego",      "OpenStego"),
    (b"openstego",      "OpenStego"),
    (b"SilentEye",      "SilentEye"),
    (b"silenteye",      "SilentEye"),
    (b"F5Stego",        "F5"),
    (b"JSteg",          "JSteg"),
    (b"jsteg",          "JSteg"),
    (b"Camouflage",     "Camouflage"),
    (b"Hide4PGP",       "Hide4PGP"),
    (b"wbStego",        "wbStego"),
    (b"MP3Stego",       "MP3Stego"),
    (b"PGP MESSAGE",    "PGP Encrypted"),
    (b"-----BEGIN PGP", "PGP Block"),
    (b"Salted__",       "OpenSSL Encrypted"),  # OpenSSL enc header
]

# ---------------------------------------------------------------------------
# Suspicious string patterns — regex applied to extracted strings
# ---------------------------------------------------------------------------
_SUSPICIOUS_PATTERNS: list[tuple[str, str]] = [
    (r"https?://\S+",                       "Embedded URL"),
    (r"[A-Za-z0-9+/]{40,}={0,2}",         "Possible base64 blob"),
    (r"password\s*[=:]\s*\S+",             "Password-like string"),
    (r"secret\s*[=:]\s*\S+",              "Secret-like string"),
    (r"\b[A-Fa-f0-9]{32}\b",              "MD5-like hash string"),
    (r"\b[A-Fa-f0-9]{64}\b",              "SHA256-like hash string"),
    (r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "Email address"),
    (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "IP address"),
]

# Minimum length for a string to be considered printable ASCII
_MIN_STRING_LENGTH = 4

# Printable ASCII characters (including space, tab, newline)
_PRINTABLE = frozenset(string.printable)


class FormatValidator:
    """
    Validates image files at the binary / format level.

    Usage
    -----
    validator = FormatValidator()
    result    = validator.validate("suspicious.jpg")
    """

    def validate(self, filepath: str | Path) -> dict:
        """
        Run full format-level forensic validation.

        Returns
        -------
        dict with keys:
            format_ok               : bool  (magic bytes match extension)
            detected_format         : str   (format name from magic bytes)
            claimed_extension       : str
            format_mismatch         : bool
            stego_tools_found       : list[str]
            extracted_strings       : list[str]  (first 100)
            suspicious_strings      : list[dict] (pattern, string, reason)
            total_strings_found     : int
            anomalies               : list[str]
            suspicion_score         : float (0–100)
        """
        path = Path(filepath)
        data = path.read_bytes()
        ext  = path.suffix.lower()

        result: dict[str, Any] = {
            "format_ok":            True,
            "detected_format":      "Unknown",
            "claimed_extension":    ext,
            "format_mismatch":      False,
            "stego_tools_found":    [],
            "extracted_strings":    [],
            "suspicious_strings":   [],
            "total_strings_found":  0,
            "anomalies":            [],
            "suspicion_score":      0.0,
        }

        # ----------------------------------------------------------------
        # 1. Magic bytes check
        # ----------------------------------------------------------------
        detected_format, valid_extensions = self._detect_format(data)
        result["detected_format"] = detected_format

        if detected_format == "Unknown":
            result["format_ok"] = False
            result["format_mismatch"] = True
            result["anomalies"].append(
                f"Unknown file format — magic bytes do not match any known signature"
            )
        elif ext not in valid_extensions and valid_extensions:
            result["format_ok"] = False
            result["format_mismatch"] = True
            result["anomalies"].append(
                f"Format mismatch: file is {detected_format} "
                f"but has extension '{ext}'"
            )

        # ----------------------------------------------------------------
        # 2. Steganography tool signature scan
        # ----------------------------------------------------------------
        for signature, tool_name in STEGO_TOOL_SIGNATURES:
            if signature in data:
                if tool_name not in result["stego_tools_found"]:
                    result["stego_tools_found"].append(tool_name)

        if result["stego_tools_found"]:
            result["anomalies"].append(
                f"Steganography tool signatures found: "
                f"{', '.join(result['stego_tools_found'])}"
            )

        # ----------------------------------------------------------------
        # 3. Printable string extraction
        # ----------------------------------------------------------------
        strings = self._extract_strings(data, min_length=_MIN_STRING_LENGTH)
        result["total_strings_found"] = len(strings)
        result["extracted_strings"] = strings[:100]

        # ----------------------------------------------------------------
        # 4. Suspicious string pattern matching
        # ----------------------------------------------------------------
        suspicious = []
        for s in strings:
            for pattern, reason in _SUSPICIOUS_PATTERNS:
                if re.search(pattern, s, re.IGNORECASE):
                    suspicious.append({
                        "string": s[:200],
                        "reason": reason,
                    })
                    break  # one reason per string is enough
        result["suspicious_strings"] = suspicious[:20]

        if suspicious:
            result["anomalies"].append(
                f"{len(suspicious)} suspicious string(s) found "
                f"(URLs, base64, passwords, hashes)"
            )

        # ----------------------------------------------------------------
        # 5. Suspicion score
        # ----------------------------------------------------------------
        score = 0.0

        if result["stego_tools_found"]:
            score += 60.0  # very strong signal

        if result["format_mismatch"]:
            score += 30.0

        if suspicious:
            score += min(20.0, len(suspicious) * 4.0)

        result["suspicion_score"] = round(min(100.0, score), 2)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_format(self, data: bytes) -> tuple[str, list[str]]:
        """
        Detect file format from magic bytes.
        Returns (format_name, valid_extensions).
        """
        for magic, extensions, name in MAGIC_SIGNATURES:
            if data.startswith(magic):
                # Special case: RIFF — check for WebP
                if name == "RIFF/WebP":
                    if len(data) >= 12 and data[8:12] == b"WEBP":
                        return "WebP", [".webp"]
                    return "RIFF (non-WebP)", [".wav", ".avi"]
                return name, extensions
        return "Unknown", []

    def _extract_strings(self, data: bytes, min_length: int = 4) -> list[str]:
        """
        Extract all runs of printable ASCII characters of at least min_length.
        Similar to the Unix `strings` command.
        """
        strings: list[str] = []
        current: list[str] = []

        for byte in data:
            char = chr(byte)
            if char in _PRINTABLE and char not in ("\r", "\n", "\x0b", "\x0c"):
                current.append(char)
            else:
                if len(current) >= min_length:
                    s = "".join(current).strip()
                    if s:
                        strings.append(s)
                current = []

        # Flush last run
        if len(current) >= min_length:
            s = "".join(current).strip()
            if s:
                strings.append(s)

        return strings

    def format_report(self, result: dict) -> str:
        """Return a plain-text summary for CLI output."""
        lines = ["=" * 60, "FORMAT VALIDATION REPORT", "=" * 60]
        lines.append(f"Format OK        : {result['format_ok']}")
        lines.append(f"Detected Format  : {result['detected_format']}")
        lines.append(f"Claimed Extension: {result['claimed_extension']}")
        lines.append(f"Format Mismatch  : {result['format_mismatch']}")
        lines.append(f"Stego Tools Found: {result['stego_tools_found'] or 'None'}")
        lines.append(f"Total Strings    : {result['total_strings_found']}")
        lines.append(f"Suspicious Strings: {len(result['suspicious_strings'])}")
        lines.append(f"Suspicion Score  : {result['suspicion_score']}/100")

        if result["suspicious_strings"]:
            lines.append("")
            lines.append("SUSPICIOUS STRINGS:")
            for item in result["suspicious_strings"]:
                lines.append(f"  [{item['reason']}] {item['string'][:80]}")

        if result["anomalies"]:
            lines.append("")
            lines.append("ANOMALIES:")
            for a in result["anomalies"]:
                lines.append(f"  ⚠  {a}")

        lines.append("=" * 60)
        return "\n".join(lines)