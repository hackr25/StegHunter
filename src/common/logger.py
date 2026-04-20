"""
Logging configuration for StegHunter.

Provides structured logging across all modules with configurable levels and formats.
"""
import logging
import sys
from pathlib import Path
from typing import Optional


# Log file location
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "steghunter.log"


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a logger instance with name.
    
    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to INFO if not set.
    
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Analysis started")
        >>> logger.error("Failed to load image", exc_info=True)
    """
    logger = logging.getLogger(name)
    
    # Don't add handlers if they already exist (avoid duplicates)
    if logger.handlers:
        return logger
    
    # Set level
    if level is None:
        level = "INFO"
    logger.setLevel(getattr(logging, level))
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Console handler (simplified output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (detailed output)
    try:
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not create file handler: {e}")
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def configure_logging(level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """Configure global logging settings.
    
    Args:
        level: Global log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Custom log file path (uses default if None)
    """
    global LOG_FILE
    if log_file:
        LOG_FILE = log_file
        LOG_DIR = log_file.parent
        LOG_DIR.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def disable_logging() -> None:
    """Disable all logging (useful for tests)."""
    logging.disable(logging.CRITICAL)


def enable_logging() -> None:
    """Re-enable logging after disable_logging()."""
    logging.disable(logging.NOTSET)
