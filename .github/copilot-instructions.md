# StegHunter Copilot Instructions

## Setup & Testing

**Environment Setup:**
```bash
python -m venv steg_hunter_env
# Windows: steg_hunter_env\Scripts\activate
# Unix: source steg_hunter_env/bin/activate
pip install -r requirements/requirements.txt
```

**Run Tests:**
```bash
# Full test suite (slow, ~5+ minutes)
pytest tests/ -v

# Single test file
pytest tests/test_analyzer.py -v

# Single test
pytest tests/test_analyzer.py::TestAnalyzerBasicAnalysis::test_basic_analysis_clean_image -v

# Fast tests only (excludes slow methods)
pytest tests/test_lsb_analyzer.py -v
```

**CLI Examples:**
```bash
python steg_hunter_cli.py info image.png              # Image metadata
python steg_hunter_cli.py analyze image.png           # Heuristic analysis
python steg_hunter_cli.py analyze image.png --use-ml  # ML-based detection
python steg_hunter_cli.py heatmap image.png --output heatmap.png
python steg_hunter_cli.py analyze dir/ --batch --recursive -o results.json
python steg_hunter_cli.py train-model --clean-dir clean/ --stego-dir stego/ --output models/model.pkl
```

**GUI:**
```bash
python steg_hunter_gui.py
```

## Architecture Overview

StegHunter uses a **3-phase multi-layered detection pipeline**:

### Pipeline Phases

**Phase 1: Format & Metadata Validation (all formats)**
- JPEG structure parsing (segment analysis)
- Format file integrity validation
- EXIF metadata extraction & anomaly detection
- Social media artifact detection (JPEG only)

**Phase 2: Error Level Analysis & Compression Artifacts (all formats)**
- ELA (Error Level Analysis) — JPEG recompression difference detection
- JPEG Ghost detection — double-compression artifacts (JPEG only)

**Phase 3: Content Analysis (all formats)**
- LSB (Least Significant Bit) — entropy + chi-square uniformity test
- Clone detection — copy-move forgery detection
- Noise analysis — Laplacian noise variance
- Color space analysis — HSV/LAB chrominance anomalies
- Statistical tests — pixel differencing, histogram chi-square
- Frequency analysis — FFT/DCT coefficient patterns (experimental)

**Final: Scoring & Reasoning**
- Weighted aggregation per `config/steg_hunter_config.yaml`
- Human-readable explanation via `ReasoningEngine`

### Core Architecture

**Entry Points:**
- `steg_hunter_cli.py` — Click CLI with commands: `info`, `analyze`, `heatmap`, `train-model`, `predict`
- `steg_hunter_gui.py` — PyQt5 desktop application

**Main Orchestrator:**
- `SteganographyAnalyzer` (`src/core/analyzer.py`)
  - Public: `analyze_image(path)` → full pipeline result dict
  - Public: `basic_analysis(path)` → file-level heuristics only
  - Internal: Calls enabled methods from Phase 1/2/3
  - Returns: `{filename, methods: {method_name: {suspicion_score, ...}}, final_suspicion_score, explanation}`

**Analysis Modules (`src/core/`):**
- Phase 1: Format validation, metadata, JPEG structure
- Phase 2: `ela_analyzer.py`, `jpeg_ghost_analyzer.py`
- Phase 3: `lsb_analyzer.py`, `clone_detector.py`, `noise_analyzer.py`, `color_space_analyzer.py`, `statistical_tests.py`
- ML: `ml_classifier.py` (Random Forest), `ml_features.py`, `deep_learning.py` (experimental)
- Output: `heatmap_generator.py`, `pdf_reporter.py`, `reasoning_engine.py`

**Forensics Module (`src/forensics/`):**
- `format_validator.py` — PNG/JPEG/BMP file structure checks
- `jpeg_structure.py` — JPEG segment parsing (SOI, APP0-APP15, SOS, etc.)
- `metadata_analyzer.py` — EXIF extraction + anomaly scoring
- `social_media_detector.py` — Platform fingerprint detection

**Common (`src/common/`):**
- `config_manager.py` — YAML config loading with dot-notation access
- `image_utils.py` — PIL validation, format checking via `validate_image_path()`
- `constants.py` — DEFAULT_WEIGHTS, SUPPORTED_FORMATS, JPEG_FORMATS
- `utils.py` — File collection, JSON/CSV export, `convert_numpy_types()` for serialization
- `exceptions.py` — Custom exceptions (InvalidImageError, ConfigError, AnalysisError)

**GUI (`src/gui/`):**
- `main_window.py` — Main PyQt5 window with tabs (Single/Batch/Train)
- `batch_dialog.py`, `train_model_dialog.py`, `results_panel.py`

## Key Conventions

### Analysis Method Return Format
**ALL** analysis methods (LSB, ELA, clone detection, etc.) return a dict following this pattern:
```python
{
    'suspicion_score': float (0-100),    # Required: Main metric
    'description': str,                  # Human-readable finding
    'is_suspicious': bool,               # True if score > threshold
    # Method-specific extras:
    'details': {...},                    # Additional findings
    'entropy': float,                    # For LSB, noise, color_space
    'histogram': [...],                  # For statistical methods
}
```
**Key point:** Not all methods use the same extra fields. Always check actual implementation.

### Configuration System
- **Path:** `config/steg_hunter_config.yaml`
- **Access:** `ConfigManager()` from `src/common/config_manager.py`
  ```python
  config = ConfigManager()
  max_workers = config.get('performance.max_workers', 4)  # Supports nested keys
  ```
- **Weights:** Must sum to 1.0. If not, they're **not auto-normalized**—scoring becomes inconsistent
- **Methods:** Toggle on/off via `enabled_methods` list (no code changes needed)
- **IMPORTANT:** Config is validated at load time; invalid YAML silently falls back to defaults

### Image Path Handling
- **Always use:** `validate_image_path(path_str)` from `src/common/image_utils.py`
  ```python
  from src.common.image_utils import validate_image_path
  path = validate_image_path(user_input)  # Raises InvalidImageError if bad
  image = Image.open(path)
  ```
- **Format detection:** Via `path.suffix.lower()`
- **JPEG-specific logic:** Check `ext in JPEG_FORMATS` or `path.suffix.lower() in {'.jpg', '.jpeg'}`
- **Supported:** `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`

### JSON Serialization
- **CRITICAL:** numpy types (np.int64, np.float32) aren't JSON-serializable
- **Always use:** `convert_numpy_types(result_dict)` before `json.dumps()`
  ```python
  from src.common.utils import convert_numpy_types
  result = analyzer.analyze_image(path)
  json_str = json.dumps(convert_numpy_types(result))
  ```

### JPEG-Specific Methods
- **ELA (Error Level Analysis):** Works on all formats but designed for JPEG (lossless→lossy comparison)
- **JPEG Ghost:** JPEG-only (detects double-compression artifacts)
- **JPEG Structure:** JPEG-only (parses segment headers)
- **Always check:** `ext in JPEG_FORMATS` before calling these

### Batch Processing
- Uses `ThreadPoolExecutor` with `max_workers` from config
- Each image processed independently (stateless methods)
- For slow systems: Reduce `max_workers` to avoid memory pressure
- Progress tracked via `tqdm` (can suppress with `--quiet` in CLI)

### Error Handling
- **Entry points (CLI/GUI):** Catch and report exceptions
- **Analysis methods:** Should not raise; return `{'error': str(e), 'suspicion_score': 0.0}`
- **Custom exceptions:** See `src/common/exceptions.py` (InvalidImageError, ConfigError, AnalysisError)
- **Important gap:** Methods fail silently if they error (returns 0 score, not reported to user)

### Model Loading (ML-specific)
- ML classifier and CNN load fresh on every analysis (not cached)
- **Performance issue:** Use singleton or module-level cache if optimizing
- Models expected at: `models/steg_model.pkl` (default for `--model` flag)

### Adding a New Analysis Method
1. Create `src/core/new_analyzer.py` with `def analyze_new(image: Image) -> dict`
2. Return dict with `suspicion_score`, `description`, `is_suspicious`
3. Add import + method call in `SteganographyAnalyzer.analyze_image()`
4. Add weight to `config/steg_hunter_config.yaml` under `weights:`
5. Add method name to `enabled_methods` list in YAML
6. Update `_DEFAULT_WEIGHTS` in `src/core/analyzer.py` for fallback

## Test Suite

**Location:** `tests/` with pytest fixtures in `conftest.py`

**What's tested:**
- ✅ Core analyzer pipeline and basic analysis
- ✅ LSB detection (plane extraction, entropy, chi-square uniformity)
- ✅ Statistical methods (chi-square, pixel differencing)
- ✅ Error handling (invalid paths, corrupted files, unsupported formats)
- ✅ Multiple image modes (RGB, RGBA, grayscale, blank)
- ✅ Configuration loading

**What's NOT tested (gaps):**
- ❌ Phase 2 methods (ELA, JPEG Ghost, heatmap)
- ❌ Phase 3 methods (clone detection, noise, color space analysis)
- ❌ Forensics module (format validation, JPEG structure, metadata, social media)
- ❌ ML classifier and deep learning models
- ❌ CLI commands (analyze, heatmap, train-model, predict)
- ❌ Batch processing and output formats
- ❌ PDF report generation
- ❌ Method failure isolation and logging

**Running Tests:**
```bash
# All tests
pytest tests/ -v

# Single test file
pytest tests/test_analyzer.py -v

# Single test class
pytest tests/test_analyzer.py::TestAnalyzerBasicAnalysis -v

# Single test
pytest tests/test_analyzer.py::TestAnalyzerBasicAnalysis::test_basic_analysis_clean_image -v

# With coverage (pytest-cov available)
pytest tests/ --cov=src --cov-report=term-missing
```

**Test Fixtures (conftest.py):**
- `sample_clean_image` — Random RGB image (no steganography)
- `sample_stego_image` — RGB image with LSB steganography embedded
- `sample_grayscale_image`, `sample_rgba_image` — Different modes
- `blank_image` — All-zero image (edge case)
- `corrupted_image` — Invalid PNG data (error testing)
- `analyzer` — SteganographyAnalyzer instance
- `config_manager` — ConfigManager with test config
- `temp_output_dir` — Temporary directory for outputs

**Performance Note:** Full test suite runs slowly (~5+ minutes) due to image generation and method calls. Tests for Phase 1 methods are slower; unit tests (LSB extraction) are fast.

## Known Gaps & Pitfalls

**Silent Failures:**
- When an analysis method errors, it returns `{'error': str(e), 'suspicion_score': 0.0}`
- This error is **not bubbled to the user**; the analysis continues with that method scoring 0
- The final score can be misleading if a critical method failed
- **Workaround:** Check method results for `'error'` key before trusting results

**Config Validation:**
- Weights are **not automatically normalized**; if they don't sum to 1.0, the final score is incorrect
- Invalid method names in `enabled_methods` are silently ignored
- Missing YAML file silently falls back to hardcoded defaults
- **Best practice:** Always validate config at startup

**Model Caching:**
- ML classifier and CNN models are loaded fresh on every analysis (no caching)
- **Performance issue for batch processing:** Loading model 1000x slower than analysis itself
- To optimize: Implement singleton or module-level cache in `ml_classifier.py`

**JPEG-Only Methods:**
- ELA, JPEG Ghost, and JPEG Structure checks only run on `.jpg`/`.jpeg` files
- Calling them on PNG/BMP is silently skipped (0 score)
- Metadata analyzer runs on all formats but different behavior per format

**Test Suite Gaps:**
- No tests for Phase 2/3 analysis methods, CLI commands, or batch processing
- Tests run slowly (5+ minutes full suite)
- No parallel test execution (pytest-xdist not configured)

**Dependencies:**
- TensorFlow 2.21 is heavy (~500MB download); if not needed, mark as optional
- PyQt5 is Windows/Linux specific; may need platform-specific handling
- piexif for EXIF is basic; doesn't handle all edge cases
