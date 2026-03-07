from PIL import Image
import numpy as np
from scipy.stats import entropy

def extract_lsb_plane(image):
    """Extract LSB plane from image (0 or 1 for each pixel)"""
    img_array = np.array(image)
    lsb_plane = img_array & 1
    return lsb_plane

def lsb_histogram(lsb_plane):
    """Count 0s and 1s in LSB plane"""
    unique, counts = np.unique(lsb_plane, return_counts=True)
    hist = dict(zip(unique, counts))
    if 0 not in hist:
        hist[0] = 0
    if 1 not in hist:
        hist[1] = 0
    return hist[0], hist[1]

def lsb_entropy(lsb_plane):
    """Calculate entropy of LSB plane (higher = more random)"""
    counts = np.bincount(lsb_plane.ravel())
    probabilities = counts / counts.sum()
    return entropy(probabilities, base=2)

def lsb_uniformity_test(count0, count1, alpha=0.05):
    """Chi-square test for LSB uniformity"""
    from scipy.stats import chisquare
    total = count0 + count1
    if total == 0:
        return 1.0, False
    expected = total / 2
    observed = [count0, count1]
    chi2_stat, p_value = chisquare(f_obs=observed, f_exp=[expected, expected])
    reject_null = p_value < alpha
    return p_value, reject_null

def lsb_analysis(image):
    """Complete LSB analysis with suspicion score"""
    lsb_plane = extract_lsb_plane(image)
    count0, count1 = lsb_histogram(lsb_plane)
    ent = lsb_entropy(lsb_plane)
    p_value, reject_null = lsb_uniformity_test(count0, count1)

    # Calculate suspicion score
    suspicion_score = ent * 50  # Max 50 from entropy
    if reject_null:
        suspicion_score += 30    # Additional 30 if LSB not uniform
    suspicion_score = min(100, suspicion_score)

    return {
        'entropy': ent,
        'lsb_counts': {'0': count0, '1': count1},
        'lsb_uniformity_p_value': p_value,
        'lsb_uniformity_reject': reject_null,
        'lsb_suspicion_score': suspicion_score
    }
