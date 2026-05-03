"""
Modern GUI Styling for StegHunter
Dark theme with vibrant accent colors
"""

MODERN_STYLESHEET = """
/* Main Window */
QMainWindow {
    background-color: #1a1a2e;
    color: #e0e0e0;
}

/* Central Widget */
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
}

/* Menu Bar */
QMenuBar {
    background-color: #16213e;
    color: #e0e0e0;
    border-bottom: 2px solid #00d4ff;
}

QMenuBar::item:selected {
    background-color: #0f3460;
}

/* Menu */
QMenu {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #00d4ff;
}

QMenu::item:selected {
    background-color: #0f3460;
}

/* Toolbar */
QToolBar {
    background-color: #16213e;
    border-bottom: 2px solid #00d4ff;
    spacing: 5px;
}

QToolBar::separator {
    background-color: #00d4ff;
    width: 2px;
    margin: 0px 5px;
}

/* Push Buttons */
QPushButton {
    background-color: #00d4ff;
    color: #000000;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11px;
}

QPushButton:hover {
    background-color: #00e5ff;
    transform: scale(1.05);
}

QPushButton:pressed {
    background-color: #00b8cc;
}

QPushButton:disabled {
    background-color: #555555;
    color: #888888;
}

/* Primary Button Variant */
QPushButton#primaryButton {
    background-color: #ff006e;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background-color: #ff1493;
}

/* Danger Button Variant */
QPushButton#dangerButton {
    background-color: #ff0000;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background-color: #cc0000;
}

/* Success Button Variant */
QPushButton#successButton {
    background-color: #00cc44;
    color: #000000;
}

QPushButton#successButton:hover {
    background-color: #00ff55;
}

/* Group Boxes */
QGroupBox {
    border: 2px solid #00d4ff;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    color: #e0e0e0;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 5px 10px;
    background-color: #16213e;
    color: #00d4ff;
}

/* Line Edits */
QLineEdit {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 2px solid #00d4ff;
    border-radius: 5px;
    padding: 5px;
    selection-background-color: #00d4ff;
    selection-color: #000000;
}

QLineEdit:focus {
    border: 2px solid #ff006e;
    background-color: #133a5c;
}

QLineEdit::placeholder {
    color: #666666;
}

/* Text Edit */
QTextEdit {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 2px solid #00d4ff;
    border-radius: 5px;
    padding: 5px;
    font-family: Consolas, monospace;
    selection-background-color: #00d4ff;
    selection-color: #000000;
}

QTextEdit:focus {
    border: 2px solid #ff006e;
}

/* Labels */
QLabel {
    color: #e0e0e0;
    font-size: 10px;
}

QLabel#titleLabel {
    color: #00d4ff;
    font-size: 16px;
    font-weight: bold;
}

QLabel#statusLabel {
    color: #00cc44;
    font-weight: bold;
}

QLabel#warningLabel {
    color: #ffaa00;
}

QLabel#errorLabel {
    color: #ff0000;
}

/* Progress Bar */
QProgressBar {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 2px solid #00d4ff;
    border-radius: 5px;
    text-align: center;
    height: 25px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #00d4ff,
                                stop:0.5 #0099cc,
                                stop:1 #00d4ff);
    border-radius: 3px;
}

/* Combo Box */
QComboBox {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 2px solid #00d4ff;
    border-radius: 5px;
    padding: 5px;
    selection-background-color: #00d4ff;
}

QComboBox:hover {
    border: 2px solid #ff006e;
}

QComboBox::drop-down {
    border: none;
    background-color: #00d4ff;
}

QComboBox::down-arrow {
    image: none;
    color: #000000;
}

QComboBox QAbstractItemView {
    background-color: #0f3460;
    color: #e0e0e0;
    selection-background-color: #00d4ff;
    selection-color: #000000;
    border: 1px solid #00d4ff;
}

/* Slider */
QSlider::groove:horizontal {
    background-color: #0f3460;
    height: 10px;
    border-radius: 5px;
    border: 1px solid #00d4ff;
}

QSlider::handle:horizontal {
    background-color: #00d4ff;
    width: 18px;
    margin: -4px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background-color: #ff006e;
}

/* Spinbox */
QSpinBox, QDoubleSpinBox {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 2px solid #00d4ff;
    border-radius: 5px;
    padding: 5px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    background-color: #00d4ff;
    border: none;
    width: 20px;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #00d4ff;
    border: none;
    width: 20px;
}

/* Checkbox */
QCheckBox {
    color: #e0e0e0;
    spacing: 5px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #00d4ff;
    border-radius: 3px;
    background-color: #0f3460;
}

QCheckBox::indicator:hover {
    border: 2px solid #ff006e;
    background-color: #133a5c;
}

QCheckBox::indicator:checked {
    background-color: #00d4ff;
    border: 2px solid #00d4ff;
}

/* Tab Widget */
QTabWidget::pane {
    border: 2px solid #00d4ff;
    background-color: #1a1a2e;
}

QTabBar::tab {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 2px solid #00d4ff;
    padding: 8px 20px;
    border-radius: 5px;
    margin: 2px;
}

QTabBar::tab:selected {
    background-color: #00d4ff;
    color: #000000;
    font-weight: bold;
}

QTabBar::tab:hover {
    background-color: #133a5c;
}

/* Scrollbar */
QScrollBar:vertical {
    background-color: #0f3460;
    width: 12px;
    border: 1px solid #00d4ff;
}

QScrollBar::handle:vertical {
    background-color: #00d4ff;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #ff006e;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
    background-color: #00d4ff;
}

QScrollBar:horizontal {
    background-color: #0f3460;
    height: 12px;
    border: 1px solid #00d4ff;
}

QScrollBar::handle:horizontal {
    background-color: #00d4ff;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #ff006e;
}

/* Table Widget */
QTableWidget {
    background-color: #0f3460;
    alternate-background-color: #133a5c;
    color: #e0e0e0;
    gridline-color: #00d4ff;
    border: 2px solid #00d4ff;
    border-radius: 5px;
}

QTableWidget::item {
    padding: 5px;
}

QTableWidget::item:selected {
    background-color: #00d4ff;
    color: #000000;
}

QHeaderView::section {
    background-color: #00d4ff;
    color: #000000;
    padding: 5px;
    border: none;
    font-weight: bold;
}

/* Tree Widget */
QTreeWidget {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 2px solid #00d4ff;
    border-radius: 5px;
}

QTreeWidget::item:selected {
    background-color: #00d4ff;
    color: #000000;
}

/* Dialog */
QDialog {
    background-color: #1a1a2e;
    color: #e0e0e0;
}

/* Splitter */
QSplitter::handle {
    background-color: #00d4ff;
    width: 3px;
}

QSplitter::handle:hover {
    background-color: #ff006e;
}

/* Status Bar */
QStatusBar {
    background-color: #16213e;
    color: #e0e0e0;
    border-top: 2px solid #00d4ff;
}

/* Message Box */
QMessageBox QLabel {
    color: #e0e0e0;
}

QMessageBox QPushButton {
    min-width: 70px;
}
"""

def apply_modern_style(app):
    """Apply modern stylesheet to QApplication"""
    app.setStyle('Fusion')
    app.setStyleSheet(MODERN_STYLESHEET)
