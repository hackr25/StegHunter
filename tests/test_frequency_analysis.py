"""
Tests for the frequency-domain analysis module.
"""
import unittest
from pathlib import Path
from PIL import Image
import numpy as np


class TestFrequencyAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create a simple synthetic image for testing
        arr = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        self.image = Image.fromarray(arr)

    def test_fft_analysis_returns_expected_keys(self):
        from src.core.frequency_analysis import FrequencyAnalyzer
        analyzer = FrequencyAnalyzer()
        result = analyzer.fft_analysis(self.image)
        expected_keys = {
            "fft_mean", "fft_std", "fft_variance", "fft_max", "fft_min",
            "fft_range", "phase_mean", "phase_std",
            "high_freq_energy", "low_freq_energy", "spectral_flatness",
        }
        self.assertEqual(expected_keys, set(result.keys()))

    def test_fft_analysis_values_are_finite(self):
        from src.core.frequency_analysis import FrequencyAnalyzer
        import math
        analyzer = FrequencyAnalyzer()
        result = analyzer.fft_analysis(self.image)
        for key, value in result.items():
            self.assertTrue(math.isfinite(value), f"{key} is not finite: {value}")

    def test_dct_analysis_returns_expected_keys(self):
        from src.core.frequency_analysis import FrequencyAnalyzer
        analyzer = FrequencyAnalyzer()
        result = analyzer.dct_analysis(self.image)
        self.assertIn("dct_mean", result)
        self.assertIn("dct_std", result)

    def test_fft_accepts_grayscale(self):
        from src.core.frequency_analysis import FrequencyAnalyzer
        analyzer = FrequencyAnalyzer()
        gray = self.image.convert("L")
        result = analyzer.fft_analysis(gray)
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()