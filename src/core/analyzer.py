"""
Main steganography analysis orchestrator.
Phase 1: JPEG Structure, Metadata, Format Validator, Social Media Detector.
Phase 2: ELA (Error Level Analysis).
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
from ..common.constants import DEFAULT_WEIGHTS, SUPPORTED_FORMATS, JPEG_FORMATS
from ..common.timeout_handler import TimeoutHandler, TimeoutException

# Configure logger for error reporting
logger = logging.getLogger(__name__)

# Lazy imports for Phase 4 to avoid circular dependencies
_video_analyzer = None
_video_container_analyzer = None


# Default weights — Phase 1 + Phase 2 (ELA)
_DEFAULT_WEIGHTS: Dict[str, float] = DEFAULT_WEIGHTS


class SteganographyAnalyzer:
    """Orchestrate multi-method steganography analysis on image files."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.supported_formats = SUPPORTED_FORMATS
        self._config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def basic_analysis(self, image_path: str) -> Dict[str, Any]:
        """Return basic file-level statistics for image_path.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dict containing basic statistics and suspicion score
        """
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

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Run all enabled detection methods and return a combined result dict.
        
        Args:
            image_path: Path to image file (.jpg, .png, .bmp, .tiff)
            
        Returns:
            Dict containing:
                - filename: Image filename
                - full_path: Absolute path
                - file_size: File size in bytes
                - format: Image format
                - dimensions: (width, height) tuple
                - mode: Image mode
                - overall_score: Combined suspicion score (0-100)
                - is_suspicious: bool
                - method_scores: Dict of individual method scores
                - methods: Dict of detailed results per method
                - analysis_time: Total analysis time in seconds
                - errors: List of methods that failed
                
        Raises:
            InvalidImageError: If image cannot be loaded or validated
        """
        from ..common.image_utils import validate_image_path
        from ..common.exceptions import InvalidImageError
        
        # Validate and load image
        try:
            path = validate_image_path(image_path)
            image = Image.open(path)
        except Exception as e:
            raise InvalidImageError(f"Failed to load image {image_path}: {e}")
        
        start = time.time()
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
            "errors":        [],  # Track methods that failed
        }

        enabled = self._enabled_methods()

        # ── Original detection methods (with error isolation) ────────────────────────
        if "basic" in enabled:
            try:
                results["methods"]["basic"] = self.basic_analysis(path)
            except Exception as exc:
                error_msg = f"basic: {str(exc)}"
                results["methods"]["basic"] = {"error": error_msg, "basic_suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'basic' failed: {exc}", exc_info=True)

        if "lsb" in enabled:
            try:
                results["methods"]["lsb"] = lsb_analysis(image)
            except Exception as exc:
                error_msg = f"lsb: {str(exc)}"
                results["methods"]["lsb"] = {"error": error_msg, "lsb_suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'lsb' failed: {exc}", exc_info=True)

        if "chi_square" in enabled:
            try:
                results["methods"]["chi_square"] = chi_square_test(image)
            except Exception as exc:
                error_msg = f"chi_square: {str(exc)}"
                results["methods"]["chi_square"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'chi_square' failed: {exc}", exc_info=True)

        if "pixel_differencing" in enabled:
            try:
                results["methods"]["pixel_differencing"] = pixel_value_differencing(image)
            except Exception as exc:
                error_msg = f"pixel_differencing: {str(exc)}"
                results["methods"]["pixel_differencing"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'pixel_differencing' failed: {exc}", exc_info=True)

        # ── Phase 1: Format Validation (all image types) ──────────────
        if "format_validation" in enabled:
            try:
                from src.forensics.format_validator import FormatValidator
                results["methods"]["format_validation"] = FormatValidator().validate(path)
            except Exception as exc:
                error_msg = f"format_validation: {str(exc)}"
                results["methods"]["format_validation"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'format_validation' failed: {exc}", exc_info=True)

        # ── Phase 1: JPEG Structure (JPEG only) ───────────────────────
        if "jpeg_structure" in enabled and ext in JPEG_FORMATS:
            try:
                from src.forensics.jpeg_structure import JPEGStructureParser
                results["methods"]["jpeg_structure"] = JPEGStructureParser().parse(path)
            except Exception as exc:
                error_msg = f"jpeg_structure: {str(exc)}"
                results["methods"]["jpeg_structure"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'jpeg_structure' failed: {exc}", exc_info=True)

        # ── Phase 1: Metadata / EXIF Analysis ────────────────────────
        if "metadata" in enabled:
            try:
                from src.forensics.metadata_analyzer import MetadataAnalyzer
                results["methods"]["metadata"] = MetadataAnalyzer().analyze(path)
            except Exception as exc:
                error_msg = f"metadata: {str(exc)}"
                results["methods"]["metadata"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'metadata' failed: {exc}", exc_info=True)

        # ── Phase 1: Social Media Detection (JPEG only) ───────────────
        if "social_media" in enabled and ext in JPEG_FORMATS:
            try:
                from src.forensics.social_media_detector import SocialMediaDetector
                results["methods"]["social_media"] = SocialMediaDetector().identify(path)
            except Exception as exc:
                error_msg = f"social_media: {str(exc)}"
                results["methods"]["social_media"] = {"error": error_msg}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'social_media' failed: {exc}", exc_info=True)


        # ── Phase 2: ELA — Error Level Analysis ──────────────────────
        if "ela" in enabled:
            try:
                from src.core.ela_analyzer import ELAAnalyzer
                timeout_sec = self._get_timeout()
                
                def run_ela():
                    return ELAAnalyzer().analyze(
                        path,
                        quality=self._cfg_int("performance.ela_quality", 95),
                        scale=self._cfg_int("performance.ela_scale", 10),
                    )
                
                # Wrap with timeout
                try:
                    results["methods"]["ela"] = TimeoutHandler.with_graceful_fallback(
                        timeout_seconds=timeout_sec,
                        fallback_value={"suspicion_score": 0.0}
                    )(run_ela)()
                except TimeoutException as te:
                    error_msg = f"ela: {str(te)}"
                    results["methods"]["ela"] = {"error": error_msg, "suspicion_score": 0.0, "timed_out": True}
                    results["errors"].append(error_msg)
                    logger.warning(f"Method 'ela' timed out after {timeout_sec}s")
                    
            except Exception as exc:
                error_msg = f"ela: {str(exc)}"
                results["methods"]["ela"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'ela' failed: {exc}", exc_info=True)
                
        # JPEG Ghost
        if "jpeg_ghost" in enabled and ext in JPEG_FORMATS:
            try:
                from src.core.jpeg_ghost_analyzer import JPEGGhostAnalyzer
                results["methods"]["jpeg_ghost"] = JPEGGhostAnalyzer().analyze(path)
            except Exception as exc:
                error_msg = f"jpeg_ghost: {str(exc)}"
                results["methods"]["jpeg_ghost"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'jpeg_ghost' failed: {exc}", exc_info=True)

        # Noise Analysis
        if "noise" in enabled:
            try:
                from src.core.noise_analyzer import NoiseAnalyzer
                results["methods"]["noise"] = NoiseAnalyzer().analyze(path)
            except Exception as exc:
                error_msg = f"noise: {str(exc)}"
                results["methods"]["noise"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'noise' failed: {exc}", exc_info=True)

        # Color Space Analysis
        if "color_space" in enabled:
            try:
                from src.core.color_space_analyzer import ColorSpaceAnalyzer
                results["methods"]["color_space"] = ColorSpaceAnalyzer().analyze(path)
            except Exception as exc:
                error_msg = f"color_space: {str(exc)}"
                results["methods"]["color_space"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'color_space' failed: {exc}", exc_info=True)
                
        # Clone Detection (Phase 3) — Heavy computation, add timeout
        if "clone_detection" in enabled:
            try:
                from src.core.clone_detector import CloneDetector
                timeout_sec = self._get_timeout()
                
                def run_clone_detection():
                    return CloneDetector().analyze(path)
                
                # Wrap with timeout
                try:
                    results["methods"]["clone_detection"] = TimeoutHandler.with_graceful_fallback(
                        timeout_seconds=timeout_sec,
                        fallback_value={"suspicion_score": 0.0}
                    )(run_clone_detection)()
                except TimeoutException as te:
                    error_msg = f"clone_detection: {str(te)}"
                    results["methods"]["clone_detection"] = {"error": error_msg, "suspicion_score": 0.0, "timed_out": True}
                    results["errors"].append(error_msg)
                    logger.warning(f"Method 'clone_detection' timed out after {timeout_sec}s")
                    
            except Exception as exc:
                error_msg = f"clone_detection: {str(exc)}"
                results["methods"]["clone_detection"] = {"error": error_msg, "suspicion_score": 0.0}
                results["errors"].append(error_msg)
                logger.warning(f"Method 'clone_detection' failed: {exc}", exc_info=True)

        # ── Final scoring ─────────────────────────────────────────────
        results["final_suspicion_score"] = round(
            self._weighted_score(results["methods"]), 2
        )
        results["is_suspicious"] = results["final_suspicion_score"] >= (
            self._config.get("suspicion_threshold", 50.0) if self._config else 50.0
        )
        
        try:
            reasoner = ReasoningEngine()
            results["explanation"] = reasoner.generate_explanation(results)
        except Exception as e:
            results["explanation"] = {"error": f"Reasoning engine failed: {str(e)}"}
            logger.warning(f"Reasoning engine failed: {e}", exc_info=True)
            
        results["analysis_time"] = round(time.time() - start, 3)
        
        # Log summary of errors if any
        if results["errors"]:
            logger.info(f"Analysis completed with {len(results['errors'])} method error(s)")
            
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_timeout(self) -> int:
        """Get analysis timeout from config, default 30 seconds."""
        if self._config is None:
            return 30
        timeout = self._config.get("performance", {}).get("timeout_seconds")
        if timeout is None:
            return 30
        return max(1, min(300, int(timeout)))  # Clamp between 1-300 seconds

    def _cfg_int(self, key: str, default: int) -> int:
        """Read an integer from config, return default if missing."""
        if self._config is None:
            return default
        val = self._config.get(key)
        return int(val) if val is not None else default

    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """Run Phase 4 video forensics analysis on a video file.
        
        Args:
            video_path: Path to video file (.mp4, .mkv, .avi, etc.)
            
        Returns:
            Dict containing:
                - filename: Video filename
                - full_path: Absolute path
                - file_size: File size in bytes
                - format: Detected video format
                - frame_count: Number of frames analyzed
                - overall_score: Combined suspicion score (0-100)
                - is_suspicious: bool
                - methods: Dict of detailed results (video_frame_analysis, video_container, heatmap)
                - analysis_time: Total analysis time in seconds
        """
        from pathlib import Path
        from ..common.exceptions import InvalidImageError
        
        try:
            path = Path(video_path)
            if not path.exists():
                raise InvalidImageError(f"Video file not found: {video_path}")
        except Exception as e:
            raise InvalidImageError(f"Failed to load video {video_path}: {e}")
        
        start = time.time()
        
        results: dict = {
            "filename": path.name,
            "full_path": str(path.resolve()),
            "file_size": path.stat().st_size,
            "format": path.suffix.lower(),
            "frame_count": 0,
            "analysis_time": 0.0,
            "methods": {},
        }
        
        # ── Phase 4: Video Frame Analysis ─────────────────────────
        try:
            global _video_analyzer
            if _video_analyzer is None:
                from src.core.video_analyzer import VideoAnalyzer
                _video_analyzer = VideoAnalyzer
            video_analyzer = _video_analyzer()
            results["methods"]["video_frame_analysis"] = video_analyzer.analyze_video(video_path)
            results["frame_count"] = results["methods"]["video_frame_analysis"].get("frame_count", 0)
        except Exception as exc:
            results["methods"]["video_frame_analysis"] = {"error": str(exc), "score": 0.0}
        
        # ── Phase 4: Video Container Analysis ──────────────────────
        try:
            global _video_container_analyzer
            if _video_container_analyzer is None:
                from src.forensics.video_container_analyzer import VideoContainerAnalyzer
                _video_container_analyzer = VideoContainerAnalyzer
            container_analyzer = _video_container_analyzer()
            results["methods"]["video_container"] = container_analyzer.analyze(video_path)
        except Exception as exc:
            results["methods"]["video_container"] = {"error": str(exc), "score": 0.0}
        
        # ── Final scoring ─────────────────────────────────────────
        frame_score = results["methods"].get("video_frame_analysis", {}).get("score", 0.0)
        container_score = results["methods"].get("video_container", {}).get("score", 0.0)
        results["overall_score"] = round((frame_score * 0.6 + container_score * 0.4), 2)
        results["is_suspicious"] = results["overall_score"] >= 50.0
        results["analysis_time"] = round(time.time() - start, 3)
        
        return results

    def _enabled_methods(self) -> list[str]:
        """Return the list of enabled method names from config, or all defaults."""
        if self._config is not None:
            methods = self._config.get("enabled_methods")
            if methods:
                return methods
        return [
            "basic", "lsb", "chi_square", "pixel_differencing",
            "jpeg_structure", "metadata", "format_validation", "social_media",
            "ela", "jpeg_ghost", "noise", "color_space", "clone_detection", 
        ]

    def _weighted_score(self, methods: Dict[str, Any]) -> float:
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
            "ela":                methods.get("ela",               {}).get("suspicion_score",       0.0),
            "jpeg_ghost":         methods.get("jpeg_ghost",        {}).get("suspicion_score",       0.0),
            "noise":              methods.get("noise",             {}).get("suspicion_score",       0.0),
            "color_space":        methods.get("color_space",       {}).get("suspicion_score",       0.0),
            "clone_detection":    methods.get("clone_detection",   {}).get("suspicion_score",       0.0),
        }

        total_weight = sum(weights.get(k, 0.0) for k in score_map if k in weights)
        if total_weight == 0:
            return 0.0

        return sum(
            score_map[k] * weights.get(k, 0.0)
            for k in score_map if k in weights
        ) / total_weight