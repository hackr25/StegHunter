import os
import cv2
import numpy as np
import tensorflow as tf
from PIL import Image


class ResidualPreprocessor:
    """
    SRM-inspired residual preprocessing.
    Suppresses semantic image content and exposes embedding artifacts.
    """

    def __init__(self):
        self.kernels = [
            np.array([[0, -1, 0],
                      [-1, 4, -1],
                      [0, -1, 0]], dtype=np.float32),

            np.array([[-1, 2, -1],
                      [2, -4, 2],
                      [-1, 2, -1]], dtype=np.float32),

            np.array([[1, -2, 1],
                      [-2, 4, -2],
                      [1, -2, 1]], dtype=np.float32)
        ]

    def process(self, img_array):
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)

        residual_maps = []
        for k in self.kernels:
            filtered = cv2.filter2D(gray, -1, k)
            residual_maps.append(filtered)

        stacked = np.stack(residual_maps, axis=-1)
        stacked = np.clip(stacked, -20, 20) / 20.0
        return stacked.astype(np.float32)


class DeepStegoAnalyzer:
    """
    TensorFlow CNN based steganographic detector.
    """

    def __init__(self, model_path="models/deep_stego_cnn.h5"):
        self.preprocessor = ResidualPreprocessor()
        self.model_loaded = False
        self.model = self._build_model()

        if os.path.exists(model_path):
            try:
                self.model.load_weights(model_path)
                self.model_loaded = True
            except Exception:
                self.model_loaded = False

    def _build_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(128, 128, 3)),

            tf.keras.layers.Conv2D(16, (3, 3), padding="same", activation="relu"),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.MaxPooling2D((2, 2)),

            tf.keras.layers.Conv2D(32, (3, 3), padding="same", activation="relu"),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.MaxPooling2D((2, 2)),

            tf.keras.layers.Conv2D(64, (3, 3), padding="same", activation="relu"),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.MaxPooling2D((2, 2)),

            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(128, activation="relu"),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(2, activation="softmax")
        ])

        model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"]
        )

        return model

    def _prepare_input(self, image_path):
        img = Image.open(image_path).convert("RGB")
        img = img.resize((128, 128))
        img_array = np.array(img)

        residual = self.preprocessor.process(img_array)
        residual = np.expand_dims(residual, axis=0)

        return residual

    def analyze(self, image_path):
        if not self.model_loaded:
            return {
                "deep_learning_score": None,
                "deep_learning_confidence": None,
                "method": "Deep CNN unavailable (model not trained)"
            }

        try:
            x = self._prepare_input(image_path)
            probs = self.model.predict(x, verbose=0)[0]

            stego_prob = float(probs[1] * 100)
            confidence = float(abs(probs[1] - probs[0]) * 100)

            return {
                "deep_learning_score": round(stego_prob, 2),
                "deep_learning_confidence": round(confidence, 2),
                "method": "TensorFlow Residual Deep CNN Steganalyzer"
            }

        except Exception as e:
            return {
                "error": str(e),
                "deep_learning_score": None,
                "deep_learning_confidence": None
            }