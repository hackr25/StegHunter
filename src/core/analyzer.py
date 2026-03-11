"""
Main steganography analysis orchestrator.
"""
from __future__ import annotations

import time
from pathlib import Path

from PIL import Image

from .lsb_analyzer import lsb_analysis
from .statistical_tests import chi_square_test, pixel_value_differencing


# Default weights used when no ConfigManager is available.
_DEFAULT_WEIGHTS: dict[str, float] = {
    "basic": 0.2,
    "lsb": 0.5,
    "chi_square": 0.2,
    "pixel_differencing": 0.1,
}

SUPPORTED_FORMATS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
)


class SteganographyAnalyzer:
    """Orchestrate multi-method steganography analysis on image files."""

    def __init__(self, config=None):
        """
        Args:
            config: Optional ConfigManager instance.
                    When None the built-in defaults are used.
        """
        self.supported_formats = SUPPORTED_FORMATS
        self._config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def basic_analysis(self, image_path) -> dict:
        """Return basic file-level statistics for *image_path*.

        The suspicion score reflects how unusual the file-size-to-pixel-count
        ratio is compared to an uncompressed image (ratio ~1.0).
        """
        start = time.time()
        path = Path(image_path)
        image = Image.open(path)

        file_size = path.stat().st_size
        dimensions = (image.width, image.height)
        channels = len(image.mode)
        expected_size = image.width * image.height * channels

        size_ratio = file_size / expected_size if expected_size > 0 else 0.0

        # Deviation from expected uncompressed size, scaled to 0-100.
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

        results: dict = {
            "filename": path.name,
            "full_path": str(path.resolve()),
            "file_size": path.stat().st_size,
            "format": image.format,
            "dimensions": (image.width, image.height),
            "mode": image.mode,
            "analysis_time": 0.0,
            "methods": {},
        }

        results["methods"]["basic"] = self.basic_analysis(path)
        results["methods"]["lsb"] = lsb_analysis(image)
        results["methods"]["chi_square"] = chi_square_test(image)
        results["methods"]["pixel_differencing"] = pixel_value_differencing(image)

        results["final_suspicion_score"] = round(
            self._weighted_score(results["methods"]), 2
        )
        results["analysis_time"] = round(time.time() - start, 3)
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _weighted_score(self, methods: dict) -> float:
        """Compute a config-driven weighted average suspicion score."""
        weights = _DEFAULT_WEIGHTS.copy()
        if self._config is not None:
            cfg_weights = self._config.get("weights")
            if cfg_weights:
                weights.update(cfg_weights)

        score_map = {
            "basic": methods.get("basic", {}).get("basic_suspicion_score", 0.0),
            "lsb": methods.get("lsb", {}).get("lsb_suspicion_score", 0.0),
            "chi_square": methods.get("chi_square", {}).get("suspicion_score", 0.0),
            "pixel_differencing": methods.get("pixel_differencing", {}).get("suspicion_score", 0.0),
        }

        total_weight = sum(weights.get(k, 0.0) for k in score_map)
        if total_weight == 0:
            return 0.0

        return sum(score_map[k] * weights.get(k, 0.0) for k in score_map) / total_weight
