import numpy as np
from scipy.stats import entropy, chisquare, kurtosis
from scipy.special import expit


def chi_square_test(image):
    """
    Enhanced grayscale pair-frequency chi-square forensic test.
    """
    img_array = np.array(image.convert('L'))
    flat = img_array.flatten()

    hist, _ = np.histogram(flat, bins=256, range=[0, 256])
    probs = hist / max(hist.sum(), 1)
    hist_entropy = entropy(probs, base=2)

    # Pair frequencies (0-1,2-3,...)
    observed = []
    expected = []

    for i in range(0, 256, 2):
        pair_sum = hist[i] + hist[i+1]
        observed.extend([hist[i], hist[i+1]])
        # Add pseudocount to avoid division by zero
        expected.extend([max(pair_sum/2, 0.5), max(pair_sum/2, 0.5)])

    chi2_stat, p_value = chisquare(f_obs=observed, f_exp=expected)
    
    # Handle NaN p-value
    if np.isnan(p_value):
        p_value = 0.0
    if np.isnan(chi2_stat):
        chi2_stat = 0.0

    entropy_score = float(expit((hist_entropy - 7.2) * 2.5) * 100)
    uniformity_score = float(min(p_value * 100, 100))

    suspicion_score = entropy_score * 0.55 + uniformity_score * 0.45

    return {
        'histogram_entropy': float(hist_entropy),
        'chi_square_p_value': float(p_value),
        'chi_square_entropy_score': entropy_score,
        'chi_square_uniformity_score': uniformity_score,
        'suspicion_score': float(min(suspicion_score, 100))
    }


def pixel_value_differencing(image):
    """
    Enhanced adjacent residual randomness analysis.
    """
    img_array = np.array(image.convert('L')).astype(np.float32)

    h_diff = np.diff(img_array, axis=1)
    v_diff = np.diff(img_array, axis=0)

    all_diff = np.concatenate([h_diff.ravel(), v_diff.ravel()])

    diff_mean = np.mean(all_diff)
    diff_std = np.std(all_diff)
    diff_kurt = kurtosis(all_diff, fisher=False)

    # local smoothness map
    local_var = []
    h, w = img_array.shape
    step = max(min(h, w) // 20, 8)

    for y in range(0, h-step, step):
        for x in range(0, w-step, step):
            patch = img_array[y:y+step, x:x+step]
            local_var.append(np.var(patch))

    smoothness_irregularity = np.std(local_var) if local_var else 0.0

    std_score = float(expit((diff_std - 22) / 4) * 100)
    kurtosis_score = float(expit((3.8 - diff_kurt) * 2) * 100)
    smoothness_score = float(expit((smoothness_irregularity - 120) / 20) * 100)

    suspicion_score = (
        std_score * 0.40 +
        kurtosis_score * 0.30 +
        smoothness_score * 0.30
    )

    confidence = 100 - np.std([std_score, kurtosis_score, smoothness_score])

    return {
        'diff_mean': float(diff_mean),
        'diff_std': float(diff_std),
        'diff_kurtosis': float(diff_kurt),
        'smoothness_irregularity': float(smoothness_irregularity),
        'pvd_std_score': std_score,
        'pvd_kurtosis_score': kurtosis_score,
        'pvd_smoothness_score': smoothness_score,
        'pvd_confidence': float(max(min(confidence, 100), 0)),
        'suspicion_score': float(min(suspicion_score, 100))
    }