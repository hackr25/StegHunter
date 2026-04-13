import numpy as np
import cv2
from PIL import Image

class NoiseAnalyzer:
    """
    Analyzes high-frequency noise components to detect 
    artificial patterns introduced by data embedding.
    """
    def analyze(self, image_path) -> dict:
        try:
            img = Image.open(image_path).convert('L') # Grayscale
            img_array = np.array(img)

            # Use Laplacian filter to extract high-frequency noise
            # This removes the 'content' and leaves the 'noise'
            laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
            
            noise_std = np.std(laplacian)
            noise_var = np.var(laplacian)
            
            # Natural images have a specific noise profile. 
            # Excessively high variance in the Laplacian often indicates 
            # modification or hidden data.
            suspicion_score = 0.0
            if noise_std > 15.0: # Heuristic threshold
                suspicion_score = min(100.0, (noise_std - 15.0) * 2)

            return {
                "noise_std": round(float(noise_std), 4),
                "noise_variance": round(float(noise_var), 4),
                "suspicion_score": round(suspicion_score, 2),
                "method": "Noise Analysis"
            }
        except Exception as e:
            return {"error": str(e), "suspicion_score": 0.0}
