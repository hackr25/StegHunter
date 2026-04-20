"""
Pytest configuration and shared fixtures for StegHunter tests.
"""
import pytest
from pathlib import Path
import numpy as np
from PIL import Image
import tempfile
import os


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory."""
    test_dir = Path(__file__).parent / "fixtures"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture(scope="session")
def sample_clean_image(test_data_dir):
    """Create a clean test image (no steganography)."""
    image_path = test_data_dir / "sample_clean.png"
    if not image_path.exists():
        # Create a simple clean image with natural-looking data
        np.random.seed(42)
        img_array = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode='RGB')
        img.save(image_path)
    return image_path


@pytest.fixture(scope="session")
def sample_stego_image(test_data_dir):
    """Create a stego test image (with LSB steganography)."""
    image_path = test_data_dir / "sample_stego.png"
    if not image_path.exists():
        # Create image with message in LSB plane
        np.random.seed(42)
        img_array = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
        
        # Embed random message in LSB plane of first 1000 pixels
        message = np.random.randint(0, 2, 1000, dtype=np.uint8)
        flat = img_array.flatten()
        for i, bit in enumerate(message):
            flat[i] = (flat[i] & 0xFE) | bit  # Replace LSB with message bit
        
        img_array = flat.reshape(img_array.shape)
        img = Image.fromarray(img_array.astype(np.uint8), mode='RGB')
        img.save(image_path)
    return image_path


@pytest.fixture(scope="session")
def sample_grayscale_image(test_data_dir):
    """Create a grayscale test image."""
    image_path = test_data_dir / "sample_grayscale.png"
    if not image_path.exists():
        np.random.seed(43)
        img_array = np.random.randint(0, 256, (256, 256), dtype=np.uint8)
        img = Image.fromarray(img_array, mode='L')
        img.save(image_path)
    return image_path


@pytest.fixture(scope="session")
def sample_rgba_image(test_data_dir):
    """Create an RGBA test image."""
    image_path = test_data_dir / "sample_rgba.png"
    if not image_path.exists():
        np.random.seed(44)
        img_array = np.random.randint(0, 256, (256, 256, 4), dtype=np.uint8)
        img = Image.fromarray(img_array, mode='RGBA')
        img.save(image_path)
    return image_path


@pytest.fixture(scope="session")
def corrupted_image(test_data_dir):
    """Create a corrupted (invalid) image file."""
    image_path = test_data_dir / "corrupted.png"
    if not image_path.exists():
        # Write invalid PNG data
        with open(image_path, 'wb') as f:
            f.write(b'Not a valid PNG file' * 10)
    return image_path


@pytest.fixture(scope="session")
def blank_image(test_data_dir):
    """Create a blank (zero-value) image."""
    image_path = test_data_dir / "blank.png"
    if not image_path.exists():
        img_array = np.zeros((256, 256, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, mode='RGB')
        img.save(image_path)
    return image_path


@pytest.fixture(scope="session")
def test_config_file(test_data_dir):
    """Create a test configuration file."""
    config_path = test_data_dir / "test_config.yaml"
    if not config_path.exists():
        config_content = """suspicion_threshold: 50.0
weights:
  basic: 0.05
  lsb: 0.25
  chi_square: 0.10
  pixel_differencing: 0.05
  ela: 0.20
  jpeg_ghost: 0.10
  clone_detection: 0.15
  noise: 0.05
  color_space: 0.05
enabled_methods:
  - basic
  - lsb
  - chi_square
  - pixel_differencing
performance:
  max_workers: 2
  chunk_size: 10
"""
        with open(config_path, 'w') as f:
            f.write(config_content)
    return config_path


@pytest.fixture
def temp_output_dir():
    """Provide a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def analyzer():
    """Provide a SteganographyAnalyzer instance."""
    from src.core.analyzer import SteganographyAnalyzer
    return SteganographyAnalyzer()


@pytest.fixture
def config_manager(test_config_file):
    """Provide a ConfigManager instance with test config."""
    from src.common.config_manager import ConfigManager
    return ConfigManager(str(test_config_file))


@pytest.fixture(scope="session")
def sample_video(test_data_dir):
    """Create a minimal test video (MP4) using PIL frames."""
    video_path = test_data_dir / "sample_test_video.mp4"
    if not video_path.exists():
        try:
            import imageio
            # Create 30 frames of 128x128 video
            frames = []
            np.random.seed(42)
            for i in range(30):
                frame = np.random.randint(0, 256, (128, 128, 3), dtype=np.uint8)
                frames.append(frame)
            # Write to MP4
            with imageio.get_writer(str(video_path), fps=10) as writer:
                for frame in frames:
                    writer.append_data(frame)
        except ImportError:
            # Fallback: create a minimal MP4 file for testing
            # (won't be a valid video, but tests can still handle it)
            with open(video_path, 'wb') as f:
                f.write(b'\x00\x00\x00\x20ftypmp42' + b'\x00' * 100)
    return video_path

