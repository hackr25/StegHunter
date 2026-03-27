# StegHunter — Advanced Steganography Detection Tool

A powerful, multi-layered tool for detecting hidden data in images using heuristic analysis, statistical tests, frequency-domain methods, and machine learning.

## Features

- **LSB steganalysis** — entropy-based least-significant-bit analysis with chi-square uniformity test
- **Statistical tests** — pixel value differencing and histogram chi-square
- **Frequency domain** — FFT and DCT coefficient analysis
- **ML-based detection** — Random Forest classifier on a 40+ feature vector
- **Hybrid ensemble** — XGBoost + CNN + ensemble voting (experimental)
- **Heatmap visualization** — sliding-window LSB entropy overlaid on the original image
- **PDF reporting** — professional analysis reports via ReportLab
- **Batch processing** — scan entire directories, export results as JSON or CSV
- **GUI + CLI** — PyQt5 desktop interface and a full Click-based CLI

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

# Train a new model
python steg_hunter_cli.py train-model --clean-dir clean/ --stego-dir stego/ --output models/steg_model.pkl

# Run ML prediction
python steg_hunter_cli.py predict path/to/image.png
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
├── steg_hunter_cli.py          # CLI entry point
├── steg_hunter_gui.py          # GUI entry point
├── config/
│   └── steg_hunter_config.yaml # Detection thresholds and weights
├── models/                     # Pre-trained model (gitignored)
├── requirements/
│   └── requirements.txt
├── scripts/
│   ├── evaluate_model.py       # Model evaluation script
│   └── generate_training_data.py
├── src/
│   ├── common/
│   │   ├── config_manager.py
│   │   └── image_utils.py
│   ├── core/
│   │   ├── analyzer.py         # Main analysis orchestrator
│   │   ├── lsb_analyzer.py     # LSB steganalysis
│   │   ├── statistical_tests.py
│   │   ├── frequency_analysis.py
│   │   ├── heatmap_generator.py
│   │   ├── ml_classifier.py    # Random Forest classifier
│   │   ├── ml_features.py      # Feature extraction
│   │   ├── deep_learning.py    # CNN model
│   │   ├── ensemble_steganalysis.py
│   │   └── pdf_reporter.py
│   ├── forensics/
│   │   └── hash_entropy.py
│   └── gui/
│       ├── main_window.py
│       ├── batch_dialog.py
│       └── train_model_dialog.py
└── tests/
```

## Configuration

Edit `config/steg_hunter_config.yaml` to adjust detection thresholds and method weights:

```yaml
suspicion_threshold: 50.0
weights:
  basic: 0.2
  lsb: 0.5
  chi_square: 0.2
  pixel_differencing: 0.1
```

## License

MIT
