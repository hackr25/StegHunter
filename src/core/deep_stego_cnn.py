import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from PIL import Image
import cv2
import os


class ResidualPreprocessor:
    """
    Apply SRM-inspired high-pass residual filters
    to suppress image semantics and expose embedding artifacts.
    """

    def __init__(self):
        self.kernels = [
            np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], dtype=np.float32),
            np.array([[-1, 2, -1], [2, -4, 2], [-1, 2, -1]], dtype=np.float32),
            np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float32)
        ]

    def process(self, img_array):
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)

        residual_maps = []
        for k in self.kernels:
            filtered = cv2.filter2D(gray, -1, k)
            residual_maps.append(filtered)

        stacked = np.stack(residual_maps, axis=0)
        stacked = np.clip(stacked, -20, 20) / 20.0
        return stacked.astype(np.float32)


class DeepStegoCNN(nn.Module):
    """
    Lightweight forensic CNN for steganographic residual learning.
    """

    def __init__(self):
        super(DeepStegoCNN, self).__init__()

        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(16)

        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(32)

        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(64)

        self.pool = nn.MaxPool2d(2, 2)

        self.fc1 = nn.Linear(64 * 16 * 16, 128)
        self.fc2 = nn.Linear(128, 2)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))

        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)

        return x


class DeepStegoAnalyzer:
    """
    Wrapper class for loading trained CNN and performing prediction.
    """

    def __init__(self, model_path="models/deep_stego_cnn.pth"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.preprocessor = ResidualPreprocessor()
        self.model = DeepStegoCNN().to(self.device)

        self.model_loaded = False
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            self.model_loaded = True

    def _prepare_input(self, image_path):
        img = Image.open(image_path).convert("RGB")
        img = img.resize((128, 128))
        img_array = np.array(img)

        residual = self.preprocessor.process(img_array)
        tensor = torch.tensor(residual).unsqueeze(0).to(self.device)

        return tensor

    def analyze(self, image_path):
        if not self.model_loaded:
            return {
                "deep_learning_score": 0.0,
                "deep_learning_confidence": 0.0,
                "method": "Deep CNN Steganalyzer (model not trained)"
            }

        try:
            x = self._prepare_input(image_path)

            with torch.no_grad():
                logits = self.model(x)
                probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

            stego_prob = float(probs[1] * 100)
            confidence = float(abs(probs[1] - probs[0]) * 100)

            return {
                "deep_learning_score": round(stego_prob, 2),
                "deep_learning_confidence": round(confidence, 2),
                "method": "Deep Residual CNN Steganalyzer"
            }

        except Exception as e:
            return {
                "error": str(e),
                "deep_learning_score": 0.0,
                "deep_learning_confidence": 0.0
            }