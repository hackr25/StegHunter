# StegHunter — Advanced Steganography & Forensics Detection Suite

A professional-grade, multi-layered forensic tool for detecting hidden data in **images and videos** using a comprehensive 5-phase pipeline: file forensics, artifact detection, forgery analysis, video forensics, and machine learning classification.

## ✨ Features

### Phase 1: File Forensics
- **Format validation** — detect format mismatches and file corruption
- **Metadata analysis** — EXIF data extraction and anomaly detection
- **JPEG structure** — detect data appended after EOI marker
- **Social media detection** — identify platform-specific compression signatures

### Phase 2: Image Artifact Detection
- **LSB steganalysis** — entropy-based least-significant-bit analysis with chi-square uniformity test
- **ELA (Error Level Analysis)** — detect recompressed regions
- **JPEG Ghost** — identify double-compression artifacts
- **Noise analysis** — detect artificial high-frequency patterns
- **Color space analysis** — YCbCr distribution anomalies
- **Statistical tests** — pixel value differencing and histogram chi-square
- **Frequency domain** — FFT and DCT coefficient analysis

### Phase 3: Clone Detection (Forgery)
- **ORB-based detection** — Oriented FAST and Rotated BRIEF keypoint matching
- **Copy-move forgery** — identify duplicated/cloned regions

### Phase 4: Video Forensics ⭐ NEW
- **Frame extraction** — per-frame LSB entropy analysis via FFmpeg
- **Temporal anomaly detection** — Z-score based frame-by-frame analysis
- **Container analysis** — MP4/MKV format parsing and structural validation
- **Entropy heatmap** — visualize suspicion levels across video timeline
- **Multi-format support** — MP4, MKV, AVI, MOV, WebM, etc.

### Phase 5: Machine Learning & GUI
- **ML-based detection** — Random Forest classifier on 40+ extracted features
- **Feature extraction** — entropy, variance, histogram, FFT, color moments, etc.
- **Hybrid ensemble** — XGBoost + CNN + ensemble voting (experimental)
- **Heatmap visualization** — sliding-window LSB entropy overlaid on images/videos
- **PDF reporting** — professional analysis reports via ReportLab
- **PyQt5 GUI** — desktop interface with live analysis and results
- **Full CLI** — Click-based command-line interface with all features

### Additional Capabilities
- **Batch processing** — scan entire directories recursively, export JSON/CSV
- **Model training** — train custom ML models on labeled datasets
- **Configuration management** — YAML-based weights and thresholds
- **Error handling** — graceful degradation, timeout protection
- **Comprehensive testing** — 60+ pytest test cases

## Installation

```bash
git clone https://github.com/hackr25/StegHunter.git
cd StegHunter
python -m venv steg_hunter_env
source steg_hunter_env/bin/activate   # Windows: steg_hunter_env\Scripts\activate
pip install -r requirements/requirements.txt
```

## Usage

### CLI

#### Image Analysis
```bash
# Inspect image metadata
python steg_hunter_cli.py info path/to/image.png

# Heuristic analysis
python steg_hunter_cli.py analyze path/to/image.png

# ML-based analysis (requires trained model)
python steg_hunter_cli.py analyze path/to/image.png --use-ml

# Batch scan a directory
python steg_hunter_cli.py analyze path/to/dir --batch --recursive --output results.json

# Generate heatmap
python steg_hunter_cli.py heatmap path/to/image.png --output heatmap.png

# Full forensic scan
python steg_hunter_cli.py forensics path/to/image.png --ela --ghost --save-pdf report.pdf
```

#### Video Analysis (Phase 4)
```bash
# Basic video analysis
python steg_hunter_cli.py video-analyze path/to/video.mp4

# With entropy heatmap output
python steg_hunter_cli.py video-analyze path/to/video.mp4 --heatmap heatmap.png

# Save results to JSON
python steg_hunter_cli.py video-analyze path/to/video.mp4 --output results.json

# Verbose output with frame details
python steg_hunter_cli.py video-analyze path/to/video.mp4 --verbose
```

#### Model Training & Prediction
```bash
# Train a new model
python steg_hunter_cli.py train-model --clean-dir clean/ --stego-dir stego/ --output models/steg_model.pkl

# Run ML prediction
python steg_hunter_cli.py predict path/to/image.png

# Export analysis results
python steg_hunter_cli.py export path/to/image.png --output results.json --format json
```

### GUI

```bash
python steg_hunter_gui.py
```

Open an image → select a detection method (Heuristic / ML) → click **Analyze** → view results and heatmap.

### Evaluate model

```bash
python scripts/evaluate_model.py models/steg_model.pkl test_images/ [labels.json]
```

## Project Structure

```
StegHunter/
├── steg_hunter_cli.py              # CLI entry point
├── steg_hunter_gui.py              # GUI entry point
├── README.md                       # This file
├── config/
│   └── steg_hunter_config.yaml     # Detection thresholds and weights
├── models/                         # Pre-trained models (gitignored)
├── requirements/
│   └── requirements.txt            # Python dependencies
├── scripts/
│   ├── evaluate_model.py           # Model evaluation
│   └── generate_training_data.py   # Training data generation
├── src/
│   ├── common/
│   │   ├── config_manager.py       # Configuration management
│   │   ├── image_utils.py          # Image I/O utilities
│   │   ├── validators.py           # Config & result validation
│   │   ├── timeout_handler.py      # Timeout decorators
│   │   └── utils.py                # General utilities
│   ├── core/
│   │   ├── analyzer.py             # Main analysis orchestrator
│   │   ├── lsb_analyzer.py         # Phase 2: LSB analysis
│   │   ├── ela_analyzer.py         # Phase 2: Error Level Analysis
│   │   ├── jpeg_ghost_analyzer.py  # Phase 2: JPEG Ghost detection
│   │   ├── noise_analyzer.py       # Phase 2: Noise detection
│   │   ├── color_space_analyzer.py # Phase 2: Color space analysis
│   │   ├── statistical_tests.py    # Phase 2: Chi-square, pixel differencing
│   │   ├── frequency_analysis.py   # Phase 2: FFT/DCT analysis
│   │   ├── clone_detector.py       # Phase 3: Copy-move forgery
│   │   ├── video_analyzer.py       # Phase 4: Video frame analysis
│   │   ├── video_heatmap_generator.py # Phase 4: Video heatmap
│   │   ├── heatmap_generator.py    # Image heatmap generation
│   │   ├── ml_features.py          # Phase 5: Feature extraction
│   │   ├── ml_classifier.py        # Phase 5: Random Forest/XGBoost
│   │   ├── deep_learning.py        # Phase 5: CNN model
│   │   ├── reasoning_engine.py     # Score aggregation & explanation
│   │   ├── ensemble_steganalysis.py # Phase 5: Ensemble methods
│   │   └── pdf_reporter.py         # PDF report generation
│   ├── forensics/
│   │   ├── format_validator.py     # Phase 1: Format validation
│   │   ├── metadata_analyzer.py    # Phase 1: EXIF analysis
│   │   ├── jpeg_structure.py       # Phase 1: JPEG structure parsing
│   │   ├── social_media_detector.py # Phase 1: Social media detection
│   │   ├── video_container_analyzer.py # Phase 4: MP4/MKV parsing
│   │   └── hash_entropy.py         # Entropy utilities
│   └── gui/
│       ├── main_window.py          # PyQt5 main window
│       ├── batch_dialog.py         # Batch processing dialog
│       └── train_model_dialog.py   # Model training dialog
└── tests/
    ├── conftest.py                 # Pytest fixtures & configuration
    ├── test_analyzer.py
    ├── test_cli.py                 # CLI command tests
    ├── test_validators.py          # Config validation tests
    ├── test_lsb_analyzer.py        # Phase 2 tests
    ├── test_ela_analyzer.py        # Phase 2 tests
    ├── test_jpeg_ghost_analyzer.py # Phase 2 tests
    ├── test_noise_analyzer.py      # Phase 2 tests
    ├── test_color_space_analyzer.py # Phase 2 tests
    ├── test_statistical_tests.py   # Phase 2 tests
    ├── test_clone_detector.py      # Phase 3 tests
    ├── test_ml_classifier.py       # Phase 5 tests
    ├── test_video_analyzer.py      # Phase 4 tests
    └── fixtures/                   # Test images
```

## Configuration

Edit `config/steg_hunter_config.yaml` to adjust detection thresholds and method weights:

```yaml
suspicion_threshold: 50.0
weights:
  # Phase 1: File Forensics
  format_validation: 0.05
  jpeg_structure: 0.05
  metadata: 0.05
  social_media: 0.05
  
  # Phase 2: Image Artifacts
  lsb: 0.20
  ela: 0.15
  jpeg_ghost: 0.10
  noise: 0.10
  color_space: 0.10
  chi_square: 0.10
  pixel_differencing: 0.05
  
  # Phase 3: Forgery Detection
  clone_detection: 0.05

enabled_methods:
  - format_validation
  - jpeg_structure
  - metadata
  - lsb
  - ela
  - noise
  - color_space

performance:
  max_workers: 4
  timeout_seconds: 30
  chunk_size: 100
```

## Architecture: 5-Phase Pipeline

StegHunter uses a **professional forensic layered defense strategy**:

```
Input (Image or Video)
    ↓
┌─────────────────────────────────────────────────────┐
│ Phase 1: Forensic Foundation                        │
│ • Format validation (magic bytes)                   │
│ • Metadata/EXIF analysis                            │
│ • JPEG structure parsing (appended data)            │
│ • Social media platform detection                   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Phase 2: Image Artifact Detection                   │
│ • LSB entropy + chi-square uniformity               │
│ • ELA (Error Level Analysis)                        │
│ • JPEG Ghost (double compression)                   │
│ • Noise analysis (high-frequency patterns)          │
│ • Color space distribution (YCbCr channels)         │
│ • FFT/DCT frequency analysis                        │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Phase 3: Forgery Detection                          │
│ • ORB keypoint matching                             │
│ • Copy-move forgery detection                       │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Phase 4: Video Forensics (NEW)                      │
│ • Frame extraction & LSB analysis                   │
│ • Temporal anomaly detection (Z-score)              │
│ • Container format analysis (MP4/MKV)               │
│ • Entropy heatmap visualization                     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Phase 5: ML Classification & Reporting              │
│ • 40+ feature extraction                            │
│ • Random Forest prediction                          │
│ • XGBoost ensemble (optional)                       │
│ • Reasoning engine (explainability)                 │
│ • PDF/JSON/CSV reporting                           │
└─────────────────────────────────────────────────────┘
    ↓
Output (0-100 suspicion score + detailed report)
```

## Testing

A comprehensive test suite with **60+ parametrized test cases** covers all 5 phases:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_video_analyzer.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test class
python -m pytest tests/test_validators.py::TestConfigValidator -v
```

**Test Coverage:**
- Phase 1: File forensics validation
- Phase 2: ELA, JPEG Ghost, Noise, Color Space analysis
- Phase 3: Clone detection (forgery)
- Phase 4: Video frame analysis, container parsing, heatmap generation
- Phase 5: ML feature extraction, classifier predictions
- CLI: All commands (analyze, heatmap, video-analyze, train-model, etc.)
- Error Handling: Config validation, timeout protection, graceful degradation

## Dependencies

Core requirements are in `requirements/requirements.txt`:

```
numpy>=1.24.0
scipy>=1.10.0
Pillow>=9.0.0
scikit-learn>=1.3.0
opencv-python>=4.8.0
PyYAML>=6.0
piexif>=1.1.3
watchdog>=6.0.0
imageio[ffmpeg]>=2.37.0
pytest>=7.0.0
pytest-cov>=4.0.0
```

**For video analysis (Phase 4):**
- FFmpeg must be installed on your system
  - Ubuntu/Debian: `apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: [Download FFmpeg](https://ffmpeg.org/download.html) or `choco install ffmpeg`

## Performance

- **Single image analysis**: ~1-2 seconds (heuristic) or 5-10 seconds (with ML)
- **Video analysis** (30 frames): ~10-30 seconds depending on resolution
- **Batch processing**: Parallelized across `max_workers` (default 4)
- **Heatmap generation**: ~0.5-1 second per image/video

Frame sampling for videos can be adjusted to speed up analysis for large videos.

## License

MIT
