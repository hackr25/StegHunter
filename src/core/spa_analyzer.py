import numpy as np
from PIL import Image


class SPAAnalyzer:
    """
    Sample Pair Analysis (SPA)
    Estimates LSB replacement embedding by analyzing
    neighboring grayscale pair transitions.
    """

    def __init__(self):
        pass

    def analyze(self, image_path):
        try:
            img = Image.open(image_path).convert("L")
            arr = np.array(img, dtype=np.int32)

            flat = arr.flatten()

            x = 0
            y = 0
            k = 0

            for i in range(0, len(flat) - 1, 2):
                a = flat[i]
                b = flat[i + 1]

                if a == b:
                    continue

                if (a % 2 == 0 and b == a + 1) or (b % 2 == 0 and a == b + 1):
                    x += 1

                if abs(a - b) == 1:
                    y += 1

                k += 1

            if k == 0 or y == 0:
                payload = 0.0
            else:
                payload = min(1.0, x / y)

            suspicion_score = payload * 100

            return {
                "sample_pairs_examined": int(k),
                "spa_transition_matches": int(x),
                "spa_adjacent_pairs": int(y),
                "estimated_payload_ratio": round(float(payload), 4),
                "suspicion_score": round(float(suspicion_score), 2),
                "method": "Sample Pair Analysis"
            }

        except Exception as e:
            return {
                "error": str(e),
                "suspicion_score": 0.0
            }