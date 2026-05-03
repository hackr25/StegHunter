from PIL import Image
import numpy as np
from scipy.stats import entropy, chisquare
from scipy.special import expit


def extract_lsb_plane(image):
    """Extract grayscale LSB plane."""
    img_array = np.array(image)

    if len(img_array.shape) == 3:
        img_array = np.mean(img_array, axis=2).astype(np.uint8)

    return img_array & 1


def lsb_histogram(lsb_plane):
    """Return count of zeros and ones."""
    unique, counts = np.unique(lsb_plane, return_counts=True)
    hist = dict(zip(unique, counts))
    return hist.get(0, 0), hist.get(1, 0)


def lsb_entropy_score(lsb_plane):
    """Entropy-based anomaly score."""
    counts = np.bincount(lsb_plane.ravel(), minlength=2)
    probs = counts / max(counts.sum(), 1)
    ent = entropy(probs, base=2)

    # sigmoid anomaly mapping centered near 0.93
    anomaly = float(expit((ent - 0.93) * 18))
    return ent, anomaly * 100


def lsb_balance_score(count0, count1):
    """Near-perfect 50/50 balance can indicate embedding."""
    total = count0 + count1
    if total == 0:
        return 0.0, 0.0

    ratio = count1 / total
    deviation = abs(ratio - 0.5)

    # smaller deviation = more suspicious
    suspicion = (1 - min(deviation / 0.08, 1.0)) * 100
    return ratio, suspicion


def lsb_spatial_correlation_score(lsb_plane):
    """Measure local LSB adjacency correlation."""
    try:
        horiz_corr = np.corrcoef(lsb_plane[:, :-1].ravel(), lsb_plane[:, 1:].ravel())[0, 1]
        vert_corr = np.corrcoef(lsb_plane[:-1, :].ravel(), lsb_plane[1:, :].ravel())[0, 1]

        horiz_corr = 0 if np.isnan(horiz_corr) else horiz_corr
        vert_corr = 0 if np.isnan(vert_corr) else vert_corr

        avg_corr = abs((horiz_corr + vert_corr) / 2)

        # lower correlation = more random = suspicious
        suspicion = (1 - min(avg_corr / 0.15, 1.0)) * 100
        return avg_corr, suspicion
    except:
        return 0.0, 0.0


def lsb_uniformity_score(count0, count1):
    """Continuous chi-square confidence mapping."""
    total = count0 + count1
    if total == 0:
        return 1.0, 0.0

    expected = total / 2
    chi2_stat, p_value = chisquare([count0, count1], [expected, expected])

    # high p-value near uniform = suspicious
    suspicion = min(p_value * 100, 100)
    return p_value, suspicion


def lsb_analysis(image):
    """Adaptive probabilistic LSB steganalysis."""
    lsb_plane = extract_lsb_plane(image)
    count0, count1 = lsb_histogram(lsb_plane)

    ent, entropy_score = lsb_entropy_score(lsb_plane)
    ratio, balance_score = lsb_balance_score(count0, count1)
    spatial_corr, spatial_score = lsb_spatial_correlation_score(lsb_plane)
    p_value, uniformity_score = lsb_uniformity_score(count0, count1)

    # weighted adaptive fusion
    suspicion_score = (
        entropy_score * 0.30 +
        balance_score * 0.25 +
        spatial_score * 0.25 +
        uniformity_score * 0.20
    )

    confidence = np.std([entropy_score, balance_score, spatial_score, uniformity_score])

    return {
        'entropy': ent,
        'lsb_counts': {'0': count0, '1': count1},
        'lsb_one_ratio': ratio,
        'spatial_lsb_correlation': spatial_corr,
        'lsb_uniformity_p_value': p_value,
        'lsb_entropy_score': entropy_score,
        'lsb_balance_score': balance_score,
        'lsb_spatial_score': spatial_score,
        'lsb_uniformity_score': uniformity_score,
        'lsb_confidence': float(100 - min(confidence, 100)),
        'lsb_suspicion_score': float(min(suspicion_score, 100))
    }