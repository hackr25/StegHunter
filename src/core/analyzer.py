"""
Main steganography analysis orchestrator.
FINAL ENTERPRISE HYBRID VERSION:
Classical Forensics + Adaptive Statistical Detectors + Deep CNN +
RS/SPA/DCT + Hybrid Heatmap + Reasoning + Hiding Localization + Video Analysis
"""
from __future__ import annotations

import time
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from PIL import Image

from .lsb_analyzer import lsb_analysis
from .statistical_tests import chi_square_test, pixel_value_differencing
from .reasoning_engine import ReasoningEngine
from .hiding_location_analyzer import HidingLocationAnalyzer

try:
    from .deep_stego_cnn import DeepStegoAnalyzer
    TF_DEEP_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] TensorFlow Deep CNN unavailable: {e}")
    DeepStegoAnalyzer = None
    TF_DEEP_AVAILABLE = False

from .rs_analyzer import RSAnalyzer
from .spa_analyzer import SPAAnalyzer
from .dct_stego_analyzer import DCTStegoAnalyzer
from src.forensics.png_chunk_analyzer import PNGChunkAnalyzer
from .heatmap_generator import HeatmapGenerator

from ..common.constants import DEFAULT_WEIGHTS, SUPPORTED_FORMATS, JPEG_FORMATS
from ..common.timeout_handler import TimeoutHandler, TimeoutException

logger = logging.getLogger(__name__)

_video_analyzer = None
_video_container_analyzer = None

_DEFAULT_WEIGHTS: Dict[str, float] = DEFAULT_WEIGHTS


class SteganographyAnalyzer:
    """Orchestrate multi-method steganography analysis on image and video files."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.supported_formats = SUPPORTED_FORMATS
        self._config = config

        self.location_analyzer = HidingLocationAnalyzer()

        self.deep_stego_analyzer = None
        if TF_DEEP_AVAILABLE:
            try:
                self.deep_stego_analyzer = DeepStegoAnalyzer()
                print("[INFO] Deep CNN TensorFlow detector loaded successfully.")
            except Exception as e:
                print(f"[WARNING] Deep CNN initialization failed: {e}")
                self.deep_stego_analyzer = None

        self.rs_analyzer = RSAnalyzer()
        self.spa_analyzer = SPAAnalyzer()
        self.dct_analyzer = DCTStegoAnalyzer()
        self.png_chunk_analyzer = PNGChunkAnalyzer()

        self.heatmap_generator = HeatmapGenerator()
        self.reasoning_engine = ReasoningEngine()

    # ------------------------------------------------------------------
    # BASIC ANALYSIS
    # ------------------------------------------------------------------

    def basic_analysis(self, image_path: str) -> Dict[str, Any]:
        start = time.time()
        path = Path(image_path)
        with Image.open(path) as img:
            image = img.copy()

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

    # ------------------------------------------------------------------
    # IMAGE ANALYSIS
    # ------------------------------------------------------------------

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        from ..common.image_utils import validate_image_path
        from ..common.exceptions import InvalidImageError

        try:
            path = validate_image_path(image_path)
            with Image.open(path) as img:
                image = img.copy()
        except Exception as e:
            raise InvalidImageError(f"Failed to load image {image_path}: {e}")

        start = time.time()
        ext = path.suffix.lower()

        results: dict = {
            "filename": path.name,
            "full_path": str(path.resolve()),
            "file_size": path.stat().st_size,
            "format": image.format,
            "dimensions": (image.width, image.height),
            "mode": image.mode,
            "analysis_time": 0.0,
            "methods": {},
            "errors": [],
            "final_suspicion_score": 0.0,
            "forensic_reasoning": {},
            "heatmap_analysis": {},
            "hiding_location": {}
        }

        enabled = self._enabled_methods()
        
                # ----------------------------------------------------------
        # BASIC ANALYSIS
        # ----------------------------------------------------------
        if "basic" in enabled:
            try:
                results["methods"]["basic"] = self.basic_analysis(path)
            except Exception as exc:
                error_msg = f"basic: {str(exc)}"
                results["methods"]["basic"] = {"error": error_msg, "basic_suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'basic' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # LSB ANALYSIS
        # ----------------------------------------------------------
        if "lsb" in enabled:
            try:
                results["methods"]["lsb"] = lsb_analysis(image)
            except Exception as exc:
                error_msg = f"lsb: {str(exc)}"
                results["methods"]["lsb"] = {"error": error_msg, "lsb_suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'lsb' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # CHI SQUARE
        # ----------------------------------------------------------
        if "chi_square" in enabled:
            try:
                results["methods"]["chi_square"] = chi_square_test(image)
            except Exception as exc:
                error_msg = f"chi_square: {str(exc)}"
                results["methods"]["chi_square"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'chi_square' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # PIXEL DIFFERENCING
        # ----------------------------------------------------------
        if "pixel_differencing" in enabled:
            try:
                results["methods"]["pixel_differencing"] = pixel_value_differencing(image)
            except Exception as exc:
                error_msg = f"pixel_differencing: {str(exc)}"
                results["methods"]["pixel_differencing"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'pixel_differencing' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # FORMAT VALIDATION
        # ----------------------------------------------------------
        if "format_validation" in enabled:
            try:
                from src.forensics.format_validator import FormatValidator
                results["methods"]["format_validation"] = FormatValidator().validate(path)
            except Exception as exc:
                error_msg = f"format_validation: {str(exc)}"
                results["methods"]["format_validation"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'format_validation' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # JPEG STRUCTURE
        # ----------------------------------------------------------
        if "jpeg_structure" in enabled and ext in JPEG_FORMATS:
            try:
                from src.forensics.jpeg_structure import JPEGStructureParser
                results["methods"]["jpeg_structure"] = JPEGStructureParser().parse(path)
            except Exception as exc:
                error_msg = f"jpeg_structure: {str(exc)}"
                results["methods"]["jpeg_structure"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'jpeg_structure' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # METADATA
        # ----------------------------------------------------------
        if "metadata" in enabled:
            try:
                from src.forensics.metadata_analyzer import MetadataAnalyzer
                results["methods"]["metadata"] = MetadataAnalyzer().analyze(path)
            except Exception as exc:
                error_msg = f"metadata: {str(exc)}"
                results["methods"]["metadata"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'metadata' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # SOCIAL MEDIA DETECTOR
        # ----------------------------------------------------------
        if "social_media" in enabled and ext in JPEG_FORMATS:
            try:
                from src.forensics.social_media_detector import SocialMediaDetector
                results["methods"]["social_media"] = SocialMediaDetector().identify(path)
            except Exception as exc:
                error_msg = f"social_media: {str(exc)}"
                results["methods"]["social_media"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'social_media' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # ERROR LEVEL ANALYSIS
        # ----------------------------------------------------------
        if "ela" in enabled:
            try:
                from src.core.ela_analyzer import ELAAnalyzer
                results["methods"]["ela"] = ELAAnalyzer().analyze(str(path))
            except Exception as exc:
                error_msg = f"ela: {str(exc)}"
                results["methods"]["ela"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'ela' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # JPEG GHOST ANALYSIS
        # ----------------------------------------------------------
        if "jpeg_ghost" in enabled and ext in JPEG_FORMATS:
            try:
                from src.core.jpeg_ghost_analyzer import JPEGGhostAnalyzer
                results["methods"]["jpeg_ghost"] = JPEGGhostAnalyzer().analyze(str(path))
            except Exception as exc:
                error_msg = f"jpeg_ghost: {str(exc)}"
                results["methods"]["jpeg_ghost"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'jpeg_ghost' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # NOISE ANALYSIS
        # ----------------------------------------------------------
        if "noise" in enabled:
            try:
                from src.core.noise_analyzer import NoiseAnalyzer
                results["methods"]["noise"] = NoiseAnalyzer().analyze(str(path))
            except Exception as exc:
                error_msg = f"noise: {str(exc)}"
                results["methods"]["noise"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'noise' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # COLOR SPACE ANALYSIS
        # ----------------------------------------------------------
        if "color_space" in enabled:
            try:
                from src.core.color_space_analyzer import ColorSpaceAnalyzer
                results["methods"]["color_space"] = ColorSpaceAnalyzer().analyze(str(path))
            except Exception as exc:
                error_msg = f"color_space: {str(exc)}"
                results["methods"]["color_space"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'color_space' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # CLONE DETECTION
        # ----------------------------------------------------------
        if "clone_detection" in enabled:
            try:
                from src.core.clone_detector import CloneDetector
                results["methods"]["clone_detection"] = CloneDetector().analyze(str(path))
            except Exception as exc:
                error_msg = f"clone_detection: {str(exc)}"
                results["methods"]["clone_detection"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'clone_detection' failed: {exc}", exc_info=True)
                
                # ----------------------------------------------------------
        # DEEP LEARNING ANALYSIS
        # ----------------------------------------------------------
        if "deep_learning" in enabled:
            if self.deep_stego_analyzer is not None:
                try:
                    results["methods"]["deep_learning"] = self.deep_stego_analyzer.analyze(str(path))
                except Exception as exc:
                    error_msg = f"deep_learning: {str(exc)}"
                    results["methods"]["deep_learning"] = {
                        "error": error_msg,
                        "suspicion_score": 0.0,
                        "status": "runtime_failed"
                    }
                    results["errors"].append(error_msg)
                    logger.warning(f"Method 'deep_learning' failed: {exc}", exc_info=True)
            else:
                results["methods"]["deep_learning"] = {
                    "suspicion_score": 0.0,
                    "status": "tensorflow_unavailable"
            }

        # ----------------------------------------------------------
        # RS ANALYSIS
        # ----------------------------------------------------------
        if "rs_analysis" in enabled:
            try:
                results["methods"]["rs_analysis"] = self.rs_analyzer.analyze(str(path))
            except Exception as exc:
                error_msg = f"rs_analysis: {str(exc)}"
                results["methods"]["rs_analysis"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'rs_analysis' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # SPA ANALYSIS
        # ----------------------------------------------------------
        if "spa_analysis" in enabled:
            try:
                results["methods"]["spa_analysis"] = self.spa_analyzer.analyze(str(path))
            except Exception as exc:
                error_msg = f"spa_analysis: {str(exc)}"
                results["methods"]["spa_analysis"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'spa_analysis' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # DCT ANALYSIS
        # ----------------------------------------------------------
        if "dct_analysis" in enabled and ext in JPEG_FORMATS:
            try:
                results["methods"]["dct_analysis"] = self.dct_analyzer.analyze(str(path))
            except Exception as exc:
                error_msg = f"dct_analysis: {str(exc)}"
                results["methods"]["dct_analysis"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'dct_analysis' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # PNG CHUNK ANALYSIS
        # ----------------------------------------------------------
        if "png_chunk" in enabled and ext == ".png":
            try:
                results["methods"]["png_chunk"] = self.png_chunk_analyzer.analyze(str(path))
            except Exception as exc:
                error_msg = f"png_chunk: {str(exc)}"
                results["methods"]["png_chunk"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'png_chunk' failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # HIDING LOCATION ESTIMATION
        # ----------------------------------------------------------
        try:
            results["hiding_location"] = self.location_analyzer.locate(results)
        except Exception as exc:
            error_msg = f"hiding_location: {str(exc)}"
            results["hiding_location"] = {"error": error_msg}
            results["errors"].append(error_msg)
            logger.warning(f"Hiding location failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # FINAL WEIGHTED SCORE
        # ----------------------------------------------------------
        results["final_suspicion_score"] = self._weighted_score(results["methods"])

        if results.get("hiding_location", {}).get("confidence", 0) > 60:
            results["final_suspicion_score"] = min(100.0, results["final_suspicion_score"] + 3.5)

        # ----------------------------------------------------------
        # FORENSIC REASONING ENGINE
        # ----------------------------------------------------------
        try:
            results["forensic_reasoning"] = self.reasoning_engine.generate_explanation(results)
        except Exception as exc:
            error_msg = f"reasoning_engine: {str(exc)}"
            results["forensic_reasoning"] = {"error": error_msg}
            results["errors"].append(error_msg)
            logger.warning(f"Reasoning engine failed: {exc}", exc_info=True)

        # ----------------------------------------------------------
        # HYBRID HEATMAP GENERATION
        # ----------------------------------------------------------
        try:
            results["heatmap_analysis"] = self.heatmap_generator.generate_hybrid_heatmap(str(path), results)
        except Exception as exc:
            error_msg = f"heatmap_generator: {str(exc)}"
            results["heatmap_analysis"] = {"error": error_msg}
            results["errors"].append(error_msg)
            logger.warning(f"Heatmap generation failed: {exc}", exc_info=True)

        results["analysis_time"] = round(time.time() - start, 3)
        return results

    # ------------------------------------------------------------------
    # VIDEO ANALYSIS
    # ------------------------------------------------------------------

    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        try:
            from .video_analyzer import VideoStegoAnalyzer
            analyzer = VideoStegoAnalyzer()
            return analyzer.analyze(video_path)
        except Exception as exc:
            return {
                "filename": Path(video_path).name,
                "analysis_type": "video",
                "error": str(exc),
                "final_suspicion_score": 0.0
            }

    # ------------------------------------------------------------------
    # ENABLED METHODS
    # ------------------------------------------------------------------

    def _enabled_methods(self):
        return [
            "basic",
            "lsb",
            "chi_square",
            "pixel_differencing",
            "format_validation",
            "jpeg_structure",
            "metadata",
            "social_media",
            "ela",
            "jpeg_ghost",
            "noise",
            "color_space",
            "clone_detection",
            "deep_learning",
            "rs_analysis",
            "spa_analysis",
            "dct_analysis",
            "png_chunk"
        ]
        
    def _safe_numeric(self, value, default=0.0):
        """
        Convert detector outputs safely into valid finite float.
        Prevents NaN / Inf poisoning of final score.
        """
        import math
        import numpy as np

        try:
            if value is None:
                return default

            if isinstance(value, np.generic):
                value = float(value)

            value = float(value)

            if math.isnan(value) or math.isinf(value):
                return default

            return value

        except Exception:
            return default

    # ------------------------------------------------------------------
    # FINAL WEIGHTED SCORE ENGINE
    # ------------------------------------------------------------------

    def _weighted_score(self, methods: Dict[str, Any]) -> float:
        """
        Enterprise weighted fusion engine with NaN/Inf immunity.
        """

        score_map = {
            "basic": methods.get("basic", {}).get("basic_suspicion_score"),
            "lsb": methods.get("lsb", {}).get("lsb_suspicion_score"),
            "chi_square": methods.get("chi_square", {}).get("suspicion_score"),
            "pixel_differencing": methods.get("pixel_differencing", {}).get("suspicion_score"),
            "format_validation": methods.get("format_validation", {}).get("suspicion_score"),
            "jpeg_structure": methods.get("jpeg_structure", {}).get("suspicion_score"),
            "metadata": methods.get("metadata", {}).get("suspicion_score"),
            "social_media": methods.get("social_media", {}).get("suspicion_score"),
            "ela": methods.get("ela", {}).get("suspicion_score"),
            "jpeg_ghost": methods.get("jpeg_ghost", {}).get("suspicion_score"),
            "noise": methods.get("noise", {}).get("suspicion_score"),
            "color_space": methods.get("color_space", {}).get("suspicion_score"),
            "clone_detection": methods.get("clone_detection", {}).get("suspicion_score"),
            "deep_learning": methods.get("deep_learning", {}).get("suspicion_score"),
            "rs_analysis": methods.get("rs_analysis", {}).get("suspicion_score"),
            "spa_analysis": methods.get("spa_analysis", {}).get("suspicion_score"),
            "dct_analysis": methods.get("dct_analysis", {}).get("suspicion_score"),
            "png_chunk": methods.get("png_chunk", {}).get("suspicion_score"),
        }

        weighted_total = 0.0
        weight_sum = 0.0

        for method, raw_score in score_map.items():
            score = self._safe_numeric(raw_score, default=None)

            if score is None:
                continue

            weight = self._safe_numeric(_DEFAULT_WEIGHTS.get(method, 1.0), default=1.0)

            weighted_total += score * weight
            weight_sum += weight

        if weight_sum <= 0:
            return 0.0

        final_score = weighted_total / weight_sum
        final_score = self._safe_numeric(final_score, default=0.0)

        final_score = max(0.0, min(100.0, final_score))

        return round(final_score, 2)