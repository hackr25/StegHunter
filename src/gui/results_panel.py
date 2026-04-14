from PyQt5 import QtWidgets, QtCore, QtGui

class ResultsPanel(QtWidgets.QWidget):
    """
    A professional forensic results display panel that 
    visualizes the ReasoningEngine's output.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- 1. Verdict Header ---
        self.verdict_label = QtWidgets.QLabel("WAITING FOR ANALYSIS")
        self.verdict_label.setAlignment(QtCore.Qt.AlignCenter)
        self.verdict_label.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: #888; 
            padding: 10px;
            border-radius: 5px;
            background-color: #f0f0f0;
        """)
        layout.addWidget(self.verdict_label)

        # --- 2. Suspicion Score Bar ---
        score_container = QtWidgets.QVBoxLayout()
        self.score_label = QtWidgets.QLabel("Suspicion Score: 0%")
        self.score_label.setAlignment(QtCore.Qt.AlignRight)
        
        self.score_bar = QtWidgets.QProgressBar()
        self.score_bar.setRange(0, 100)
        self.score_bar.setValue(0)
        self.score_bar.setTextVisible(False)
        self.score_bar.setFixedHeight(20)
        
        score_container.addWidget(self.score_label)
        score_container.addWidget(self.score_bar)
        layout.addLayout(score_container)

        # --- 3. Detailed Findings (The Explainability Part) ---
        findings_label = QtWidgets.QLabel("Forensic Evidence:")
        findings_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(findings_label)

        self.findings_box = QtWidgets.QTextEdit()
        self.findings_box.setReadOnly(True)
        self.findings_box.setPlaceholderText("Detailed forensic markers will appear here...")
        self.findings_box.setStyleSheet("background-color: #fafafa; border: 1px solid #ddd; font-family: Consolas, Monaco, monospace;")
        layout.addWidget(self.findings_box)

        # --- 4. Summary Footer ---
        self.summary_label = QtWidgets.QLabel("Ready to analyze image.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-style: italic; color: #666;")
        layout.addWidget(self.summary_label)

    def update_results(self, results: dict):
        """
        Populates the panel with data from the analyzer.
        Expected input: The results dictionary from analyzer.analyze_image()
        """
        # Extract data from the reasoning engine output
        explanation = results.get("explanation", {})
        final_score = results.get("final_suspicion_score", 0)
        
        # Update Score
        self.score_bar.setValue(int(final_score))
        self.score_label.setText(f"Suspicion Score: {final_score}%")

        # Update Verdict and Colors
        verdict = explanation.get("verdict", "Unknown")
        self.verdict_label.setText(verdict.upper())
        
        if final_score > 70:
            # Danger Red
            self.verdict_label.setStyleSheet("font-size: 22px; font-weight: bold; color: white; background-color: #d32f2f; padding: 10px; border-radius: 5px;")
            self.score_bar.setStyleSheet("QProgressBar::chunk { background-color: #d32f2f; }")
        elif final_score > 40:
            # Warning Orange
            self.verdict_label.setStyleSheet("font-size: 22px; font-weight: bold; color: white; background-color: #f57c00; padding: 10px; border-radius: 5px;")
            self.score_bar.setStyleSheet("QProgressBar::chunk { background-color: #f57c00; }")
        else:
            # Safe Green
            self.verdict_label.setStyleSheet("font-size: 22px; font-weight: bold; color: white; background-color: #388e3c; padding: 10px; border-radius: 5px;")
            self.score_bar.setStyleSheet("QProgressBar::chunk { background-color: #388e3c; }")

        # Update Detailed Findings
        findings = explanation.get("detailed_findings", [])
        if findings:
            text = ""
            for item in findings:
                text += f"• {item}\n\n"
            self.findings_box.setPlainText(text)
        else:
            self.findings_box.setPlainText("No significant markers were detected in this image.")

        # Update Summary
        self.summary_label.setText(explanation.get("summary", "Analysis completed successfully."))
