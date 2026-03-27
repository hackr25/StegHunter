"""
Main steganography analysis orchestrator.
Updated in Phase 1 to include forensic analysis modules:
  - JPEG Structure Parser
  - Metadata Analyzer (EXIF)
  - Format Validator (magic bytes + stego signatures)
  - Social Media Platform Detector
"""
from __future__ import annotations

import time
from pathlib import Path

from PIL import Image

from .lsb_analyzer import lsb_analysis
from .statistical_tests import chi_square_test, pixel_value_differencing


# Default weights — updated with Phase 1 forensic methods
_DEFAULT_WEIGHTS: dict[str, float] = {
    "basic":              0.15,
    "lsb":                0.30,
    "chi_square":         0.10,
    "pixel_differencing": 0.05,
    "jpeg_structure":     0.15,
    "metadata":           0.10,
    "format_validation":  0.15,
}

SUPPORTED_FORMATS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
)

JPEG_FORMATS: frozenset[str] = frozenset({".jpg", ".jpeg"})


class SteganographyAnalyzer:
    """Orchestrate multi-method steganography analysis on image files."""

    def __init__(self, config=None):
        self.supported_formats = SUPPORTED_FORMATS
        self._config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def basic_analysis(self, image_path) -> dict:
        """Return basic file-level statistics for *image_path*."""
        start = time.time()
        path = Path(image_path)
        image = Image.open(path)

        file_size = path.stat().st_size
        dimensions = (image.width, image.height)
        channels = len(image.mode)
        expected_size = image.width * image.height * channels

        size_ratio = file_size / expected_size if expected_size > 0 else 0.0
        deviation = abs(size_ratio - 1.0)
        suspicion_score = min(100.0, deviation * 50.0)

        return {
            "filename": path.name,
            "file_size": file_size,
            "dimensions": dimensions,
            "format": image.format,
            "analysis_time": round(time.time() - start, 3),
            "size_ratio": round(size_ratio, 4),
            "basic_suspicion_score": round(suspicion_score, 2),
        }

    def analyze_image(self, image_path) -> dict:
        """Run all enabled detection methods and return a combined result dict."""
        start = time.time()
        path = Path(image_path)
        image = Image.open(path)
        ext = path.suffix.lower()

        results: dict = {
            "filename":      path.name,
            "full_path":     str(path.resolve()),
            "file_size":     path.stat().st_size,
            "format":        image.format,
            "dimensions":    (image.width, image.height),
            "mode":          image.mode,
            "analysis_time": 0.0,
            "methods":       {},
        }

        enabled = self._enabled_methods()

        # ── Original detection methods ────────────────────────────────
        if "basic" in enabled:
            results["methods"]["basic"] = self.basic_analysis(path)

        if "lsb" in enabled:
            results["methods"]["lsb"] = lsb_analysis(image)

        if "chi_square" in enabled:
            results["methods"]["chi_square"] = chi_square_test(image)

        if "pixel_differencing" in enabled:
            results["methods"]["pixel_differencing"] = pixel_value_differencing(image)

        # ── Phase 1: Format Validation (all image types) ──────────────
        if "format_validation" in enabled:
            try:
                from src.forensics.format_validator import FormatValidator
                results["methods"]["format_validation"] = FormatValidator().validate(path)
            except Exception as exc:
                results["methods"]["format_validation"] = {"error": str(exc), "suspicion_score": 0.0}

        # ── Phase 1: JPEG Structure (JPEG only) ───────────────────────
        if "jpeg_structure" in enabled and ext in JPEG_FORMATS:
            try:
                from src.forensics.jpeg_structure import JPEGStructureParser
                results["methods"]["jpeg_structure"] = JPEGStructureParser().parse(path)
            except Exception as exc:
                results["methods"]["jpeg_structure"] = {"error": str(exc), "suspicion_score": 0.0}

        # ── Phase 1: Metadata / EXIF Analysis ────────────────────────
        if "metadata" in enabled:
            try:
                from src.forensics.metadata_analyzer import MetadataAnalyzer
                results["methods"]["metadata"] = MetadataAnalyzer().analyze(path)
            except Exception as exc:
                results["methods"]["metadata"] = {"error": str(exc), "suspicion_score": 0.0}

        # ── Phase 1: Social Media Detection (JPEG only) ───────────────
        if "social_media" in enabled and ext in JPEG_FORMATS:
            try:
                from src.forensics.social_media_detector import SocialMediaDetector
                results["methods"]["social_media"] = SocialMediaDetector().identify(path)
            except Exception as exc:
                results["methods"]["social_media"] = {"error": str(exc)}

        # ── Final scoring ─────────────────────────────────────────────
        results["final_suspicion_score"] = round(
            self._weighted_score(results["methods"]), 2
        )
        results["analysis_time"] = round(time.time() - start, 3)
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _enabled_methods(self) -> list[str]:
        """Return the list of enabled method names from config, or all defaults."""
        if self._config is not None:
            methods = self._config.get("enabled_methods")
            if methods:
                return methods
        return [
            "basic", "lsb", "chi_square", "pixel_differencing",
            "jpeg_structure", "metadata", "format_validation", "social_media",
        ]

    def _weighted_score(self, methods: dict) -> float:
        """Compute a config-driven weighted average suspicion score."""
        weights = _DEFAULT_WEIGHTS.copy()
        if self._config is not None:
            cfg_weights = self._config.get("weights")
            if cfg_weights:
                weights.update(cfg_weights)

        score_map = {
            "basic":              methods.get("basic",             {}).get("basic_suspicion_score", 0.0),
            "lsb":                methods.get("lsb",               {}).get("lsb_suspicion_score",  0.0),
            "chi_square":         methods.get("chi_square",        {}).get("suspicion_score",       0.0),
            "pixel_differencing": methods.get("pixel_differencing",{}).get("suspicion_score",       0.0),
            "jpeg_structure":     methods.get("jpeg_structure",    {}).get("suspicion_score",       0.0),
            "metadata":           methods.get("metadata",          {}).get("suspicion_score",       0.0),
            "format_validation":  methods.get("format_validation", {}).get("suspicion_score",       0.0),
        }

        total_weight = sum(weights.get(k, 0.0) for k in score_map if k in weights)
        if total_weight == 0:
            return 0.0

        return sum(
            score_map[k] * weights.get(k, 0.0)
            for k in score_map if k in weights
        ) / total_weight