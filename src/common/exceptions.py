"""
Custom exception hierarchy for StegHunter.
"""


class SteghunterException(Exception):
    """Base exception for all StegHunter-specific errors."""
    pass


class InvalidImageError(SteghunterException):
    """Raised when image file is invalid, corrupted, or unsupported."""
    pass


class ConfigError(SteghunterException):
    """Raised when configuration is invalid or incomplete."""
    pass


class ModelError(SteghunterException):
    """Raised when ML model operations fail (loading, training, prediction)."""
    pass


class AnalysisError(SteghunterException):
    """Raised when analysis pipeline encounters an error."""
    pass
