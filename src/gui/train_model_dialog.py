"""
Model Training Dialog for StegHunter
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QProgressBar, QTextEdit, QFileDialog, QCheckBox, QComboBox,
                             QGroupBox, QLineEdit, QDoubleSpinBox, QSpinBox, QMessageBox,
                             QListWidget, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from pathlib import Path
import time
from src.core.ml_classifier import MLSteganalysisClassifier

class ModelTrainingWorker(QThread):
    """Worker thread for model training"""
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, clean_dir, stego_dir, output_path, test_size, verbose):
        super().__init__()
        self.clean_dir = clean_dir
        self.stego_dir = stego_dir
        self.output_path = output_path
        self.test_size = test_size
        self.verbose = verbose
    
    def run(self):
        try:
            self.log_signal.emit("Starting model training...")
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
            self.log_signal.emit("Training Random Forest classifier...")
            classifier = MLSteganalysisClassifier()
            metrics = classifier.train_model(clean_images, stego_images, self.output_path, self.test_size)
            
            self.progress_signal.emit(90)
            self.log_signal.emit("Model training completed!")
            
            # Emit results
            self.finished_signal.emit(metrics)
            
        except Exception as e:
            self.error_signal.emit(str(e))

class TrainModelDialog(QDialog):
    """Dialog for training ML models"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Train ML Model - StegHunter")
        self.setGeometry(200, 200, 800, 700)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Training Data Selection
        data_group = QGroupBox("Training Data")
        data_layout = QVBoxLayout()
        
        # Clean images
        clean_layout = QHBoxLayout()
        self.clean_label = QLabel("Clean Images Directory:")
        self.clean_path = QLineEdit()
        self.clean_path.setPlaceholderText("Select directory with clean images")
        clean_browse = QPushButton("Browse...")
        clean_browse.clicked.connect(self.select_clean_directory)
        clean_layout.addWidget(self.clean_label)
        clean_layout.addWidget(self.clean_path)
        clean_layout.addWidget(clean_browse)
        data_layout.addLayout(clean_layout)
        
        # Stego images
        stego_layout = QHBoxLayout()
        self.stego_label = QLabel("Stego Images Directory:")
        self.stego_path = QLineEdit()
        self.stego_path.setPlaceholderText("Select directory with stego images")
        stego_browse = QPushButton("Browse...")
        stego_browse.clicked.connect(self.select_stego_directory)
        stego_layout.addWidget(self.stego_label)
        stego_layout.addWidget(self.stego_path)
        stego_layout.addWidget(stego_browse)
        data_layout.addLayout(stego_layout)
        
        # Output model
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Output Model File:")
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("models/steg_model.pkl")
        self.output_path.setText("models/steg_model.pkl")
        output_browse = QPushButton("Browse...")
        output_browse.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_browse)
        data_layout.addLayout(output_layout)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Training Parameters
        params_group = QGroupBox("Training Parameters")
        params_layout = QVBoxLayout()
        
        # Test size
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Test Size:"))
        self.test_size_spin = QDoubleSpinBox()
        self.test_size_spin.setRange(0.1, 0.5)
        self.test_size_spin.setSingleStep(0.05)
        self.test_size_spin.setValue(0.2)
        self.test_size_spin.setSuffix(" (20%)")
        test_layout.addWidget(self.test_size_spin)
        test_layout.addStretch()
        params_layout.addLayout(test_layout)
        
        # Verbose option
        self.verbose_check = QCheckBox("Verbose Output (show feature importance)")
        self.verbose_check.setChecked(True)
        params_layout.addWidget(self.verbose_check)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Training Section
        train_group = QGroupBox("Model Training")
        train_layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        train_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to start training")
        self.status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        train_layout.addWidget(self.status_label)
        
        # Log output
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("QTextEdit { font-family: Consolas, monospace; font-size: 10px; }")
        train_layout.addWidget(self.log_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.train_btn = QPushButton("Start Training")
        self.train_btn.clicked.connect(self.start_training)
        button_layout.addWidget(self.train_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        train_layout.addLayout(button_layout)
        train_group.setLayout(train_layout)
        layout.addWidget(train_group)
        
        # Results Section
        results_group = QGroupBox("Training Results")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        self.setLayout(layout)
    
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
    
    def start_training(self):
        """Start model training"""
        clean_dir = self.clean_path.text()
        stego_dir = self.stego_path.text()
        output_path = self.output_path.text()
        
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
            verbose=self.verbose_check.isChecked()
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
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def training_finished(self, metrics):
        """Handle training completion"""
        self.progress_bar.setValue(100)
        self.status_label.setText("Training completed successfully!")
        self.add_log("✓ Model training completed successfully")
        
        # Display results
        self.display_results(metrics)
        
        # Re-enable UI
        self.train_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        
        # Show success message
        QMessageBox.information(self, "Success", f"Model trained and saved to:\n{self.output_path.text()}")
    
    def training_error(self, error_message):
        """Handle training errors"""
        self.status_label.setText(f"Error: {error_message}")
        self.add_log(f"✗ Error: {error_message}")
        
        # Re-enable UI
        self.train_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Error", f"Training failed:\n{error_message}")
    
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