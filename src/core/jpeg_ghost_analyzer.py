import numpy as np
from PIL import Image
import cv2

class JPEGGhostAnalyzer:
    """
    Detects 'ghost' artifacts caused by multiple JPEG compression cycles
    with different quality factors.
    """
    def __init__(self):
        # Common JPEG quality factors to test for ghosts
        self.test_qualities = [70, 80, 90, 95, 100]

    def analyze(self, image_path) -> dict:
        try:
            img = Image.open(image_path).convert('RGB')
            original = np.array(img).astype(np.float32)
            
            min_diff = float('inf')
            best_q = 0

            # Simulate different JPEG compression levels to find the 'ghost'
            for q in self.test_qualities:
                # Encode and decode to simulate JPEG compression
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), q]
                _, encoded_img = cv2.imencode('.jpg', original, encode_param)
                decoded_img = cv2.imdecode(encoded_img, 1)
                decoded_img = cv2.cvtColor(decoded_img, cv2.COLOR_BGR2RGB).astype(np.float32)
                
                # Calculate Mean Absolute Error (MAE)
                diff = np.mean(np.abs(original - decoded_img))
                
                if diff < min_diff:
                    min_diff = diff
                    best_q = q

            # If the difference is significantly high even at the best Q, 
            # or if the best Q is very low, it suggests double compression.
            suspicion_score = 0.0
            if min_diff > 2.0: # Threshold for noise/artifacts
                suspicion_score = min(100.0, min_diff * 10)

            return {
                "best_fit_quality": best_q,
                "min_mae": round(float(min_diff), 4),
                "suspicion_score": round(suspicion_score, 2),
                "method": "JPEG Ghost Analysis"
            }
        except Exception as e:
            return {"error": str(e), "suspicion_score": 0.0}
