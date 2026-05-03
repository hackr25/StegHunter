"""
Model Training Dialog for StegHunter - Enhanced Modern Design
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QProgressBar, QTextEdit, QFileDialog, QCheckBox, QComboBox,
                             QGroupBox, QLineEdit, QDoubleSpinBox, QSpinBox, QMessageBox,
                             QListWidget, QTableWidget, QTableWidgetItem, QScrollArea, QWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from pathlib import Path
import time
from src.core.ml_classifier import MLSteganalysisClassifier
from src.gui.modern_components import ModernButton, ModernCard, StatusIndicator, SectionHeader

class ModelTrainingWorker(QThread):
    """Worker thread for model training"""
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, clean_dir, stego_dir, output_path, test_size, verbose,
                 clean_video_dir=None, stego_video_dir=None, use_video_training=False):
        super().__init__()
        self.clean_dir = clean_dir
        self.stego_dir = stego_dir
        self.output_path = output_path
        self.test_size = test_size
        self.verbose = verbose
        self.clean_video_dir = clean_video_dir
        self.stego_video_dir = stego_video_dir
        self.use_video_training = use_video_training
    
    def run(self):
        try:
            if self.use_video_training and (self.clean_video_dir or self.stego_video_dir):
                self.run_video_training()
            else:
                self.run_image_training()
            
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def run_image_training(self):
        """Train on images only"""
        self.log_signal.emit("Starting model training (Images Only)...")
        self.progress_signal.emit(10)
        
        # Collect training images
        self.log_signal.emit("Collecting training images...")
        from src.common.utils import collect_image_files
        clean_images = [str(p) for p in collect_image_files(self.clean_dir)]
        stego_images = [str(p) for p in collect_image_files(self.stego_dir)]
        
        self.log_signal.emit(f"Found {len(clean_images)} clean images")
        self.log_signal.emit(f"Found {len(stego_images)} stego images")
        self.progress_signal.emit(30)
        
        if len(clean_images) == 0 or len(stego_images) == 0:
            self.error_signal.emit("Need at least one clean and one stego image")
            return
        
        # Train model
        self.log_signal.emit("Training all 4 ML models...")
        from src.core.ml_multi_model_manager import MultiModelMLManager
        manager = MultiModelMLManager()
        
        self.progress_signal.emit(50)
        metrics = manager.train_all_models(self.clean_dir, self.stego_dir)
        
        self.progress_signal.emit(90)
        self.log_signal.emit("Model training completed!")
        
        # Emit results
        self.finished_signal.emit(metrics)
    
    def run_video_training(self):
        """Train on images + videos"""
        self.log_signal.emit("Starting model training (Images + Videos)...")
        self.progress_signal.emit(10)
        
        # Collect training images
        self.log_signal.emit("Collecting training images...")
        from src.common.utils import collect_image_files
        clean_images = [str(p) for p in collect_image_files(self.clean_dir)]
        stego_images = [str(p) for p in collect_image_files(self.stego_dir)]
        
        self.log_signal.emit(f"Found {len(clean_images)} clean images")
        self.log_signal.emit(f"Found {len(stego_images)} stego images")
        
        # Collect videos if provided
        if self.clean_video_dir:
            self.log_signal.emit(f"Videos directory (clean): {self.clean_video_dir}")
        if self.stego_video_dir:
            self.log_signal.emit(f"Videos directory (stego): {self.stego_video_dir}")
        
        self.progress_signal.emit(30)
        
        if len(clean_images) == 0 or len(stego_images) == 0:
            self.error_signal.emit("Need at least one clean and one stego image")
            return
        
        # Train models with video support
        self.log_signal.emit("Training all 4 ML models (with video features)...")
        from src.core.ml_multi_model_manager import MultiModelMLManager
        manager = MultiModelMLManager()
        
        self.progress_signal.emit(50)
        metrics = manager.train_all_models_with_video(
            self.clean_dir,
            self.stego_dir,
            self.clean_video_dir,
            self.stego_video_dir
        )
        
        self.progress_signal.emit(90)
        self.log_signal.emit("Model training with video features completed!")
        
        # Emit results
        self.finished_signal.emit(metrics)

class TrainModelDialog(QDialog):
    """Dialog for training ML models"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Train ML Model - StegHunter")
        self.setGeometry(200, 200, 800, 700)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface with modern design"""
        self.setWindowTitle("🎓 Train ML Models - StegHunter")
        self.setGeometry(200, 200, 900, 1000)
        self.setStyleSheet("QDialog { background-color: #1a1a2e; }")
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = SectionHeader("🎯 Model Training Configuration")
        main_layout.addWidget(header)
        
        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background-color: #1a1a2e; border: none; }")
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(15)
        
        # Training Data Selection Card
        data_group = ModernCard("📁 Training Data Selection")
        data_layout = QVBoxLayout()
        
        # Clean images
        clean_layout = QHBoxLayout()
        self.clean_label = QLabel("Clean Images Directory:")
        self.clean_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        self.clean_path = QLineEdit()
        self.clean_path.setPlaceholderText("Select directory with clean images")
        clean_browse = ModernButton("Browse", "primary")
        clean_browse.setMaximumWidth(100)
        clean_browse.clicked.connect(self.select_clean_directory)
        clean_layout.addWidget(self.clean_label)
        clean_layout.addWidget(self.clean_path)
        clean_layout.addWidget(clean_browse)
        data_layout.addLayout(clean_layout)
        
        # Stego images
        stego_layout = QHBoxLayout()
        self.stego_label = QLabel("Stego Images Directory:")
        self.stego_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        self.stego_path = QLineEdit()
        self.stego_path.setPlaceholderText("Select directory with stego images")
        stego_browse = ModernButton("Browse", "primary")
        stego_browse.setMaximumWidth(100)
        stego_browse.clicked.connect(self.select_stego_directory)
        stego_layout.addWidget(self.stego_label)
        stego_layout.addWidget(self.stego_path)
        stego_layout.addWidget(stego_browse)
        data_layout.addLayout(stego_layout)
        
        # Video training option
        self.use_video_check = QCheckBox("🎬 Include Video Training Data")
        self.use_video_check.setStyleSheet("color: #00d4ff; font-weight: bold;")
        self.use_video_check.stateChanged.connect(self.toggle_video_fields)
        data_layout.addWidget(self.use_video_check)
        
        # Clean videos (hidden by default)
        clean_video_layout = QHBoxLayout()
        self.clean_video_label = QLabel("Clean Videos Directory:")
        self.clean_video_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        self.clean_video_path = QLineEdit()
        self.clean_video_path.setPlaceholderText("Select directory with clean videos (MP4, AVI, MOV, etc.)")
        self.clean_video_path.setEnabled(False)
        clean_video_browse = ModernButton("Browse", "primary")
        clean_video_browse.setMaximumWidth(100)
        clean_video_browse.clicked.connect(self.select_clean_video_directory)
        clean_video_browse.setEnabled(False)
        self.clean_video_browse = clean_video_browse
        clean_video_layout.addWidget(self.clean_video_label)
        clean_video_layout.addWidget(self.clean_video_path)
        clean_video_layout.addWidget(clean_video_browse)
        self.clean_video_widget = QWidget()
        self.clean_video_widget.setLayout(clean_video_layout)
        self.clean_video_widget.setVisible(False)
        data_layout.addWidget(self.clean_video_widget)
        
        # Stego videos (hidden by default)
        stego_video_layout = QHBoxLayout()
        self.stego_video_label = QLabel("Stego Videos Directory:")
        self.stego_video_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        self.stego_video_path = QLineEdit()
        self.stego_video_path.setPlaceholderText("Select directory with stego videos (optional)")
        self.stego_video_path.setEnabled(False)
        stego_video_browse = ModernButton("Browse", "primary")
        stego_video_browse.setMaximumWidth(100)
        stego_video_browse.clicked.connect(self.select_stego_video_directory)
        stego_video_browse.setEnabled(False)
        self.stego_video_browse = stego_video_browse
        stego_video_layout.addWidget(self.stego_video_label)
        stego_video_layout.addWidget(self.stego_video_path)
        stego_video_layout.addWidget(stego_video_browse)
        self.stego_video_widget = QWidget()
        self.stego_video_widget.setLayout(stego_video_layout)
        self.stego_video_widget.setVisible(False)
        data_layout.addWidget(self.stego_video_widget)
        
        # Output model
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Output Model File:")
        self.output_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("models/steg_model.pkl")
        self.output_path.setText("models/steg_model.pkl")
        output_browse = ModernButton("Browse", "primary")
        output_browse.setMaximumWidth(100)
        output_browse.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_browse)
        data_layout.addLayout(output_layout)
        
        data_group.add_layout(data_layout)
        scroll_layout.addWidget(data_group)
        
        # Training Parameters Card
        params_group = ModernCard("⚙️ Training Parameters")
        params_layout = QVBoxLayout()
        
        # Test size
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Test Size Ratio:"))
        self.test_size_spin = QDoubleSpinBox()
        self.test_size_spin.setRange(0.1, 0.5)
        self.test_size_spin.setSingleStep(0.05)
        self.test_size_spin.setValue(0.2)
        self.test_size_spin.setSuffix(" (20%)")
        test_layout.addWidget(self.test_size_spin)
        test_layout.addStretch()
        params_layout.addLayout(test_layout)
        
        # Verbose option
        self.verbose_check = QCheckBox("📊 Show Feature Importance (Verbose)")
        self.verbose_check.setStyleSheet("color: #e0e0e0;")
        self.verbose_check.setChecked(True)
        params_layout.addWidget(self.verbose_check)
        
        params_group.add_layout(params_layout)
        scroll_layout.addWidget(params_group)
        
        # Training Status Card
        status_group = ModernCard("📈 Training Progress")
        status_layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        status_layout.addWidget(self.progress_bar)
        
        # Status indicator
        self.status_indicator = StatusIndicator("Ready to start training", "info")
        status_layout.addWidget(self.status_indicator)
        
        # Log output with better styling
        log_label = QLabel("📝 Training Log:")
        log_label.setStyleSheet("color: #00d4ff; font-weight: bold;")
        status_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setMinimumHeight(100)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0f3460;
                color: #00d4ff;
                border: 2px solid #00d4ff;
                border-radius: 5px;
                font-family: Consolas, monospace;
                font-size: 10px;
                padding: 5px;
            }
        """)
        status_layout.addWidget(self.log_text)
        
        status_group.add_layout(status_layout)
        scroll_layout.addWidget(status_group)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.train_btn = ModernButton("🚀 Start Training", "success")
        self.train_btn.setMinimumHeight(40)
        self.train_btn.clicked.connect(self.start_training)
        button_layout.addWidget(self.train_btn)
        
        self.cancel_btn = ModernButton("✕ Cancel", "danger")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        # Results Section
        results_group = ModernCard("✅ Training Results")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setMaximumHeight(200)
        self.results_table.setMinimumHeight(100)
        results_layout.addWidget(self.results_table)
        
        results_group.add_layout(results_layout)
        main_layout.addWidget(results_group)
        
        self.setLayout(main_layout)
    
    def select_clean_directory(self):
        """Select directory with clean images"""
        directory = QFileDialog.getExistingDirectory(self, "Select Clean Images Directory")
        if directory:
            self.clean_path.setText(directory)
    
    def select_stego_directory(self):
        """Select directory with stego images"""
        directory = QFileDialog.getExistingDirectory(self, "Select Stego Images Directory")
        if directory:
            self.stego_path.setText(directory)
    
    def select_clean_video_directory(self):
        """Select directory with clean videos"""
        directory = QFileDialog.getExistingDirectory(self, "Select Clean Videos Directory")
        if directory:
            self.clean_video_path.setText(directory)
    
    def select_stego_video_directory(self):
        """Select directory with stego videos"""
        directory = QFileDialog.getExistingDirectory(self, "Select Stego Videos Directory")
        if directory:
            self.stego_video_path.setText(directory)
    
    def select_output_file(self):
        """Select output model file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Model As",
            self.output_path.text(),
            "Pickle Files (*.pkl)"
        )
        
        if file_path:
            self.output_path.setText(file_path)
    
    def toggle_video_fields(self):
        """Toggle video input fields visibility"""
        is_checked = self.use_video_check.isChecked()
        self.clean_video_widget.setVisible(is_checked)
        self.stego_video_widget.setVisible(is_checked)
        self.clean_video_path.setEnabled(is_checked)
        self.clean_video_browse.setEnabled(is_checked)
        self.stego_video_path.setEnabled(is_checked)
        self.stego_video_browse.setEnabled(is_checked)
    
    def start_training(self):
        """Start model training"""
        clean_dir = self.clean_path.text()
        stego_dir = self.stego_path.text()
        output_path = self.output_path.text()
        use_video = self.use_video_check.isChecked()
        clean_video_dir = self.clean_video_path.text() if use_video else None
        stego_video_dir = self.stego_video_path.text() if use_video else None
        
        if not clean_dir or not stego_dir:
            QMessageBox.warning(self, "Warning", "Please select both clean and stego directories")
            return
        
        if not output_path:
            QMessageBox.warning(self, "Warning", "Please specify an output file")
            return
        
        # Validate directories
        if not Path(clean_dir).exists():
            QMessageBox.warning(self, "Warning", "Clean directory does not exist")
            return
        
        if not Path(stego_dir).exists():
            QMessageBox.warning(self, "Warning", "Stego directory does not exist")
            return
        
        if use_video and clean_video_dir and not Path(clean_video_dir).exists():
            QMessageBox.warning(self, "Warning", "Clean video directory does not exist")
            return
        
        if use_video and stego_video_dir and not Path(stego_video_dir).exists():
            QMessageBox.warning(self, "Warning", "Stego video directory does not exist")
            return
        
        # Disable UI during training
        self.train_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.results_table.setRowCount(0)
        
        # Start worker thread
        self.worker = ModelTrainingWorker(
            clean_dir=clean_dir,
            stego_dir=stego_dir,
            output_path=output_path,
            test_size=self.test_size_spin.value(),
            verbose=self.verbose_check.isChecked(),
            clean_video_dir=clean_video_dir,
            stego_video_dir=stego_video_dir,
            use_video_training=use_video
        )
        
        # Connect signals
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.log_signal.connect(self.add_log)
        self.worker.finished_signal.connect(self.training_finished)
        self.worker.error_signal.connect(self.training_error)
        
        self.worker.start()
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def add_log(self, message):
        """Add message to log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        self.log_text.append(formatted_msg)
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def training_finished(self, metrics):
        """Handle training completion"""
        self.progress_bar.setValue(100)
        
        training_mode = "Images + Videos" if self.use_video_check.isChecked() else "Images Only"
        status_text = f"✅ Training completed successfully! (Mode: {training_mode})"
        self.status_indicator.update_status("success")
        self.status_indicator.set_text(status_text)
        self.add_log(f"✓ Model training completed successfully ({training_mode})")
        
        # Display results
        self.display_results(metrics)
        
        # Re-enable UI
        self.train_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        
        # Show success message
        QMessageBox.information(
            self, 
            "✅ Training Successful",
            f"Model trained and saved to:\n{self.output_path.text()}\n\nTraining Mode: {training_mode}"
        )
    
    def training_error(self, error_message):
        """Handle training errors"""
        status_text = f"❌ Error: {error_message}"
        self.status_indicator.update_status("error")
        self.status_indicator.set_text(status_text)
        self.add_log(f"✗ Error: {error_message}")
        
        # Re-enable UI
        self.train_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "❌ Training Failed", f"Training failed:\n{error_message}")
    
    def display_results(self, metrics):
        """Display training results in table"""
        # Clear existing results
        self.results_table.setRowCount(0)
        
        # Add basic metrics
        metrics_to_show = [
            ("Accuracy", f"{metrics['accuracy']:.4f}"),
            ("Precision", f"{metrics['precision']:.4f}"),
            ("Recall", f"{metrics['recall']:.4f}"),
            ("F1-Score", f"{metrics['f1_score']:.4f}"),
            ("Cross-Validation Mean", f"{metrics['cv_mean']:.4f} (±{metrics['cv_std']:.4f})")
        ]
        
        for metric, value in metrics_to_show:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(metric))
            self.results_table.setItem(row, 1, QTableWidgetItem(value))
        
        # Add feature importance if available and verbose
        if self.verbose_check.isChecked() and 'feature_importance' in metrics:
            self.results_table.insertRow(self.results_table.rowCount())
            self.results_table.setItem(self.results_table.rowCount()-1, 0, QTableWidgetItem("Feature Importance"))
            self.results_table.setItem(self.results_table.rowCount()-1, 1, QTableWidgetItem("Top 10 features:"))
            
            # Sort features by importance
            sorted_features = sorted(metrics['feature_importance'].items(), 
                                   key=lambda x: x[1], reverse=True)[:10]
            
            for feature, importance in sorted_features:
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                self.results_table.setItem(row, 0, QTableWidgetItem(f"  {feature}"))
                self.results_table.setItem(row, 1, QTableWidgetItem(f"{importance:.4f}"))