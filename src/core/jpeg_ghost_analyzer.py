import numpy as np
from PIL import Image
import cv2
from scipy.special import expit


class JPEGGhostAnalyzer:
    """
    Advanced blockwise JPEG ghost forensic analyzer.
    Detects double-compression and localized recompression inconsistencies.
    """

    def __init__(self):
        self.test_qualities = [60, 70, 80, 85, 90, 95, 100]

    def _block_irregularity(self, diff_map, block=16):
        h, w = diff_map.shape
        vals = []

        for y in range(0, h - block, block):
            for x in range(0, w - block, block):
                roi = diff_map[y:y+block, x:x+block]
                vals.append(np.mean(roi))

        return np.std(vals) if vals else 0.0

    def analyze(self, image_path) -> dict:
        try:
            img = Image.open(image_path).convert('RGB')
            original = np.array(img).astype(np.float32)

            min_global_mae = float('inf')
            best_q = 0
            best_diff_map = None

            for q in self.test_qualities:
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), q]
                _, encoded_img = cv2.imencode('.jpg', cv2.cvtColor(original.astype(np.uint8), cv2.COLOR_RGB2BGR), encode_param)
                decoded_img = cv2.imdecode(encoded_img, 1)
                decoded_img = cv2.cvtColor(decoded_img, cv2.COLOR_BGR2RGB).astype(np.float32)

                abs_diff = np.mean(np.abs(original - decoded_img), axis=2)
                global_mae = np.mean(abs_diff)

                if global_mae < min_global_mae:
                    min_global_mae = global_mae
                    best_q = q
                    best_diff_map = abs_diff

            # Blockwise recompression irregularity
            block_irregularity = self._block_irregularity(best_diff_map, block=16)

            # Hotspot intensity
            hotspot_score_raw = np.percentile(best_diff_map, 95) - np.percentile(best_diff_map, 50)

            # Adaptive anomaly scoring
            mae_score = float(expit((min_global_mae - 1.5) * 2.0) * 100)
            irregularity_score = float(expit((block_irregularity - 0.8) * 3.0) * 100)
            hotspot_score = float(expit((hotspot_score_raw - 1.2) * 2.5) * 100)

            # unusual best fit quality can also indicate prior compression mismatch
            quality_score = float((1 - min(abs(best_q - 95) / 35, 1.0)) * 100)

            suspicion_score = (
                mae_score * 0.30 +
                irregularity_score * 0.30 +
                hotspot_score * 0.25 +
                quality_score * 0.15
            )

            confidence = 100 - np.std([mae_score, irregularity_score, hotspot_score, quality_score])

            return {
                "best_fit_quality": int(best_q),
                "min_global_mae": round(float(min_global_mae), 4),
                "block_irregularity": round(float(block_irregularity), 4),
                "ghost_hotspot_intensity": round(float(hotspot_score_raw), 4),

                "mae_score": round(mae_score, 2),
                "block_irregularity_score": round(irregularity_score, 2),
                "ghost_hotspot_score": round(hotspot_score, 2),
                "quality_anomaly_score": round(quality_score, 2),

                "jpeg_ghost_confidence": round(float(max(min(confidence, 100), 0)), 2),
                "suspicion_score": round(float(min(suspicion_score, 100)), 2),
                "method": "Advanced JPEG Ghost Analysis"
            }

        except Exception as e:
            return {"error": str(e), "suspicion_score": 0.0}