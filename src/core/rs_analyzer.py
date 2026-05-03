import numpy as np
from PIL import Image


class RSAnalyzer:
    """
    Regular/Singular (RS) Steganalysis.
    Detects LSB embedding by measuring smoothness changes
    under controlled flipping masks.
    """

    def __init__(self):
        self.mask = np.array([1, -1, 1, -1])

    def _discrimination(self, group):
        """
        Smoothness discrimination function.
        """
        return np.sum(np.abs(np.diff(group)))

    def _flip(self, group, mask_type=1):
        flipped = group.copy()

        for i in range(len(group)):
            if self.mask[i] == mask_type:
                if flipped[i] % 2 == 0:
                    flipped[i] += 1
                else:
                    flipped[i] -= 1

        return flipped

    def _count_rs(self, values):
        regular = 0
        singular = 0

        for i in range(0, len(values) - 4, 4):
            group = values[i:i+4]

            original_d = self._discrimination(group)
            flipped_d = self._discrimination(self._flip(group, 1))

            if flipped_d > original_d:
                regular += 1
            elif flipped_d < original_d:
                singular += 1

        return regular, singular

    def analyze(self, image_path):
        try:
            img = Image.open(image_path).convert("L")
            arr = np.array(img).flatten().astype(np.int32)

            R, S = self._count_rs(arr)

            total = R + S
            if total == 0:
                score = 0.0
                imbalance = 0.0
            else:
                imbalance = abs(R - S) / total
                embedding_estimate = 1.0 - imbalance
                score = embedding_estimate * 100

            return {
                "regular_groups": int(R),
                "singular_groups": int(S),
                "rs_imbalance": round(float(imbalance), 4),
                "suspicion_score": round(float(score), 2),
                "method": "Regular Singular Statistical Analysis"
            }

        except Exception as e:
            return {
                "error": str(e),
                "suspicion_score": 0.0
            }