"""
Tests for the ML-based steganography classifier.
"""
import unittest
import tempfile
from pathlib import Path
from PIL import Image
import numpy as np


def _make_temp_images(n: int, directory: Path, label: str) -> list[str]:
    """Create *n* synthetic PNG images in *directory*."""
    paths = []
    for i in range(n):
        arr = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)
        p = directory / f"{label}_{i}.png"
        Image.fromarray(arr).save(p)
        paths.append(str(p))
    return paths


class TestMLFeatureExtractor(unittest.TestCase):
    def setUp(self):
        arr = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        self.tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        Image.fromarray(arr).save(self.tmp.name)

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_extract_features_returns_dict(self):
        from src.core.ml_features import MLFeatureExtractor
        extractor = MLFeatureExtractor()
        features = extractor.extract_features(self.tmp.name)
        self.assertIsInstance(features, dict)
        self.assertGreater(len(features), 0)

    def test_no_nan_in_features(self):
        import math
        from src.core.ml_features import MLFeatureExtractor
        extractor = MLFeatureExtractor()
        features = extractor.extract_features(self.tmp.name)
        for key, val in features.items():
            self.assertFalse(math.isnan(val), f"NaN found for feature '{key}'")

    def test_features_to_vector_length_matches_names(self):
        from src.core.ml_features import MLFeatureExtractor
        extractor = MLFeatureExtractor()
        features = extractor.extract_features(self.tmp.name)
        vector = extractor.features_to_vector(features)
        self.assertEqual(len(vector), len(extractor.feature_names))


class TestMLClassifierTrainPredict(unittest.TestCase):
    def test_train_and_predict(self):
        from src.core.ml_classifier import MLSteganalysisClassifier
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            clean_dir = tmp / "clean"
            stego_dir = tmp / "stego"
            clean_dir.mkdir()
            stego_dir.mkdir()
            model_path = str(tmp / "model.pkl")

            clean_images = _make_temp_images(6, clean_dir, "clean")
            stego_images = _make_temp_images(6, stego_dir, "stego")

            clf = MLSteganalysisClassifier()
            metrics = clf.train_model(clean_images, stego_images, model_path, test_size=0.3)

            self.assertIn("accuracy", metrics)
            self.assertGreaterEqual(metrics["accuracy"], 0.0)
            self.assertLessEqual(metrics["accuracy"], 1.0)

            # Predict on a new image
            result = clf.predict(clean_images[0])
            self.assertIn("prediction", result)
            self.assertIn(result["prediction"], [0, 1])
            self.assertGreaterEqual(result["probability"], 0.0)
            self.assertLessEqual(result["probability"], 1.0)


if __name__ == "__main__":
    unittest.main()