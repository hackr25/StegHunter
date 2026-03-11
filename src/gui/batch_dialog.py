"""
Batch Processing Dialog for StegHunter
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QProgressBar, QTextEdit, QFileDialog, QCheckBox, QComboBox,
                             QGroupBox, QListWidget, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from pathlib import Path
import time
from src.core.analyzer import SteganographyAnalyzer
from src.core.ml_classifier import MLSteganalysisClassifier

class BatchProcessingWorker(QThread):
    """Worker thread for batch processing"""
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)
    
    def __init__(self, directory, recursive, use_ml, model_path, output_path, output_format):
        super().__init__()
        self.directory = directory
        self.recursive = recursive
        self.use_ml = use_ml
        self.model_path = model_path
        self.output_path = output_path
        self.output_format = output_format
        self.analyzer = SteganographyAnalyzer()
        self.results = []
    
    def run(self):
        try:
            # Collect image files
            image_files = self.collect_image_files(Path(self.directory), self.recursive)
            
            if not image_files:
                self.error_signal.emit("No image files found in the selected directory")
                return
            
            self.log_signal.emit(f"Found {len(image_files)} image files")
            
            # Load ML model if needed
            classifier = None
            if self.use_ml:
                if not Path(self.model_path).exists():
                    self.error_signal.emit("ML model not found. Please train a model first.")
                    return
                classifier = MLSteganalysisClassifier(self.model_path)
            
            # Process each file
            total_files = len(image_files)
            for i, file_path in enumerate(image_files):
                try:
                    self.log_signal.emit(f"Processing {file_path.name}...")
                    
                    if self.use_ml and classifier:
                        result = classifier.predict(str(file_path))
                        analysis_result = {
                            'filename': file_path.name,
                            'file_path': str(file_path),
                            'method': 'ML-based',
                            'prediction': result['prediction'],
                            'probability': result['probability'],
                            'confidence': result['confidence'],
                            'status': 'STEGO' if result['prediction'] == 1 else 'CLEAN'
                        }
                    else:
                        result = self.analyzer.analyze_image(file_path)
                        analysis_result = {
                            'filename': file_path.name,
                            'file_path': str(file_path),
                            'method': 'Heuristic',
                            'final_score': result.get('final_suspicion_score', 0),
                            'basic_score': result.get('methods', {}).get('basic', {}).get('basic_suspicion_score', 0),
                            'lsb_score': result.get('methods', {}).get('lsb', {}).get('lsb_suspicion_score', 0),
                            'status': 'High Suspicion' if result.get('final_suspicion_score', 0) >= 50 else 'Low Suspicion'
                        }
                    
                    self.results.append(analysis_result)
                    
                    # Update progress
                    progress = int((i + 1) / total_files * 100)
                    self.progress_signal.emit(progress, f"Processed {i+1}/{total_files} files")
                    self.log_signal.emit(f"✓ {file_path.name}: {analysis_result.get('status', 'Completed')}")
                    
                except Exception as e:
                    self.log_signal.emit(f"✗ {file_path.name}: Error - {str(e)}")
                    continue
            
            # Save results
            if self.output_path:
                self.save_results(self.results, self.output_path, self.output_format)
            
            self.finished_signal.emit(self.results)
            
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def collect_image_files(self, directory, recursive):
        """Collect image files from directory using shared utility."""
        from src.common.utils import collect_image_files
        return collect_image_files(directory, recursive)
    
    def save_results(self, results, output_path, output_format):
        """Save results to file"""
        try:
            if output_format == 'csv':
                self.save_csv(results, output_path)
            else:
                self.save_json(results, output_path)
            self.log_signal.emit(f"Results saved to {output_path}")
        except Exception as e:
            self.error_signal.emit(f"Error saving results: {e}")
    
    def save_csv(self, results, output_path):
        """Save results as CSV using shared utility."""
        if not results:
            self.log_signal.emit("No results to save")
            return
        try:
            from src.common.utils import save_results_csv
            save_results_csv(results, output_path)
            self.log_signal.emit(f"✓ Saved {len(results)} results to CSV")
        except Exception as e:
            self.log_signal.emit(f"✗ Error saving CSV: {e}")
            raise

    
    def save_json(self, results, output_path):
        """Save results as JSON using shared utility."""
        if not results:
            self.log_signal.emit("No results to save")
            return
        try:
            from src.common.utils import save_results_json
            save_results_json(results, output_path)
            self.log_signal.emit(f"✓ Saved {len(results)} results to JSON")
        except Exception as e:
            self.log_signal.emit(f"✗ Error saving JSON: {e}")
            raise


class BatchProcessingDialog(QDialog):
    """Dialog for batch processing images"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Processing - StegHunter")
        self.setGeometry(200, 200, 800, 600)
        self.init_ui()
        
        # Store results
        self.results = []
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Directory selection
        dir_group = QGroupBox("Directory Selection")
        dir_layout = QVBoxLayout()
        
        # Directory path
        path_layout = QHBoxLayout()
        self.dir_label = QLabel("No directory selected")
        self.dir_label.setStyleSheet("QLabel { border: 1px solid #ccc; padding: 5px; background-color: #f9f9f9; }")
        path_layout.addWidget(self.dir_label)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.select_directory)
        path_layout.addWidget(browse_btn)
        
        dir_layout.addLayout(path_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.recursive_check = QCheckBox("Include subdirectories")
        self.recursive_check.setChecked(True)
        options_layout.addWidget(self.recursive_check)
        
        options_layout.addStretch()
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(['Heuristic', 'ML'])
        options_layout.addWidget(QLabel("Method:"))
        options_layout.addWidget(self.method_combo)
        
        dir_layout.addLayout(options_layout)
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        # Output options
        output_group = QGroupBox("Output Options")
        output_layout = QVBoxLayout()
        
        output_path_layout = QHBoxLayout()
        self.output_label = QLabel("No output file selected")
        self.output_label.setStyleSheet("QLabel { border: 1px solid #ccc; padding: 5px; background-color: #f9f9f9; }")
        output_path_layout.addWidget(self.output_label)
        
        output_browse_btn = QPushButton("Browse...")
        output_browse_btn.clicked.connect(self.select_output_file)
        output_path_layout.addWidget(output_browse_btn)
        
        output_layout.addLayout(output_path_layout)
        
        format_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(['JSON', 'CSV'])
        format_layout.addWidget(QLabel("Format:"))
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        
        output_layout.addLayout(format_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Processing section
        process_group = QGroupBox("Processing")
        process_layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        process_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to start batch processing")
        self.status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        process_layout.addWidget(self.status_label)
        
        # Log output
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("QTextEdit { font-family: Consolas, monospace; font-size: 10px; }")
        process_layout.addWidget(self.log_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.export_btn = QPushButton("Export Results")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        process_layout.addLayout(button_layout)
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        self.setLayout(layout)
    
    def select_directory(self):
        """Select directory for batch processing"""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.directory = directory
            self.dir_label.setText(directory)
            
            # Set default output path
            default_output = Path(directory) / "steganalysis_results.json"
            self.output_path = str(default_output)
            self.output_label.setText(self.output_path)
    
    def select_output_file(self):
        """Select output file for results"""
        if not hasattr(self, 'directory'):
            QMessageBox.warning(self, "Warning", "Please select a directory first")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results As",
            self.output_path,
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        
        if file_path:
            self.output_path = file_path
            self.output_label.setText(file_path)
    
    def start_processing(self):
        """Start batch processing"""
        if not hasattr(self, 'directory'):
            QMessageBox.warning(self, "Warning", "Please select a directory first")
            return
        
        if not hasattr(self, 'output_path'):
            QMessageBox.warning(self, "Warning", "Please select an output file")
            return
        
        # Disable UI during processing
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        # Start worker thread
        self.worker = BatchProcessingWorker(
            directory=self.directory,
            recursive=self.recursive_check.isChecked(),
            use_ml=self.method_combo.currentText() == 'ML',
            model_path='models/steg_model.pkl',
            output_path=self.output_path,
            output_format=self.format_combo.currentText().lower()
        )
        
        # Connect signals
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.processing_finished)
        self.worker.error_signal.connect(self.processing_error)
        self.worker.log_signal.connect(self.add_log)
        
        self.worker.start()
    
    def update_progress(self, value, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def processing_finished(self, results):
        """Handle processing completion"""
        self.results = results
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Processing complete! Processed {len(results)} files")
        self.add_log("✓ Batch processing completed successfully")
        
        # Re-enable UI
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
    
    def processing_error(self, error_message):
        """Handle processing errors"""
        self.status_label.setText(f"Error: {error_message}")
        self.add_log(f"✗ Error: {error_message}")
        
        # Re-enable UI
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def add_log(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def export_results(self):
        """Export results to file"""
        if not self.results:
            QMessageBox.information(self, "Info", "No results to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            "",
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.worker.save_csv(self.results, file_path)
                else:
                    self.worker.save_json(self.results, file_path)
                
                QMessageBox.information(self, "Success", f"Results exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export results: {e}")