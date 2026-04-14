"""
Main Application Window for SteHunter GUI
"""
import warnings
import numpy as np

# Suppress NumPy warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', message='invalid value encountered in divide')
np.seterr(divide='ignore', invalid='ignore')

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QTabWidget,
                             QStatusBar, QMenuBar, QAction, QToolBar, QComboBox,
                             QProgressBar, QSplitter, QTextEdit, QCheckBox,
                             QSlider, QGroupBox, QSpinBox, QDoubleSpinBox, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont
import sys
from pathlib import Path
from .batch_dialog import BatchProcessingDialog
from src.core.pdf_reporter import PDFReporter
from src.forensics.hash_entropy import calculate_hashes,calculate_entropy
from .train_model_dialog import TrainModelDialog
from .results_panel import ResultsPanel


class SteganographyAnalyzerWorker(QThread):
    """Worker thread for running analysis in background"""
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, image_path, analyzer, use_ml=False, model_path=None):
        super().__init__()
        self.image_path = image_path
        self.analyzer = analyzer
        self.use_ml = use_ml
        self.model_path = model_path
    
    def run(self):
        try:
            if self.use_ml:
                from src.core.ml_classifier import MLSteganalysisClassifier
                classifier = MLSteganalysisClassifier(self.model_path)
                result = classifier.predict(self.image_path)
                
                prob_score = result['probability'] * 100 
                
                self.finished_signal.emit({
                    'filename': Path(self.image_path).name,
                    'method': 'ML-based',
                    'prediction': result['prediction'],
                    'probability': result['probability'],
                    'confidence': result['confidence'],
                    'final_suspicion_score': prob_score, # ADD THIS
                    'explanation': { # ADD THIS
                        'verdict': "Highly Suspicious" if result['prediction'] == 1 else "Clean",
                        'detailed_findings': [f"ML Model predicts steganography with {prob_score:.2f}% probability."],
                        'summary': f"ML Analysis complete. Verdict: {'Stego' if result['prediction'] == 1 else 'Clean'}"
                    }
                })
            else:
                results = self.analyzer.analyze_image(self.image_path)
                self.finished_signal.emit(results)
                
        except Exception as e:
            self.error_signal.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_image_path = None
        self.current_image = None
        self.analysis_results = None
        
        # Core components
        from src.core.analyzer import SteganographyAnalyzer
        self.analyzer = SteganographyAnalyzer()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("StegHunter - Advanced Steganography Detection Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout()
        central_widget.setLayout(self.main_layout)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main splitter for image viewer and results
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Left panel - Image viewer
        self.create_image_viewer()
        self.main_splitter.addWidget(self.image_viewer_group)
        
        # Right panel - Analysis results
        self.create_results_panel()
        self.main_splitter.addWidget(self.results_group)
        
        # Set splitter proportions
        self.main_splitter.setSizes([600, 600])
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.setVisible(False)
        
        # Styling
        self.apply_styles()
        
        self.results_panel = ResultsPanel()
        self.main_layout.addWidget(self.results_panel)
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        open_action = QAction('&Open Image', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open an image for analysis')
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('&Export Results', self)
        export_action.setShortcut('Ctrl+E')
        export_action.setStatusTip('Export analysis results')
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Analyze menu
        analyze_menu = menubar.addMenu('&Analyze')
        
        analyze_action = QAction('&Analyze Image', self)
        analyze_action.setShortcut('Ctrl+A')
        analyze_action.setStatusTip('Analyze current image')
        analyze_action.triggered.connect(self.analyze_image)
        analyze_menu.addAction(analyze_action)
        
        batch_action = QAction('&Batch Process', self)
        batch_action.setShortcut('Ctrl+B')
        batch_action.setStatusTip('Process multiple images')
        batch_action.triggered.connect(self.batch_process)
        analyze_menu.addAction(batch_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        heatmap_action = QAction('Generate &Heatmap', self)
        heatmap_action.setStatusTip('Generate visual heatmap')
        heatmap_action.triggered.connect(self.generate_heatmap)
        tools_menu.addAction(heatmap_action)
        
        train_model_action = QAction('Train &Model', self)
        train_model_action.setStatusTip('Train ML detection model')
        train_model_action.triggered.connect(self.train_model)
        tools_menu.addAction(train_model_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.setStatusTip('About StegHunter')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        
        pdf_action = QAction('Export &PDF Report', self)
        pdf_action.setShortcut('Ctrl+P')
        pdf_action.setStatusTip('Export analysis results as PDF')
        pdf_action.triggered.connect(self.export_pdf_report)
        file_menu.insertAction(export_action, pdf_action)

    
    def create_toolbar(self):
        """Create application toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Open button
        open_btn = QPushButton('📁 Open')
        open_btn.setStatusTip('Open Image (Ctrl+O)')
        open_btn.clicked.connect(self.open_image)
        toolbar.addWidget(open_btn)
        
        toolbar.addSeparator()
        
        # Analyze button
        analyze_btn = QPushButton('🔍 Analyze')
        analyze_btn.setStatusTip('Analyze Image (Ctrl+A)')
        analyze_btn.clicked.connect(self.analyze_image)
        toolbar.addWidget(analyze_btn)
        
        # Heatmap button
        heatmap_btn = QPushButton('🔥 Heatmap')
        heatmap_btn.setStatusTip('Generate Heatmap')
        heatmap_btn.clicked.connect(self.generate_heatmap)
        toolbar.addWidget(heatmap_btn)
        
        toolbar.addSeparator()
        
        # Method selection
        toolbar.addWidget(QLabel('Method:'))
        self.method_combo = QComboBox()
        self.method_combo.addItems(['Heuristic', 'ML'])
        self.method_combo.setStatusTip('Select detection method')
        toolbar.addWidget(self.method_combo)
        
        toolbar.addSeparator()
        
        # Threshold slider
        toolbar.addWidget(QLabel('Threshold:'))
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(50)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        self.threshold_slider.setMaximumWidth(200)
        self.threshold_slider.setStatusTip('Suspicion threshold')
        toolbar.addWidget(self.threshold_slider)
        
        self.threshold_label = QLabel('50')
        self.threshold_label.setMinimumWidth(30)
        toolbar.addWidget(self.threshold_label)
        
        self.threshold_slider.valueChanged.connect(lambda val: self.threshold_label.setText(str(val)))
        
        toolbar.addSeparator()
        
        # Export button
        export_btn = QPushButton('💾 Export')
        export_btn.setStatusTip('Export Results (Ctrl+E)')
        export_btn.clicked.connect(self.export_results)
        toolbar.addWidget(export_btn)
    
    def create_image_viewer(self):
        """Create image viewer panel"""
        self.image_viewer_group = QGroupBox("Image Viewer")
        layout = QVBoxLayout()
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("QLabel { background-color: #f0f0f0; border: 2px dashed #ccc; }")
        self.image_label.setText("Drop image here or use File > Open")
        layout.addWidget(self.image_label)
        
        # Image info
        self.image_info_label = QLabel("No image loaded")
        self.image_info_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        layout.addWidget(self.image_info_label)

        self.hash_md5_label = QLabel("MD5: N/A")
        self.hash_sha256_label = QLabel("SHA256: N/A")
        self.entropy_label = QLabel("Entropy: N/A")

        self.hash_md5_label.setStyleSheet("QLabel { font-family: Consolas; font-size: 11px; }")
        self.hash_sha256_label.setStyleSheet("QLabel { font-family: Consolas; font-size: 11px; }")
        self.entropy_label.setStyleSheet("QLabel { font-weight: bold; font-size: 12px; }")

        layout.addWidget(self.hash_md5_label)
        layout.addWidget(self.hash_sha256_label)
        layout.addWidget(self.entropy_label)
                
        self.image_viewer_group.setLayout(layout)
    
    def create_results_panel(self):
        """Create analysis results panel"""
        self.results_group = QGroupBox("Analysis Results")
        layout = QVBoxLayout()
        
        # Tabs for different result types
        self.results_tab = QTabWidget()
        
        # Summary tab
        self.create_summary_tab()
        self.results_tab.addTab(self.summary_tab, "Summary")
        
        # Details tab
        self.create_details_tab()
        self.results_tab.addTab(self.details_tab, "Details")
        
        # Heatmap tab
        self.create_heatmap_tab()
        self.results_tab.addTab(self.heatmap_tab, "Heatmap")
        
        # Methods tab
        self.create_methods_tab()
        self.results_tab.addTab(self.methods_tab, "Methods")
        
        layout.addWidget(self.results_tab)

        # ELA tab
        self.create_ela_tab()
        self.results_tab.addTab(self.ela_tab, "ELA")

        # File Info tab
        self.create_file_info_tab()
        self.results_tab.addTab(self.file_info_tab, "File Info")

        # Metadata tab
        self.create_metadata_tab()
        self.results_tab.addTab(self.metadata_tab, "Metadata")
        
        self.create_noise_tab()
        self.results_tab.addTab(self.noise_tab, "Noise")

        self.create_color_tab()
        self.results_tab.addTab(self.color_tab, "Color Space")

        self.create_ghost_tab()
        self.results_tab.addTab(self.ghost_tab, "JPEG Ghost")
        
        self.create_clone_tab()
        self.results_tab.addTab(self.clone_tab, "Clone Detection")

        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        reanalyze_btn = QPushButton('🔄 Re-analyze')
        reanalyze_btn.clicked.connect(self.analyze_image)
        actions_layout.addWidget(reanalyze_btn)
        
        export_btn = QPushButton('💾 Export')
        export_btn.clicked.connect(self.export_results)
        actions_layout.addWidget(export_btn)
        
        layout.addLayout(actions_layout)
        
        self.results_group.setLayout(layout)
    

    
    def create_summary_tab(self):
        """Create summary results tab"""
        self.summary_tab = QWidget()
        layout = QVBoxLayout()
        
        # Main result display
        self.result_label = QLabel("No analysis performed")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; padding: 20px; }")
        layout.addWidget(self.result_label)
        
        # Suspicion score
        self.score_label = QLabel("Suspicion Score: N/A")
        self.score_label.setStyleSheet("QLabel { font-size: 24px; font-weight: bold; }")
        self.score_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.score_label)
        
        # Status indicator
        self.status_indicator = QLabel("Status: Unknown")
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.status_indicator.setStyleSheet("QLabel { font-size: 16px; padding: 10px; }")
        layout.addWidget(self.status_indicator)
        
        # Progress bar for analysis
        self.analysis_progress = QProgressBar()
        self.analysis_progress.setVisible(False)
        layout.addWidget(self.analysis_progress)
        
        self.summary_tab.setLayout(layout)
    
    def create_details_tab(self):
        """Create detailed results tab"""
        self.details_tab = QWidget()
        layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet("QTextEdit { font-family: Consolas, monospace; font-size: 10px; }")
        layout.addWidget(self.details_text)
        
        self.details_tab.setLayout(layout)
    
    def create_heatmap_tab(self):
        """Create heatmap visualization tab"""
        self.heatmap_tab = QWidget()
        layout = QVBoxLayout()
        
        self.heatmap_label = QLabel()
        self.heatmap_label.setAlignment(Qt.AlignCenter)
        self.heatmap_label.setMinimumSize(400, 300)
        self.heatmap_label.setStyleSheet("QLabel { background-color: #f0f0f0; border: 2px dashed #ccc; }")
        self.heatmap_label.setText("No heatmap generated")
        layout.addWidget(self.heatmap_label)
        
        # Heatmap controls
        heatmap_layout = QHBoxLayout()
        heatmap_layout.addWidget(QLabel("Method:"))
        
        self.heatmap_method_combo = QComboBox()
        self.heatmap_method_combo.addItems(['LSB', 'Comprehensive', 'ML'])
        heatmap_layout.addWidget(self.heatmap_method_combo)
        
        generate_heatmap_btn = QPushButton('Generate Heatmap')
        generate_heatmap_btn.clicked.connect(self.generate_heatmap)
        heatmap_layout.addWidget(generate_heatmap_btn)
        
        layout.addLayout(heatmap_layout)
        self.heatmap_tab.setLayout(layout)
    
    def create_methods_tab(self):
        """Create detailed methods results tab"""
        self.methods_tab = QWidget()
        layout = QVBoxLayout()
        
        self.methods_text = QTextEdit()
        self.methods_text.setReadOnly(True)
        self.methods_text.setStyleSheet("QTextEdit { font-family: Consolas, monospace; font-size: 10px; }")
        layout.addWidget(self.methods_text)
        
        self.methods_tab.setLayout(layout)

    def create_ela_tab(self):
        """ELA (Error Level Analysis) tab"""
        self.ela_tab = QWidget()
        layout = QVBoxLayout()

        # Image display
        self.ela_label = QLabel("Run ELA to see results")
        self.ela_label.setAlignment(Qt.AlignCenter)
        self.ela_label.setMinimumSize(400, 300)
        self.ela_label.setStyleSheet(
            "QLabel { background-color: #1a1a2e; color: #aaa; border: 2px dashed #444; }"
        )
        layout.addWidget(self.ela_label)

        # Score display
        self.ela_score_label = QLabel("ELA Score: —")
        self.ela_score_label.setAlignment(Qt.AlignCenter)
        self.ela_score_label.setStyleSheet("QLabel { font-size: 13px; font-weight: bold; }")
        layout.addWidget(self.ela_score_label)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Quality:"))
        self.ela_quality_slider = QSlider(Qt.Horizontal)
        self.ela_quality_slider.setRange(70, 98)
        self.ela_quality_slider.setValue(95)
        self.ela_quality_slider.setTickInterval(5)
        ctrl.addWidget(self.ela_quality_slider)
        self.ela_quality_val = QLabel("95")
        self.ela_quality_slider.valueChanged.connect(
            lambda v: self.ela_quality_val.setText(str(v))
        )
        ctrl.addWidget(self.ela_quality_val)

        run_ela_btn = QPushButton("▶ Run ELA")
        run_ela_btn.clicked.connect(self.run_ela_analysis)
        ctrl.addWidget(run_ela_btn)
        layout.addLayout(ctrl)

        self.ela_tab.setLayout(layout)
        
    def create_noise_tab(self):
        self.noise_tab = QWidget()
        layout = QVBoxLayout()
        self.noise_text = QTextEdit()
        self.noise_text.setReadOnly(True)
        self.noise_text.setStyleSheet("font-family: Consolas; background: #f9f9f9;")
        layout.addWidget(QLabel("Noise Analysis Statistics:"))
        layout.addWidget(self.noise_text)
        self.noise_tab.setLayout(layout)

    def create_color_tab(self):
        self.color_tab = QWidget()
        layout = QVBoxLayout()
        self.color_text = QTextEdit()
        self.color_text.setReadOnly(True)
        self.color_text.setStyleSheet("font-family: Consolas; background: #f9f9f9;")
        layout.addWidget(QLabel("Color Space (YCbCr) Analysis:"))
        layout.addWidget(self.color_text)
        self.color_tab.setLayout(layout)

    def create_ghost_tab(self):
        self.ghost_tab = QWidget()
        layout = QVBoxLayout()
        self.ghost_text = QTextEdit()
        self.ghost_text.setReadOnly(True)
        self.ghost_text.setStyleSheet("font-family: Consolas; background: #f9f9f9;")
        layout.addWidget(QLabel("JPEG Ghost Analysis:"))
        layout.addWidget(self.ghost_text)
        self.ghost_tab.setLayout(layout)


    def run_ela_analysis(self):
        """Run ELA on current image and display result."""
        if not self.current_image_path:
            self.show_error("Load an image first.")
            return
        try:
            from src.core.heatmap_generator import HeatmapGenerator
            quality = self.ela_quality_slider.value()
            gen = HeatmapGenerator()
            ela_bgr = gen.generate_ela_heatmap(self.current_image_path, quality=quality)
            scores  = gen.ela_score(self.current_image_path, quality=quality)

            # Convert BGR → QPixmap
            import cv2
            from PyQt5.QtGui import QImage
            ela_rgb = cv2.cvtColor(ela_bgr, cv2.COLOR_BGR2RGB)
            h, w, ch = ela_rgb.shape
            qimg = QImage(ela_rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            self.ela_label.setPixmap(
                pix.scaled(self.ela_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            sc = scores['suspicion_score']
            color = "#e74c3c" if sc >= 50 else "#27ae60"
            self.ela_score_label.setText(
                f"ELA Score: {sc:.1f}/100 | Mean: {scores['ela_mean']:.2f} | "
                f"Std: {scores['ela_std']:.2f}"
            )
            self.ela_score_label.setStyleSheet(
                f"QLabel {{ font-size: 13px; font-weight: bold; color: {color}; }}"
            )
            self.status_bar.showMessage(f"ELA complete — suspicion score: {sc:.1f}")
        except Exception as e:
            self.show_error(f"ELA failed: {e}")

    def create_file_info_tab(self):
        """File structure / hex strings / format validation tab"""
        self.file_info_tab = QWidget()
        layout = QVBoxLayout()

        self.file_info_text = QTextEdit()
        self.file_info_text.setReadOnly(True)
        self.file_info_text.setStyleSheet(
            "QTextEdit { font-family: Consolas, 'Courier New', monospace; font-size: 10px; "
            "background: #0d1117; color: #c9d1d9; }"
        )
        layout.addWidget(self.file_info_text)

        scan_btn = QPushButton("🔍 Scan File Structure")
        scan_btn.clicked.connect(self.scan_file_structure)
        layout.addWidget(scan_btn)

        self.file_info_tab.setLayout(layout)

    def scan_file_structure(self):
        """Scan JPEG structure and format validation for current file."""
        if not self.current_image_path:
            self.show_error("Load an image first.")
            return
        try:
            from pathlib import Path
            path = Path(self.current_image_path)
            lines = []

            # Magic bytes check
            with open(path, 'rb') as f:
                header = f.read(8)
            magic_map = {
                b'\xff\xd8\xff': 'JPEG',
                b'\x89PNG':      'PNG',
                b'BM':           'BMP',
                b'GIF8':         'GIF',
            }
            detected_fmt = next(
                (fmt for sig, fmt in magic_map.items() if header[:len(sig)] == sig),
                'Unknown'
            )
            ext = path.suffix.upper().lstrip('.')
            match = "✅ Match" if detected_fmt.upper().startswith(ext[:3]) else "⚠️  MISMATCH"
            lines.append(f"=== FORMAT VALIDATION ===")
            lines.append(f"Extension : {path.suffix}")
            lines.append(f"Detected  : {detected_fmt}")
            lines.append(f"Status    : {match}")
            lines.append("")

            # JPEG structure
            if path.suffix.lower() in ('.jpg', '.jpeg'):
                lines.append("=== JPEG MARKER STRUCTURE ===")
                with open(path, 'rb') as f:
                    data = f.read()
                MARKERS = {
                    0xFFD8: 'SOI',    0xFFD9: 'EOI',
                    0xFFE0: 'APP0',   0xFFE1: 'APP1(EXIF)',
                    0xFFDB: 'DQT',    0xFFC0: 'SOF0',
                    0xFFC4: 'DHT',    0xFFDA: 'SOS',
                    0xFFDD: 'DRI',    0xFFE2: 'APP2',
                }
                i = 0
                eoi_offset = None
                while i < len(data) - 1:
                    if data[i] == 0xFF and data[i+1] not in (0x00, 0xFF):
                        code = (data[i] << 8) | data[i+1]
                        name = MARKERS.get(code, f'0x{code:04X}')
                        if code == 0xFFD9:
                            eoi_offset = i
                        size = 0
                        if code not in (0xFFD8, 0xFFD9):
                            try:
                                import struct
                                size = struct.unpack('>H', data[i+2:i+4])[0]
                            except Exception:
                                pass
                        lines.append(f"  Offset 0x{i:06X}  {name:<16} size={size}")
                        i += max(2, size + 2) if size else 2
                    else:
                        i += 1
                if eoi_offset is not None:
                    appended = len(data) - (eoi_offset + 2)
                    if appended > 0:
                        lines.append("")
                        lines.append(f"⚠️  APPENDED DATA AFTER EOI: {appended} bytes")
                        lines.append("    This is a common steganography technique!")
                    else:
                        lines.append("")
                        lines.append("✅ No data appended after EOI marker")
                lines.append("")

            # Known stego tool signatures
            lines.append("=== STEGO TOOL SIGNATURES ===")
            with open(path, 'rb') as f:
                data = f.read()
            sigs = {
                b'OpenStego': 'OpenStego',
                b'SilentEye': 'SilentEye',
                b'Steghide':  'Steghide',
                b'outguess':  'OutGuess',
                b'F5Stego':   'F5',
                b'stegdetect':'StegDetect marker',
            }
            found_any = False
            for sig, name in sigs.items():
                if sig in data:
                    lines.append(f"  ⚠️  Found: {name}")
                    found_any = True
            if not found_any:
                lines.append("  ✅ No known stego tool signatures found")

            self.file_info_text.setPlainText("\n".join(lines))
            self.status_bar.showMessage("File structure scan complete")
        except Exception as e:
            self.show_error(f"File scan failed: {e}")

    def create_metadata_tab(self):
        """EXIF metadata viewer tab"""
        self.metadata_tab = QWidget()
        layout = QVBoxLayout()

        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setStyleSheet(
            "QTextEdit { font-family: Consolas, 'Courier New', monospace; font-size: 10px; "
            "background: #0d1117; color: #c9d1d9; }"
        )
        layout.addWidget(self.metadata_text)

        read_meta_btn = QPushButton("📋 Read Metadata & EXIF")
        read_meta_btn.clicked.connect(self.read_metadata)
        layout.addWidget(read_meta_btn)

        self.metadata_tab.setLayout(layout)

    def read_metadata(self):
        """Extract and display EXIF/metadata for current image."""
        if not self.current_image_path:
            self.show_error("Load an image first.")
            return
        try:
            from PIL import Image as PILImage
            from PIL.ExifTags import TAGS, GPSTAGS
            from pathlib import Path
            import os

            path = Path(self.current_image_path)
            lines = []

            # File-level metadata
            stat = path.stat()
            lines.append("=== FILE METADATA ===")
            lines.append(f"File Name      : {path.name}")
            lines.append(f"File Size      : {stat.st_size:,} bytes")
            lines.append(f"Extension      : {path.suffix}")
            from datetime import datetime
            lines.append(f"Modified       : {datetime.fromtimestamp(stat.st_mtime)}")
            lines.append(f"Created        : {datetime.fromtimestamp(stat.st_ctime)}")
            lines.append("")

            # EXIF data
            img = PILImage.open(self.current_image_path)
            exif_data = img._getexif() if hasattr(img, '_getexif') else None

            if exif_data:
                lines.append("=== EXIF DATA ===")
                anomalies = []
                has_gps = False
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, f"Tag_{tag_id}")
                    if tag == 'GPSInfo':
                        has_gps = True
                        lines.append(f"  {tag:<30}: [GPS coordinates present]")
                        anomalies.append("GPS data embedded in image")
                    elif tag in ('Software', 'ProcessingSoftware'):
                        lines.append(f"  {tag:<30}: {str(value)[:60]}")
                        edit_keywords = ['photoshop', 'gimp', 'lightroom',
                                         'affinity', 'paint', 'preview']
                        if any(kw in str(value).lower() for kw in edit_keywords):
                            anomalies.append(f"Editing software detected: {value}")
                    elif tag in ('DateTime', 'DateTimeOriginal', 'DateTimeDigitized'):
                        lines.append(f"  {tag:<30}: {str(value)[:60]}")
                    elif tag == 'Make':
                        lines.append(f"  {tag:<30}: {str(value)[:60]}")
                    elif tag == 'Model':
                        lines.append(f"  {tag:<30}: {str(value)[:60]}")
                    else:
                        val_str = str(value)
                        if len(val_str) < 80:
                            lines.append(f"  {tag:<30}: {val_str}")

                lines.append("")
                lines.append("=== ANOMALY DETECTION ===")
                if anomalies:
                    for a in anomalies:
                        lines.append(f"  ⚠️  {a}")
                else:
                    lines.append("  ✅ No metadata anomalies detected")
            else:
                lines.append("=== EXIF DATA ===")
                lines.append("  No EXIF data found in this image.")
                lines.append("  (Images processed by some tools strip EXIF)")

            # Thumbnail check
            lines.append("")
            lines.append("=== THUMBNAIL ===")
            try:
                from PIL.ExifTags import TAGS
                if hasattr(img, 'applist'):
                    lines.append("  Embedded thumbnail: checking...")
                else:
                    # Try extracting via piexif if available
                    try:
                        import piexif
                        exif_bytes = img.info.get('exif', b'')
                        if exif_bytes:
                            exif_dict = piexif.load(exif_bytes)
                            thumb = exif_dict.get('thumbnail')
                            if thumb:
                                lines.append(f"  Embedded thumbnail: {len(thumb)} bytes")
                                lines.append("  (Thumbnail mismatch check requires piexif)")
                            else:
                                lines.append("  No embedded thumbnail found")
                        else:
                            lines.append("  No EXIF bytes — no thumbnail")
                    except ImportError:
                        lines.append("  Install piexif for thumbnail analysis")
            except Exception:
                lines.append("  Thumbnail check skipped")

            self.metadata_text.setPlainText("\n".join(lines))
            self.status_bar.showMessage("Metadata extraction complete")
        except Exception as e:
            self.show_error(f"Metadata read failed: {e}")
    
    def apply_styles(self):
        """Apply modern styling to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #0078d7;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
            }
            QStatusBar {
                background-color: #333;
                color: white;
            }
        """)
    
    def open_image(self):
        """Open image file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Open Image',
            '',
            'Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;All Files (*)'
        )
        
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, image_path):
        """Load and display image"""
        try:
            # Load image with PIL
            from PIL import Image
            self.current_image = Image.open(image_path)
            self.current_image_path = image_path
        
            try:
                md5, sha256 = calculate_hashes(image_path)
                entropy = calculate_entropy(image_path)

                self.hash_md5_label.setText(f"MD5: {md5}")
                self.hash_sha256_label.setText(f"SHA256: {sha256}")
                self.entropy_label.setText(f"Entropy: {entropy}")

                # Entropy warning for possible stego
                if entropy > 7.5:
                    self.entropy_label.setText(f"Entropy: {entropy}  ⚠ High Randomness")
                    self.entropy_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

            except Exception as e:
                print(f"Forensic calculation error: {e}")
            
            # Display in Qt
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
            
            # Update info
            self.image_info_label.setText(f"Image: {Path(image_path).name} | Size: {self.current_image.size[0]}x{self.current_image.size[1]} | Format: {self.current_image.format}")
            
            # Update status
            self.status_bar.showMessage(f"Loaded: {image_path}")
            
            # Clear previous results
            self.clear_results()
            
        except Exception as e:
            self.status_bar.showMessage(f"Error loading image: {e}")
            self.show_error(f"Error loading image: {e}")
    
    def analyze_image(self):
        """Analyze the loaded image"""
        if not self.current_image_path:
            self.show_error("No image loaded")
            return
        
        self.status_bar.showMessage("Analyzing image...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Disable UI during analysis
        self.setEnabled(False)
        
        # Create and start worker thread
        use_ml = self.method_combo.currentText() == 'ML'
        self.analyzer_worker = SteganographyAnalyzerWorker(
            self.current_image_path,
            self.analyzer,
            use_ml=use_ml,
            model_path='models/steg_model.pkl'
        )
        
        # Connect signals
        self.analyzer_worker.progress_signal.connect(self.update_progress)
        self.analyzer_worker.finished_signal.connect(self.analysis_finished)
        self.analyzer_worker.error_signal.connect(self.analysis_error)
        
        # Start analysis
        self.analyzer_worker.start()
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def analysis_finished(self, results):
        """Handle analysis completion"""
        self.analysis_results = results
        self.progress_bar.setVisible(False)
        self.setEnabled(True)
        
        # Update summary tab
        self.update_summary_results(results)
        
        # Update details tab
        self.update_details_results(results)
        
        # Update methods tab
        self.update_methods_results(results)
        
        self.status_bar.showMessage("Analysis complete")
        
        self.update_ela_tab(results)
        self.update_noise_tab(results)
        self.update_color_tab(results)
        self.update_ghost_tab(results)
        self.update_clone_tab(results)
        
        # Switch to summary tab
        self.results_tab.setCurrentIndex(0)
        self.results_panel.update_results(results)
        self.status_bar.showMessage("Analysis complete")
        self.results_tab.setCurrentIndex(0)
    
    def analysis_error(self, error_msg):
        """Handle analysis error"""
        self.progress_bar.setVisible(False)
        self.setEnabled(True)
        self.status_bar.showMessage(f"Analysis error: {error_msg}")
        self.show_error(f"Analysis error: {error_msg}")
    
    def update_summary_results(self, results):
        """Update summary results display"""
        # Handle different result structures (ML vs Heuristic)
        if 'ml_prediction' in results:
            # ML results structure
            prediction = results['ml_prediction']
            score = results['ml_probability'] * 100
            status = "HIGH SUSPICION" if prediction == 1 else "CLEAN"
            status_color = "#ff0000" if prediction == 1 else "#00ff00"
            
            self.result_label.setText(f"ML PREDICTION\n{status}")
            self.result_label.setStyleSheet(f"QLabel {{ font-size: 18px; font-weight: bold; padding: 20px; color: {status_color}; }}")
            
            self.score_label.setText(f"Suspicion Score: {score:.2f}%")
            
            threshold = self.threshold_slider.value()
            self.status_indicator.setText(f"Status: {status} (Threshold: {threshold})")
            self.status_indicator.setStyleSheet(f"QLabel {{ font-size: 16px; padding: 10px; color: {status_color}; font-weight: bold; }}")
        else:
            # Heuristic results structure
            score = results.get('final_suspicion_score', 0)
            threshold = self.threshold_slider.value()
            status = "HIGH SUSPICION" if score >= threshold else "CLEAN"
            status_color = "#ff0000" if score >= threshold else "#00ff00"
            
            self.result_label.setText(f"DETECTED\n{status}")
            self.result_label.setStyleSheet(f"QLabel {{ font-size: 18px; font-weight: bold; padding: 20px; color: {status_color}; }}")
            
            self.score_label.setText(f"Suspicion Score: {score:.2f}/100")
            
            self.status_indicator.setText(f"Status: {status} (Threshold: {threshold})")
            self.status_indicator.setStyleSheet(f"QLabel {{ font-size: 16px; padding: 10px; color: {status_color}; font-weight: bold; }}")
    
    def update_noise_tab(self, results):
        if 'methods' in results and 'noise' in results['methods']:
            data = results['methods']['noise']
            text = f"Noise Standard Deviation: {data.get('noise_std', 'N/A')}\n"
            text += f"Noise Variance: {data.get('noise_variance', 'N/A')}\n"
            text += f"Suspicion Score: {data.get('suspicion_score', 'N/A')}"
            self.noise_text.setPlainText(text)

    def update_color_tab(self, results):
        if 'methods' in results and 'color_space' in results['methods']:
            data = results['methods']['color_space']
            text = f"Cb Entropy: {data.get('cb_entropy', 'N/A')}\n"
            text += f"Cr Entropy: {data.get('cr_entropy', 'N/A')}\n"
            text += f"Suspicion Score: {data.get('suspicion_score', 'N/A')}"
            self.color_text.setPlainText(text)
            
    def update_ela_tab(self, results):
        """Update the ELA tab with results from the main analysis orchestrator"""
        if 'methods' in results and 'ela' in results['methods']:
            data = results['methods']['ela']
            score = data.get('suspicion_score', 0)
            
            # Determine color based on score
            color = "#e74c3c" if score >= 50 else "#27ae60"
            
            # Update the label in the ELA tab
            self.ela_score_label.setText(f"ELA Score: {score:.1f}/100")
            self.ela_score_label.setStyleSheet(
                f"QLabel {{ font-size: 13px; font-weight: bold; color: {color}; }}"
            )

    def update_ghost_tab(self, results):
        if 'methods' in results and 'jpeg_ghost' in results['methods']:
            data = results['methods']['jpeg_ghost']
            text = f"Best Fit Quality: {data.get('best_fit_quality', 'N/A')}\n"
            text += f"Min MAE: {data.get('min_mae', 'N/A')}\n"
            text += f"Suspicion Score: {data.get('suspicion_score', 'N/A')}"
            self.ghost_text.setPlainText(text)
    
    def update_details_results(self, results):
        """Update detailed results display"""
        import json
        
        # Handle different result structures
        if 'ml_prediction' in results:
            # ML results - format nicely
            details = f"ML Analysis Results:\n"
            details += "=" * 50 + "\n"
            details += f"Filename: {results['filename']}\n"
            details += f"Prediction: {'STEGANOGRAPHY' if results['ml_prediction'] == 1 else 'CLEAN'}\n"
            details += f"Probability: {results['ml_probability']:.4f}\n"
            details += f"Confidence: {results['ml_confidence']:.4f}\n"
            details += f"Method: {results['method']}\n"
        else:
            # Heuristic results
            details = json.dumps(results, indent=2, default=str)
        
        self.details_text.setPlainText(details)
    
    def update_methods_results(self, results):
        """Update methods results display"""
        if 'methods' in results:
            # Heuristic results
            methods = results['methods']
            method_text = "Method Analysis Results:\n\n"
            
            for method_name, method_results in methods.items():
                method_text += f"{method_name.upper()}:\n"
                for key, value in method_results.items():
                    if isinstance(value, (int, float)):
                        method_text += f"  {key}: {value:.4f}\n"
                    else:
                        method_text += f"  {key}: {value}\n"
                method_text += "\n"
            
            self.methods_text.setPlainText(method_text)
        else:
            # ML results - show ML-specific info
            method_text = "ML Model Analysis:\n"
            method_text += "=" * 50 + "\n"
            method_text += "Model Type: Random Forest Classifier\n"
            method_text += "Features Used: 70+ ML features\n"
            method_text += "Prediction Method: Probability-based classification\n"
            method_text += f"Confidence: {results.get('ml_confidence', 'N/A')}\n"
            method_text += f"Method: {results.get('method', 'ML-based')}\n"
            
            self.methods_text.setPlainText(method_text)
    
    def create_clone_tab(self):
        """Create the Clone Detection results tab"""
        self.clone_tab = QWidget()
        layout = QVBoxLayout()
        self.clone_text = QTextEdit()
        self.clone_text.setReadOnly(True)
        self.clone_text.setStyleSheet("font-family: Consolas; background: #f9f9f9;")
        layout.addWidget(QLabel("Clone Analysis (Copy-Move Forgery):"))
        layout.addWidget(self.clone_text)
        self.clone_tab.setLayout(layout)
    
    def update_clone_tab(self, results):
        if 'methods' in results and 'clone_detection' in results['methods']:
            data = results['methods']['clone_detection']
            text = f"Identical Patches Found: {data.get('clone_matches', 'N/A')}\n"
            text += f"Suspicion Score: {data.get('suspicion_score', 'N/A')}\n"
            text += "\nNote: High match counts suggest that parts of the image were copied and pasted."
            self.clone_text.setPlainText(text)

    
    
    def clear_results(self):
        """Clear all results"""
        self.result_label.setText("No analysis performed")
        self.result_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; padding: 20px; }")
        self.score_label.setText("Suspicion Score: N/A")
        self.status_indicator.setText("Status: Unknown")
        self.details_text.clear()
        self.methods_text.clear()
    
    def generate_heatmap(self):
        """Generate heatmap for current image"""
        if not self.current_image_path:
            self.show_error("No image loaded")
            return
        
        try:
            from src.core.heatmap_generator import HeatmapGenerator
            from src.core.ml_classifier import MLSteganalysisClassifier
            
            method = self.heatmap_method_combo.currentText().lower()
            generator = HeatmapGenerator()
            
            # Generate unique output filename
            import time
            timestamp = int(time.time())
            output_path = f"heatmap_{method}_{timestamp}.png"
            
            self.status_bar.showMessage(f"Generating {method} heatmap...")
            
            if method == 'lsb':
                heatmap = generator.generate_lsb_heatmap(self.current_image_path, output_path)
            elif method == 'comprehensive':
                heatmaps = generator.generate_comprehensive_heatmap(self.current_image_path, output_path)
                self.status_bar.showMessage(f"Generated {len(heatmaps)} heatmap(s)")
            elif method == 'ml':
                model_path = 'models/steg_model.pkl'
                if not Path(model_path).exists():
                    self.show_error("No trained ML model found. Train a model first with 'train-model' command")
                    return
                classifier = MLSteganalysisClassifier(model_path)
                heatmap = generator.generate_ml_heatmap(self.current_image_path, classifier, output_path)
            
            # Verify the file was created
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                self.status_bar.showMessage(f"Heatmap saved: {output_path} ({file_size:,} bytes)")
                
                # Display heatmap
                pixmap = QPixmap(output_path)
                self.heatmap_label.setPixmap(pixmap.scaled(
                    self.heatmap_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))
                
                # Switch to heatmap tab
                self.results_tab.setCurrentIndex(2)
            else:
                self.show_error(f"Heatmap file not created: {output_path}")
                
        except Exception as e:
            self.status_bar.showMessage(f"Error generating heatmap: {e}")
            self.show_error(f"Error generating heatmap: {e}\n{type(e).__name__}: {e}")
                
    
    def export_results(self):
        """Export analysis results"""
        if not self.analysis_results:
            self.show_error("No results to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Export Results',
            '',
            'JSON Files (*.json);;CSV Files (*.csv);;All Files (*)'
        )
        
        if file_path:
            try:
                import json
                import csv
                
                if file_path.endswith('.csv'):
                    # Export as CSV
                    with open(file_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        # Write headers
                        writer.writerow(['Filename', 'Prediction', 'Probability', 'Confidence', 'Status'])
                        # Write data
                        result = self.analysis_results
                        if 'ml_prediction' in result:
                            writer.writerow([
                                result['filename'],
                                'STEGO' if result['ml_prediction'] == 1 else 'CLEAN',
                                f"{result['ml_probability']:.4f}",
                                f"{result['ml_confidence']:.4f}",
                                'STEGO' if result['ml_prediction'] == 1 else 'CLEAN'
                            ])
                        else:
                            writer.writerow([
                                result['filename'],
                                'STEGO' if result.get('final_suspicion_score', 0) >= 50 else 'CLEAN',
                                f"{result.get('final_suspicion_score', 0):.2f}",
                                'N/A',
                                'STEGO' if result.get('final_suspicion_score', 0) >= 50 else 'CLEAN'
                            ])
                else:
                    # Export as JSON
                    with open(file_path, 'w') as f:
                        json.dump(self.analysis_results, f, indent=2, default=str)
                
                self.status_bar.showMessage(f"Results exported to {file_path}")
                
            except Exception as e:
                self.show_error(f"Error exporting results: {e}")
    
    def batch_process(self):
        """Batch process images"""
        dialog = BatchProcessingDialog(self)
        dialog.exec_()

    
    def train_model(self):
        """Train ML model"""
        dialog = TrainModelDialog(self)
        dialog.exec_()

    
    def show_about(self):
        """Show about dialog"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(self, "About StegHunter", 
            "StegHunter v1.0.0\n\n"
            "Advanced Steganography Detection Tool\n\n"
            "Features:\n"
            "• Multiple detection methods (heuristic & ML)\n"
            "• Visual heatmaps\n"
            "• Batch processing\n"
            "• Export capabilities\n\n"
            "Built with Python, PyQt5, and scikit-learn")
    
    def show_error(self, message):
        """Show error message"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Error", message)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up temporary files
        temp_heatmaps = list(Path('.').glob('temp_heatmap*.png'))
        for temp_file in temp_heatmaps:
            try:
                temp_file.unlink()
            except:
                pass
        
        event.accept()
        
    def export_pdf_report(self):
        """Export analysis results as PDF report"""
        if not self.analysis_results:
            self.show_error("No analysis results to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Export PDF Report',
            '',
            'PDF Files (*.pdf)'
        )
        
        if file_path:
            try:
                reporter = PDFReporter()
                
                # Get heatmap path if available
                heatmap_path = None
                if hasattr(self, 'last_heatmap_path'):
                    heatmap_path = self.last_heatmap_path
                
                pdf_path = reporter.create_single_image_report(
                    self.current_image_path,
                    self.analysis_results,
                    heatmap_path,
                    file_path
                )
                
                self.status_bar.showMessage(f"PDF report saved to {pdf_path}")
                QMessageBox.information(self, "Success", f"PDF report saved to:\n{pdf_path}")
                
            except Exception as e:
                self.show_error(f"Error creating PDF report: {e}")
    
    def export_batch_pdf(self, results):
        """Export batch results as PDF report"""
        if not results:
            self.show_error("No batch results to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Export Batch PDF Report',
            '',
            'PDF Files (*.pdf)'
        )
        
        if file_path:
            try:
                reporter = PDFReporter()
                pdf_path = reporter.create_batch_report(results, file_path)
                
                self.status_bar.showMessage(f"Batch PDF report saved to {pdf_path}")
                QMessageBox.information(self, "Success", f"Batch PDF report saved to:\n{pdf_path}")
                
            except Exception as e:
                self.show_error(f"Error creating batch PDF report: {e}")


def main():
    """Main entry point for GUI application"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()