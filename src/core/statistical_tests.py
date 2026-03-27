import numpy as np
from scipy.stats import entropy

def chi_square_test(image):
    """Chi-square test for pixel value distribution"""
    img_array = np.array(image.convert('L'))  # Grayscale
    hist, bins = np.histogram(img_array.flatten(), bins=256, range=[0, 256])
    probabilities = hist / hist.sum()
    ent = entropy(probabilities, base=2)
    
    # Higher entropy may indicate hidden data
    suspicion_score = min(100, ent * 15)  # Heuristic scaling
    
    return {
        'entropy': ent,
        'histogram': hist.tolist(),
        'suspicion_score': suspicion_score
    }

def pixel_value_differencing(image):
    """Analyze differences between adjacent pixels"""
    img_array = np.array(image.convert('L'))  # Grayscale
    diff = np.diff(img_array, axis=1)
    diff_mean = np.mean(diff)
    diff_std = np.std(diff)
    
    # Higher standard deviation suggests more randomness
    suspicion_score = min(100, diff_std * 5)
    
    return {
        'diff_mean': float(diff_mean),
        'diff_std': float(diff_std),
        'suspicion_score': suspicion_score
    }
