import numpy as np
from PIL import Image
from scipy.stats import entropy

class ColorSpaceAnalyzer:
    """
    Analyzes images in YCbCr and HSV color spaces. 
    Hidden data often creates anomalies in Chrominance channels.
    """
    def analyze(self, image_path) -> dict:
        try:
            img = Image.open(image_path).convert('RGB')
            img_array = np.array(img)

            # Convert RGB to YCbCr (Luminance, Blue-difference, Red-difference)
            # Y = 0.299R + 0.587G + 0.114B
            # Cb and Cr are the color components
            ycbcr = self._rgb_to_ycbcr(img_array)
            
            # Calculate entropy for Cb and Cr channels separately
            cb_entropy = self._calculate_entropy(ycbcr[:, :, 1])
            cr_entropy = self._calculate_entropy(ycbcr[:, :, 2])
            
            # In natural images, Cb and Cr entropy is usually lower than Y.
            # If Cb/Cr entropy is unusually high, it suggests hidden data.
            avg_color_entropy = (cb_entropy + cr_entropy) / 2
            
            suspicion_score = 0.0
            if avg_color_entropy > 7.0: # Entropy threshold for 8-bit channels
                suspicion_score = min(100.0, (avg_color_entropy - 7.0) * 20)

            return {
                "cb_entropy": round(cb_entropy, 4),
                "cr_entropy": round(cr_entropy, 4),
                "suspicion_score": round(suspicion_score, 2),
                "method": "Color Space Analysis"
            }
        except Exception as e:
            return {"error": str(e), "suspicion_score": 0.0}

    def _rgb_to_ycbcr(self, rgb):
        # Simplified RGB to YCbCr conversion
        x = np.dot(rgb[...,:3], [0.299, 0.587, 0.114])
        cb = np.dot(rgb[...,:3], [-0.1687, -0.3313, 0.5]) + 128
        cr = np.dot(rgb[...,:3], [0.5, -0.4187, -0.0813]) + 128
        return np.stack([x, cb, cr], axis=-1)

    def _calculate_entropy(self, data):
        hist = np.histogram(data, bins=256, range=(0, 256))[0]
        probs = hist / np.sum(hist)
        probs = probs[probs > 0]
        return -np.sum(probs * np.log2(probs))
