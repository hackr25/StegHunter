"""
Professional Stylesheet for StegHunter GUI
Clean, business-appropriate design with proper spacing and typography
"""

from PyQt5.QtWidgets import QApplication

# Professional Color Palette
COLORS = {
    'bg_primary': '#F5F5F5',      # Light gray background
    'bg_secondary': '#FFFFFF',    # White for cards/sections
    'bg_hover': '#F0F0F0',        # Hover state
    'text_primary': '#1F1F1F',    # Dark gray for text
    'text_secondary': '#666666',  # Medium gray for secondary text
    'border': '#D0D0D0',          # Subtle borders
    'accent': '#0066CC',          # Professional blue
    'accent_light': '#E6F0FF',    # Light blue background
    'success': '#22863A',         # Professional green
    'warning': '#B08800',         # Professional amber
    'error': '#CB2431',           # Professional red
    'info': '#0366D6',            # Professional info blue
}

PROFESSIONAL_STYLESHEET = f"""
/* Main Window and Central Widget */
QMainWindow {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
}}

QWidget {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
}}

/* Menu Bar */
QMenuBar {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 2px 0px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['accent_light']};
    color: {COLORS['accent']};
}}

QMenu {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
}}

QMenu::item:selected {{
    background-color: {COLORS['accent_light']};
    color: {COLORS['accent']};
}}

/* Tool Bar */
QToolBar {{
    background-color: {COLORS['bg_secondary']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 5px;
    spacing: 5px;
}}

QToolBar::separator {{
    background-color: {COLORS['border']};
    width: 2px;
    margin: 0px 5px;
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: 500;
    font-size: 11pt;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
    border: 1px solid {COLORS['accent']};
    color: {COLORS['accent']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent_light']};
    border: 1px solid {COLORS['accent']};
}}

/* Primary Action Button */
QPushButton#primaryButton {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    font-weight: 600;
}}

QPushButton#primaryButton:hover {{
    background-color: #0052A3;
    color: white;
    border: none;
}}

/* Success Button */
QPushButton#successButton {{
    background-color: {COLORS['success']};
    color: white;
    border: none;
    font-weight: 600;
}}

QPushButton#successButton:hover {{
    background-color: #1D6B27;
    color: white;
}}

/* Warning Button */
QPushButton#warningButton {{
    background-color: {COLORS['warning']};
    color: white;
    border: none;
    font-weight: 600;
}}

QPushButton#warningButton:hover {{
    background-color: #966B00;
    color: white;
}}

/* Error Button */
QPushButton#errorButton {{
    background-color: {COLORS['error']};
    color: white;
    border: none;
    font-weight: 600;
}}

QPushButton#errorButton:hover {{
    background-color: #B91C1C;
    color: white;
}}

/* Labels */
QLabel {{
    color: {COLORS['text_primary']};
    font-size: 10pt;
}}

QLabel#titleLabel {{
    color: {COLORS['text_primary']};
    font-size: 14pt;
    font-weight: 600;
}}

QLabel#subtitleLabel {{
    color: {COLORS['text_secondary']};
    font-size: 11pt;
}}

/* Line Edits and Text Input */
QLineEdit, QPlainTextEdit, QTextEdit {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
    selection-background-color: {COLORS['accent']};
    selection-color: white;
}}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{
    border: 2px solid {COLORS['accent']};
    background-color: {COLORS['bg_secondary']};
}}

/* Combo Boxes */
QComboBox {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 5px;
    min-height: 28px;
}}

QComboBox:focus {{
    border: 2px solid {COLORS['accent']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent_light']};
    selection-color: {COLORS['accent']};
}}

/* Spin Boxes and Sliders */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 5px;
}}

QSlider::groove:horizontal {{
    background-color: {COLORS['border']};
    height: 6px;
    margin: 2px 0px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {COLORS['accent']};
    width: 14px;
    margin: -4px 0px;
    border-radius: 7px;
    border: 1px solid {COLORS['accent']};
}}

QSlider::handle:horizontal:hover {{
    background-color: #0052A3;
}}

/* Checkboxes */
QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['bg_secondary']};
}}

QCheckBox::indicator:hover {{
    border: 1px solid {COLORS['accent']};
    background-color: {COLORS['accent_light']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
    image: url(:/qt-project.org/styles/commonstyle/images/checkbox.png);
}}

/* Progress Bar */
QProgressBar {{
    background-color: {COLORS['border']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    text-align: center;
    height: 20px;
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 3px;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['bg_primary']};
}}

QTabBar::tab {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-radius: 4px 4px 0px 0px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['accent']};
    border: 1px solid {COLORS['border']};
    border-bottom: 3px solid {COLORS['accent']};
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_primary']};
}}

/* Scroll Bars */
QScrollBar:vertical {{
    background-color: {COLORS['bg_primary']};
    width: 14px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border']};
    border-radius: 7px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['accent']};
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_primary']};
    height: 14px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border']};
    border-radius: 7px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['accent']};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    border: none;
    background: none;
}}

/* Group Boxes */
QGroupBox {{
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0px 3px 0px 3px;
    font-weight: 600;
}}

/* Status Bar */
QStatusBar {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
}}

/* Dialogs */
QDialog {{
    background-color: {COLORS['bg_primary']};
}}

/* Tooltips */
QToolTip {{
    background-color: {COLORS['text_primary']};
    color: white;
    border: none;
    padding: 4px 8px;
    border-radius: 3px;
}}

/* Message Boxes */
QMessageBox {{
    background-color: {COLORS['bg_primary']};
}}

QMessageBox QLabel {{
    color: {COLORS['text_primary']};
}}

/* Professional Card Style */
QGroupBox#card {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    margin: 0px;
    padding: 12px;
}}

/* Success/Error/Warning Boxes */
QGroupBox#successBox {{
    background-color: rgba(34, 134, 58, 0.1);
    border: 1px solid {COLORS['success']};
    border-radius: 4px;
}}

QGroupBox#errorBox {{
    background-color: rgba(203, 36, 49, 0.1);
    border: 1px solid {COLORS['error']};
    border-radius: 4px;
}}

QGroupBox#warningBox {{
    background-color: rgba(176, 136, 0, 0.1);
    border: 1px solid {COLORS['warning']};
    border-radius: 4px;
}}

QGroupBox#infoBox {{
    background-color: rgba(3, 102, 214, 0.1);
    border: 1px solid {COLORS['info']};
    border-radius: 4px;
}}
"""


def apply_professional_style(app: QApplication):
    """Apply professional stylesheet to the entire application"""
    app.setStyle('Fusion')
    app.setStyleSheet(PROFESSIONAL_STYLESHEET)
