import hashlib
import math
from collections import Counter
from PIL import Image
import numpy as np


# -----------------------------
# HASH CALCULATION
# -----------------------------

def calculate_hashes(file_path):
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)

    return md5_hash.hexdigest(), sha256_hash.hexdigest()


# -----------------------------
# ENTROPY CALCULATION
# -----------------------------

def calculate_entropy(image_path):
    image = Image.open(image_path).convert("L")  # grayscale
    pixels = np.array(image).flatten()

    pixel_counts = Counter(pixels)
    total_pixels = len(pixels)

    entropy = 0

    for count in pixel_counts.values():
        probability = count / total_pixels
        entropy -= probability * math.log2(probability)

    return round(entropy, 4)