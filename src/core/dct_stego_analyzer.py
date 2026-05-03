import cv2
import numpy as np
from PIL import Image


class DCTStegoAnalyzer:
    """
    JPEG DCT coefficient anomaly detector.
    Estimates transform-domain steganographic embedding by
    analyzing blockwise frequency coefficient distributions.
    """

    def __init__(self):
        pass

    def _block_dct(self, gray):
        h, w = gray.shape
        h8 = h - (h % 8)
        w8 = w - (w % 8)
        gray = gray[:h8, :w8]

        coeffs = []

        for y in range(0, h8, 8):
            for x in range(0, w8, 8):
                block = np.float32(gray[y:y+8, x:x+8]) - 128.0
                dct = cv2.dct(block)
                coeffs.append(dct)

        return coeffs

    def analyze(self, image_path):
        try:
            img = Image.open(image_path).convert("L")
            gray = np.array(img, dtype=np.float32)

            coeff_blocks = self._block_dct(gray)

            if not coeff_blocks:
                return {
                    "suspicion_score": 0.0,
                    "method": "DCT Coefficient Analysis"
                }

            ac_values = []

            for block in coeff_blocks:
                # Ignore DC coefficient [0,0]
                ac = block.flatten()[1:]
                ac_values.extend(ac)

            ac_values = np.array(ac_values)

            near_zero = np.sum(np.abs(ac_values) < 1.5)
            moderate = np.sum((np.abs(ac_values) >= 1.5) & (np.abs(ac_values) < 8))

            total = len(ac_values)

            if total == 0:
                score = 0.0
                ratio = 0.0
            else:
                ratio = near_zero / total
                distribution_balance = moderate / total

                # JPEG stego often over-populates near-zero AC coefficients
                score = min(100.0, ((ratio * 0.7) + ((1 - distribution_balance) * 0.3)) * 100)

            return {
                "total_ac_coefficients": int(total),
                "near_zero_ratio": round(float(ratio), 4),
                "midband_distribution": round(float(distribution_balance), 4),
                "suspicion_score": round(float(score), 2),
                "method": "JPEG DCT Coefficient Statistical Analysis"
            }

        except Exception as e:
            return {
                "error": str(e),
                "suspicion_score": 0.0
            }