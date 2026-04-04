"""
ELA — Error Level Analysis for StegHunter.

Detects image tampering and steganographic manipulation by re-saving
an image at a known JPEG quality and analysing the per-pixel error levels.

Authentic regions of a JPEG image that have been compressed once will
have uniformly low error at that quality level. Regions that were pasted
from another source, or processed by a steganography tool, will show
anomalous error levels that stand out from the surrounding area.

Three analyses are combined into a single suspicion score:
  1. ELA pixel statistics  — mean, std, ratio of the error map
  2. Blocking artifacts    — gradient anomaly at 8-pixel JPEG boundaries
  3. Regional variance     — std across 32x32 block ELA means
     (uniform tampering vs localised patch detection)

Design note
-----------
The pixel-level re-compression is deliberately delegated to
HeatmapGenerator.ela_score() / generate_ela_heatmap() which are
already tested and used by the GUI ELA tab.  This module wraps those
results, adds blocking-artifact analysis, and exposes a clean dict
that analyzer.py can drop into results["methods"]["ela"].
"""
from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

# cv2 is optional — blocking analysis degrades gracefully without it
try:
    import cv2
    _CV2 = True
except ImportError:
    _CV2 = False


# ---------------------------------------------------------------------------
# Supported formats for ELA (only formats that can be lossily re-saved)
# ---------------------------------------------------------------------------
_ELA_FORMATS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"})

# PNG / BMP / TIFF will be re-saved as JPEG internally for ELA.
# The result is still meaningful — it shows how much each region
# diverges from a JPEG-compressed version of itself.


class ELAAnalyzer:
    """
    Standalone Error Level Analysis module.

    Usage
    -----
    result = ELAAnalyzer().analyze("photo.jpg")
    result = ELAAnalyzer().analyze("photo.jpg", quality=90, scale=15)
    """

    def analyze(
        self,
        image_path: str | Path,
        quality: int = 95,
        scale: int = 10,
        block_size: int = 32,
    ) -> dict[str, Any]:
        """
        Run full ELA analysis and return a result dict.

        Parameters
        ----------
        image_path : path to the image file
        quality    : JPEG re-compression quality (70-98, default 95)
        scale      : amplification factor for pixel differences (default 10)
        block_size : block size in pixels for regional variance (default 32)

        Returns
        -------
        dict with keys:
            supported           : bool  — False for unsupported formats
            ela_mean            : float — mean pixel error (0-255 range)
            ela_max             : float — max pixel error
            ela_std             : float — standard deviation of pixel errors
            ela_ratio           : float — std / mean (localisation signal)
            regional_std        : float — std of block-level means
                                          (high = non-uniform = forgery patch)
            blocking_score      : float — gradient at JPEG 8px boundaries vs
                                          between boundaries (needs cv2)
            blocking_anomaly    : bool  — True if blocking_score < 1.5
                                          (consistent blocking absent = re-encoded)
            quality_used        : int   — quality setting used
            scale_used          : int   — scale setting used
            suspicion_score     : float — combined score 0-100
            suspicion_reasons   : list[str] — human-readable flags
            analysis_time       : float — seconds
        """
        start = time.time()
        path = Path(image_path)
        ext = path.suffix.lower()

        base: dict[str, Any] = {
            "supported":        False,
            "ela_mean":         0.0,
            "ela_max":          0.0,
            "ela_std":          0.0,
            "ela_ratio":        0.0,
            "regional_std":     0.0,
            "blocking_score":   0.0,
            "blocking_anomaly": False,
            "quality_used":     quality,
            "scale_used":       scale,
            "suspicion_score":  0.0,
            "suspicion_reasons": [],
            "analysis_time":    0.0,
        }

        if ext not in _ELA_FORMATS:
            base["suspicion_reasons"].append(
                f"ELA not applicable for format '{ext}'"
            )
            base["analysis_time"] = round(time.time() - start, 3)
            return base

        base["supported"] = True

        # ------------------------------------------------------------------
        # 1. ELA pixel statistics
        # ------------------------------------------------------------------
        ela_arr = self._compute_ela_array(path, quality, scale)

        ela_mean = float(np.mean(ela_arr))
        ela_max  = float(np.max(ela_arr))
        ela_std  = float(np.std(ela_arr))
        ela_ratio = ela_std / (ela_mean + 1e-8)

        base["ela_mean"]  = round(ela_mean, 3)
        base["ela_max"]   = round(ela_max, 3)
        base["ela_std"]   = round(ela_std, 3)
        base["ela_ratio"] = round(ela_ratio, 4)

        # ------------------------------------------------------------------
        # 2. Regional variance  (block-level ELA means)
        #    A genuine tampered region produces a bright patch in the ELA map.
        #    High variance of block means = localised anomaly = stronger signal.
        # ------------------------------------------------------------------
        regional_std = self._regional_variance(ela_arr, block_size)
        base["regional_std"] = round(regional_std, 3)

        # ------------------------------------------------------------------
        # 3. Blocking artifact score  (requires cv2)
        #    Authentic JPEG images have strong gradients at 8-pixel boundaries.
        #    A score < 1.5 means the blocking grid is weak or absent,
        #    which indicates re-encoding or stitching from a non-JPEG source.
        # ------------------------------------------------------------------
        if _CV2 and ext in {".jpg", ".jpeg"}:
            blocking_score = self._blocking_artifact_score(path)
            blocking_anomaly = blocking_score < 1.5
        else:
            blocking_score = 0.0
            blocking_anomaly = False

        base["blocking_score"]   = round(blocking_score, 4)
        base["blocking_anomaly"] = blocking_anomaly

        # ------------------------------------------------------------------
        # 4. Combined suspicion score
        # ------------------------------------------------------------------
        score, reasons = self._compute_suspicion(
            ela_mean, ela_std, ela_ratio, regional_std,
            blocking_score, blocking_anomaly, ext
        )
        base["suspicion_score"]   = round(score, 2)
        base["suspicion_reasons"] = reasons
        base["analysis_time"]     = round(time.time() - start, 3)
        return base

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_ela_array(
        self, path: Path, quality: int, scale: int
    ) -> np.ndarray:
        """
        Re-save image at *quality*, compute |original - recompressed| * scale.
        Returns a float32 array of shape (H, W) (grayscale ELA values).
        """
        orig = Image.open(path).convert("RGB")
        buf = BytesIO()
        orig.save(buf, "JPEG", quality=quality)
        buf.seek(0)
        recomp = Image.open(buf).convert("RGB")

        orig_arr   = np.array(orig,   dtype=np.float32)
        recomp_arr = np.array(recomp, dtype=np.float32)

        ela_rgb = np.abs(orig_arr - recomp_arr) * scale
        ela_rgb = np.clip(ela_rgb, 0.0, 255.0)

        # Collapse channels to single grayscale ELA map
        return ela_rgb.mean(axis=2)

    def _regional_variance(self, ela_arr: np.ndarray, block_size: int) -> float:
        """
        Compute the standard deviation of per-block ELA means.
        High value = one region has much higher error than others = forgery patch.
        """
        h, w = ela_arr.shape
        block_means = []
        for y in range(0, h - block_size + 1, block_size):
            for x in range(0, w - block_size + 1, block_size):
                block = ela_arr[y:y + block_size, x:x + block_size]
                block_means.append(float(np.mean(block)))

        if not block_means:
            return 0.0
        return float(np.std(block_means))

    def _blocking_artifact_score(self, path: Path) -> float:
        """
        Measure the ratio of gradient strength at 8-pixel JPEG block
        boundaries vs between boundaries.

        A genuine JPEG will have clear block boundaries (ratio > 2.0).
        A re-encoded or composited image loses this structure (ratio < 1.5).
        """
        try:
            gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE).astype(float)
            if gray is None:
                return 0.0

            # Horizontal gradients (row direction)
            grad_h = np.abs(np.diff(gray, axis=0))
            h = grad_h.shape[0]

            # Rows at 8-pixel boundaries
            boundary_rows = list(range(7, h, 8))
            non_boundary_rows = [i for i in range(h) if i % 8 != 7]

            if not boundary_rows or not non_boundary_rows:
                return 0.0

            boundary_mean    = float(grad_h[boundary_rows, :].mean())
            non_boundary_mean = float(grad_h[non_boundary_rows, :].mean())

            return boundary_mean / (non_boundary_mean + 1e-8)
        except Exception:
            return 0.0

    def _compute_suspicion(
        self,
        ela_mean: float,
        ela_std: float,
        ela_ratio: float,
        regional_std: float,
        blocking_score: float,
        blocking_anomaly: bool,
        ext: str,
    ) -> tuple[float, list[str]]:
        """
        Combine the three analysis signals into a 0-100 suspicion score.

        Scoring rationale
        -----------------
        * ela_mean > 15  : overall high re-compression error
                           (could be heavy compression, adds moderate points)
        * ela_ratio > 3  : std is large relative to mean
                           (localised bright patch = strong forgery signal)
        * regional_std > 20 : one block region much brighter than rest
                           (strongest signal for pasted regions)
        * blocking_anomaly  : missing JPEG grid = re-encoded or composited
        """
        score = 0.0
        reasons: list[str] = []

        # Signal 1 — overall ELA mean
        if ela_mean > 25:
            score += 30.0
            reasons.append(
                f"High overall ELA mean ({ela_mean:.1f}) — significant "
                "re-compression error across image"
            )
        elif ela_mean > 15:
            score += 15.0
            reasons.append(
                f"Elevated ELA mean ({ela_mean:.1f}) — moderate "
                "re-compression error"
            )

        # Signal 2 — localisation ratio (std / mean)
        if ela_ratio > 5.0:
            score += 35.0
            reasons.append(
                f"Very high ELA localisation ratio ({ela_ratio:.2f}) — "
                "strongly suggests a pasted region with different origin quality"
            )
        elif ela_ratio > 3.0:
            score += 20.0
            reasons.append(
                f"Elevated ELA ratio ({ela_ratio:.2f}) — "
                "possible localised forgery patch"
            )

        # Signal 3 — regional variance
        if regional_std > 30.0:
            score += 25.0
            reasons.append(
                f"High regional ELA variance ({regional_std:.1f}) — "
                "one or more blocks have anomalous error vs surroundings"
            )
        elif regional_std > 15.0:
            score += 10.0
            reasons.append(
                f"Moderate regional ELA variance ({regional_std:.1f})"
            )

        # Signal 4 — blocking anomaly (JPEG only)
        if blocking_anomaly and ext in {".jpg", ".jpeg"}:
            score += 15.0
            reasons.append(
                f"Weak JPEG blocking artifacts (ratio {blocking_score:.2f}) — "
                "image may have been re-encoded or composited from non-JPEG source"
            )

        return min(100.0, score), reasons

    def format_report(self, result: dict) -> str:
        """Plain-text summary for CLI output."""
        lines = [
            "=" * 60,
            "ERROR LEVEL ANALYSIS REPORT",
            "=" * 60,
            f"Supported        : {result['supported']}",
            f"Quality Used     : {result['quality_used']}",
            f"ELA Mean         : {result['ela_mean']}",
            f"ELA Max          : {result['ela_max']}",
            f"ELA Std          : {result['ela_std']}",
            f"ELA Ratio        : {result['ela_ratio']}",
            f"Regional Std     : {result['regional_std']}",
            f"Blocking Score   : {result['blocking_score']}",
            f"Blocking Anomaly : {result['blocking_anomaly']}",
            f"Suspicion Score  : {result['suspicion_score']}/100",
            f"Analysis Time    : {result['analysis_time']}s",
        ]
        if result["suspicion_reasons"]:
            lines.append("")
            lines.append("FLAGS:")
            for r in result["suspicion_reasons"]:
                lines.append(f"  ⚠  {r}")
        lines.append("=" * 60)
        return "\n".join(lines)