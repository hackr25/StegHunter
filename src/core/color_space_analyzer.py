import numpy as np
from PIL import Image
from scipy.stats import entropy
from scipy.special import expit
import cv2


class ColorSpaceAnalyzer:
    """
    Advanced chromatic forensic analyzer.
    Detects hidden-data artifacts through chrominance entropy,
    luminance correlation disruption, and saturation irregularity.
    """

    def _rgb_to_ycbcr(self, rgb):
        y = np.dot(rgb[..., :3], [0.299, 0.587, 0.114])
        cb = np.dot(rgb[..., :3], [-0.1687, -0.3313, 0.5]) + 128
        cr = np.dot(rgb[..., :3], [0.5, -0.4187, -0.0813]) + 128
        return np.stack([y, cb, cr], axis=-1)

    def _calculate_entropy(self, data):
        hist = np.histogram(data, bins=256, range=(0, 256))[0]
        probs = hist / max(np.sum(hist), 1)
        probs = probs[probs > 0]
        return -np.sum(probs * np.log2(probs))

    def _local_variance_irregularity(self, channel):
        h, w = channel.shape
        patch = max(min(h, w) // 20, 8)

        vars_ = []
        for y in range(0, h - patch, patch):
            for x in range(0, w - patch, patch):
                roi = channel[y:y+patch, x:x+patch]
                vars_.append(np.var(roi))

        return np.std(vars_) if vars_ else 0.0

    def analyze(self, image_path) -> dict:
        try:
            img = Image.open(image_path).convert('RGB')
            img_array = np.array(img).astype(np.float32)

            ycbcr = self._rgb_to_ycbcr(img_array)

            y = ycbcr[:, :, 0]
            cb = ycbcr[:, :, 1]
            cr = ycbcr[:, :, 2]

            cb_entropy = self._calculate_entropy(cb)
            cr_entropy = self._calculate_entropy(cr)

            cb_corr = np.corrcoef(y.flatten(), cb.flatten())[0, 1]
            cr_corr = np.corrcoef(y.flatten(), cr.flatten())[0, 1]

            cb_corr = 0 if np.isnan(cb_corr) else cb_corr
            cr_corr = 0 if np.isnan(cr_corr) else cr_corr

            avg_corr = abs((cb_corr + cr_corr) / 2)

            cb_local_irreg = self._local_variance_irregularity(cb)
            cr_local_irreg = self._local_variance_irregularity(cr)
            chroma_irregularity = (cb_local_irreg + cr_local_irreg) / 2

            hsv = cv2.cvtColor(img_array.astype(np.uint8), cv2.COLOR_RGB2HSV)
            sat = hsv[:, :, 1]
            sat_entropy = self._calculate_entropy(sat)

            # Adaptive anomaly scores
            cb_score = float(expit((cb_entropy - 6.9) * 2.0) * 100)
            cr_score = float(expit((cr_entropy - 6.9) * 2.0) * 100)

            corr_score = float((1 - min(avg_corr / 0.18, 1.0)) * 100)

            chroma_irreg_score = float(expit((chroma_irregularity - 55) / 10) * 100)
            sat_score = float(expit((sat_entropy - 6.5) * 1.8) * 100)

            suspicion_score = (
                cb_score * 0.22 +
                cr_score * 0.22 +
                corr_score * 0.22 +
                chroma_irreg_score * 0.18 +
                sat_score * 0.16
            )

            confidence = 100 - np.std([cb_score, cr_score, corr_score, chroma_irreg_score, sat_score])

            return {
                "cb_entropy": round(float(cb_entropy), 4),
                "cr_entropy": round(float(cr_entropy), 4),
                "ycbcr_avg_correlation": round(float(avg_corr), 4),
                "chroma_local_irregularity": round(float(chroma_irregularity), 4),
                "saturation_entropy": round(float(sat_entropy), 4),

                "cb_entropy_score": round(cb_score, 2),
                "cr_entropy_score": round(cr_score, 2),
                "corr_disruption_score": round(corr_score, 2),
                "chroma_irregularity_score": round(chroma_irreg_score, 2),
                "saturation_score": round(sat_score, 2),

                "color_confidence": round(float(max(min(confidence, 100), 0)), 2),
                "suspicion_score": round(float(min(suspicion_score, 100)), 2),
                "method": "Advanced Color Space Analysis"
            }

        except Exception as e:
            return {"error": str(e), "suspicion_score": 0.0}