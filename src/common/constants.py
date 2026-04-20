"""
Constants and default configurations for StegHunter.
"""

# Supported image formats
SUPPORTED_FORMATS = frozenset({'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'})
JPEG_FORMATS = frozenset({'.jpg', '.jpeg'})

# Default method weights (must sum to 1.0)
DEFAULT_WEIGHTS = {
    "basic": 0.05,
    "lsb": 0.25,
    "chi_square": 0.10,
    "pixel_differencing": 0.05,
    "jpeg_structure": 0.10,
    "metadata": 0.05,
    "format_validation": 0.10,
    "ela": 0.20,
    "jpeg_ghost": 0.10,
    "noise": 0.10,
    "color_space": 0.10,
    "clone_detection": 0.15,
}

# Default configuration
DEFAULT_CONFIG = {
    "suspicion_threshold": 50.0,
    "weights": DEFAULT_WEIGHTS,
    "enabled_methods": [
        "basic",
        "lsb",
        "chi_square",
        "pixel_differencing",
        "ela",
        "jpeg_ghost",
        "clone_detection",
        "noise",
        "metadata",
        "jpeg_structure",
        "format_validation",
    ],
    "output": {
        "default_format": "json",
        "include_detailed": False,
        "save_ela_heatmap": False,
        "save_ghost_map": False,
    },
    "performance": {
        "max_workers": 4,
        "chunk_size": 10,
        "ela_quality": 95,
        "ela_scale": 10,
        "clone_block_size": 16,
        "noise_block_size": 32,
    },
    "video": {
        "frame_sample_rate": 10,
        "duplicate_threshold": 0.98,
        "diff_spike_multiplier": 3.0,
    },
}

# Suspicion threshold constants
THRESHOLD_LOW = 25.0
THRESHOLD_MEDIUM = 50.0
THRESHOLD_HIGH = 75.0
