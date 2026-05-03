"""
Global constants for StegHunter.
Enhanced Hybrid Detection Version
"""

# ---------------------------------------------------------
# SUPPORTED IMAGE FORMATS
# ---------------------------------------------------------

SUPPORTED_FORMATS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp"
}

JPEG_FORMATS = {
    ".jpg",
    ".jpeg"
}

VIDEO_FORMATS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".wmv",
    ".flv",
    ".webm"
}

# ---------------------------------------------------------
# DEFAULT HYBRID DETECTOR WEIGHTS
# Must approximately sum near 1.0 (normalization also exists)
# ---------------------------------------------------------

DEFAULT_WEIGHTS = {
    "basic": 0.04,
    "lsb": 0.09,
    "chi_square": 0.07,
    "pixel_differencing": 0.07,
    "jpeg_structure": 0.08,
    "metadata": 0.05,
    "format_validation": 0.05,
    "ela": 0.15,
    "jpeg_ghost": 0.08,
    "noise": 0.08,
    "color_space": 0.08,
    "clone_detection": 0.08,
    "deep_learning": 0.16
}

# ---------------------------------------------------------
# GLOBAL DECISION THRESHOLDS
# ---------------------------------------------------------

DEFAULT_SUSPICION_THRESHOLD = 50.0
HIGH_RISK_THRESHOLD = 75.0
LOW_RISK_THRESHOLD = 25.0

# ---------------------------------------------------------
# PERFORMANCE DEFAULTS
# ---------------------------------------------------------

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_ELA_QUALITY = 95
DEFAULT_ELA_SCALE = 10

# ---------------------------------------------------------
# VERSION INFO
# ---------------------------------------------------------

ENGINE_VERSION = "2.5 Hybrid Deep Forensics"