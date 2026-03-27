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

# -----------------------------
# VIDEO FRAME HASHING
# -----------------------------

def calculate_video_frame_hashes(video_path, sample_every: int = 1) -> dict:
    """
    Hash every Nth frame of a video using MD5.
    Returns dict with frame hashes, duplicate count, and duplicate frame indices.

    Args:
        video_path:    Path to video file.
        sample_every:  Hash every Nth frame (1 = all frames, 10 = every 10th).

    Returns:
        {
          'frame_hashes': list[str],
          'total_frames': int,
          'sampled_frames': int,
          'duplicate_count': int,
          'duplicate_indices': list[int],
        }
    """
    try:
        import cv2
    except ImportError:
        return {'error': 'opencv-python not installed'}

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {'error': f'Cannot open video: {video_path}'}

    frame_hashes = []
    seen: dict[str, int] = {}          # hash → first seen frame index
    duplicate_indices = []
    fnum = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if fnum % sample_every == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h = hashlib.md5(gray.tobytes()).hexdigest()
            if h in seen:
                duplicate_indices.append(fnum)
            else:
                seen[h] = fnum
            frame_hashes.append(h)
        fnum += 1

    cap.release()

    return {
        'frame_hashes': frame_hashes,
        'total_frames': fnum,
        'sampled_frames': len(frame_hashes),
        'duplicate_count': len(duplicate_indices),
        'duplicate_indices': duplicate_indices[:20],   # cap output size
    }


def calculate_per_channel_hash(image_path: str) -> dict:
    """
    Compute MD5 hash of each RGB channel independently.
    Useful for detecting channel-specific LSB embedding where only
    one channel has been modified — the other channels' hashes stay stable.
    """
    image = Image.open(image_path).convert('RGB')
    arr = np.array(image)
    return {
        'red':   hashlib.md5(arr[:, :, 0].tobytes()).hexdigest(),
        'green': hashlib.md5(arr[:, :, 1].tobytes()).hexdigest(),
        'blue':  hashlib.md5(arr[:, :, 2].tobytes()).hexdigest(),
        'full':  hashlib.md5(arr.tobytes()).hexdigest(),
    }