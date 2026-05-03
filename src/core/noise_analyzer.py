import numpy as np
import cv2
from PIL import Image
from scipy.stats import entropy
from scipy.special import expit


class NoiseAnalyzer:
    """
    Advanced residual noise forensic analyzer.
    Detects embedding-induced inconsistencies in high-frequency residual space.
    """

    def _residual_entropy(self, residual):
        hist, _ = np.histogram(residual.flatten(), bins=256)
        probs = hist / max(np.sum(hist), 1)
        probs = probs[probs > 0]
        return entropy(probs, base=2)

    def _local_noise_irregularity(self, residual):
        h, w = residual.shape
        patch = max(min(h, w) // 20, 8)

        vars_ = []
        for y in range(0, h - patch, patch):
            for x in range(0, w - patch, patch):
                roi = residual[y:y+patch, x:x+patch]
                vars_.append(np.var(roi))

        return np.std(vars_) if vars_ else 0.0

    def analyze(self, image_path) -> dict:
        try:
            img = Image.open(image_path).convert('L')
            img_array = np.array(img).astype(np.float32)

            # Laplacian residual
            laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
            lap_abs = np.abs(laplacian)

            noise_std = np.std(lap_abs)
            noise_var = np.var(lap_abs)

            # Residual entropy
            res_entropy = self._residual_entropy(lap_abs)

            # Local irregularity
            local_irregularity = self._local_noise_irregularity(lap_abs)

            # Median filter mismatch residual
            median_filtered = cv2.medianBlur(img_array.astype(np.uint8), 3)
            mismatch = np.abs(img_array - median_filtered)
            mismatch_mean = np.mean(mismatch)

            # Adaptive anomaly scores
            std_score = float(expit((noise_std - 10) / 2.5) * 100)
            entropy_score = float(expit((res_entropy - 5.8) * 2.2) * 100)
            irregularity_score = float(expit((local_irregularity - 18) / 4) * 100)
            mismatch_score = float(expit((mismatch_mean - 2.5) * 1.8) * 100)

            suspicion_score = (
                std_score * 0.30 +
                entropy_score * 0.25 +
                irregularity_score * 0.25 +
                mismatch_score * 0.20
            )

            confidence = 100 - np.std([std_score, entropy_score, irregularity_score, mismatch_score])

            return {
                "noise_std": round(float(noise_std), 4),
                "noise_variance": round(float(noise_var), 4),
                "residual_entropy": round(float(res_entropy), 4),
                "local_noise_irregularity": round(float(local_irregularity), 4),
                "median_mismatch_mean": round(float(mismatch_mean), 4),

                "noise_std_score": round(std_score, 2),
                "noise_entropy_score": round(entropy_score, 2),
                "noise_irregularity_score": round(irregularity_score, 2),
                "noise_mismatch_score": round(mismatch_score, 2),

                "noise_confidence": round(float(max(min(confidence, 100), 0)), 2),
                "suspicion_score": round(float(min(suspicion_score, 100)), 2),
                "method": "Advanced Residual Noise Analysis"
            }

        except Exception as e:
            return {"error": str(e), "suspicion_score": 0.0}