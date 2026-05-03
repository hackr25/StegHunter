"""
Professional Stylesheet for StegHunter GUI
Clean, business-appropriate design with proper spacing and typography
Supports both Light and Dark modes
"""

from PyQt5.QtWidgets import QApplication
import json
from pathlib import Path

# Professional Color Palettes
LIGHT_COLORS = {
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

DARK_COLORS = {
    'bg_primary': '#1E1E1E',      # Dark background
    'bg_secondary': '#2D2D2D',    # Dark card/section background
    'bg_hover': '#3A3A3A',        # Hover state
    'text_primary': '#E0E0E0',    # Light text
    'text_secondary': '#A0A0A0',  # Medium gray text
    'border': '#404040',          # Subtle borders
    'accent': '#4A9FFF',          # Bright blue for dark mode
    'accent_light': '#1A3A52',    # Dark blue background
    'success': '#4EC9B0',         # Bright green for dark mode
    'warning': '#FFD93D',         # Bright amber for dark mode
    'error': '#FF6B6B',           # Bright red for dark mode
    'info': '#5DADE2',            # Bright info blue for dark mode
}

# Default to light mode
COLORS = LIGHT_COLORS
CURRENT_THEME = 'light'


def generate_stylesheet(theme='light'):
    """Generate stylesheet for specified theme"""
    colors = LIGHT_COLORS if theme == 'light' else DARK_COLORS
    
    stylesheet = f"""
/* Main Window and Central Widget */
QMainWindow {{
    background-color: {colors['bg_primary']};
    color: {colors['text_primary']};
}}

QWidget {{
    background-color: {colors['bg_primary']};
    color: {colors['text_primary']};
}}

/* Menu Bar */
QMenuBar {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border-bottom: 1px solid {colors['border']};
    padding: 2px 0px;
}}

QMenuBar::item:selected {{
    background-color: {colors['accent_light']};
    color: {colors['accent']};
}}

QMenu {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
}}

QMenu::item:selected {{
    background-color: {colors['accent_light']};
    color: {colors['accent']};
}}

/* Tool Bar */
QToolBar {{
    background-color: {colors['bg_secondary']};
    border-bottom: 1px solid {colors['border']};
    padding: 5px;
    spacing: 5px;
}}

QToolBar::separator {{
    background-color: {colors['border']};
    width: 2px;
    margin: 0px 5px;
}}

/* Buttons */
QPushButton {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: 500;
    font-size: 11pt;
}}

QPushButton:hover {{
    background-color: {colors['bg_hover']};
    border: 1px solid {colors['accent']};
    color: {colors['accent']};
}}

QPushButton:pressed {{
    background-color: {colors['accent_light']};
    border: 1px solid {colors['accent']};
}}

/* Primary Action Button */
QPushButton#primaryButton {{
    background-color: {colors['accent']};
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
    background-color: {colors['success']};
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
    background-color: {colors['warning']};
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
    background-color: {colors['error']};
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
    color: {colors['text_primary']};
    font-size: 10pt;
}}

QLabel#titleLabel {{
    color: {colors['text_primary']};
    font-size: 14pt;
    font-weight: 600;
}}

QLabel#subtitleLabel {{
    color: {colors['text_secondary']};
    font-size: 11pt;
}}

/* Line Edits and Text Input */
QLineEdit, QPlainTextEdit, QTextEdit {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    padding: 6px;
    selection-background-color: {colors['accent']};
    selection-color: white;
}}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{
    border: 2px solid {colors['accent']};
    background-color: {colors['bg_secondary']};
}}

/* Ensure read-only text edits also follow theme */
QTextEdit:read-only, QPlainTextEdit:read-only {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
}}

/* Combo Boxes */
QComboBox {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    padding: 5px;
    min-height: 28px;
}}

QComboBox:focus {{
    border: 2px solid {colors['accent']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
}}

QComboBox QAbstractItemView {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    selection-background-color: {colors['accent_light']};
    selection-color: {colors['accent']};
}}

/* Spin Boxes and Sliders */
QSpinBox, QDoubleSpinBox {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    padding: 5px;
}}

QSlider::groove:horizontal {{
    background-color: {colors['border']};
    height: 6px;
    margin: 2px 0px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {colors['accent']};
    width: 14px;
    margin: -4px 0px;
    border-radius: 7px;
    border: 1px solid {colors['accent']};
}}

QSlider::handle:horizontal:hover {{
    background-color: #0052A3;
}}

/* Checkboxes */
QCheckBox {{
    color: {colors['text_primary']};
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid {colors['border']};
    background-color: {colors['bg_secondary']};
}}

QCheckBox::indicator:hover {{
    border: 1px solid {colors['accent']};
    background-color: {colors['accent_light']};
}}

QCheckBox::indicator:checked {{
    background-color: {colors['accent']};
    border: 1px solid {colors['accent']};
    image: url(:/qt-project.org/styles/commonstyle/images/checkbox.png);
}}

/* Progress Bar */
QProgressBar {{
    background-color: {colors['border']};
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    text-align: center;
    height: 20px;
}}

QProgressBar::chunk {{
    background-color: {colors['accent']};
    border-radius: 3px;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {colors['border']};
    background-color: {colors['bg_primary']};
}}

QTabBar::tab {{
    background-color: {colors['bg_hover']};
    color: {colors['text_secondary']};
    border: 1px solid {colors['border']};
    border-bottom: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-radius: 4px 4px 0px 0px;
}}

QTabBar::tab:selected {{
    background-color: {colors['bg_secondary']};
    color: {colors['accent']};
    border: 1px solid {colors['border']};
    border-bottom: 3px solid {colors['accent']};
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background-color: {colors['bg_secondary']};
    color: {colors['text_primary']};
}}

/* Scroll Bars */
QScrollBar:vertical {{
    background-color: {colors['bg_primary']};
    width: 14px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {colors['border']};
    border-radius: 7px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors['accent']};
}}

QScrollBar:horizontal {{
    background-color: {colors['bg_primary']};
    height: 14px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {colors['border']};
    border-radius: 7px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {colors['accent']};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    border: none;
    background: none;
}}

/* Group Boxes */
QGroupBox {{
    color: {colors['text_primary']};
    border: 1px solid {colors['border']};
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
    background-color: {colors['bg_secondary']};
    color: {colors['text_secondary']};
    border-top: 1px solid {colors['border']};
}}

/* Dialogs */
QDialog {{
    background-color: {colors['bg_primary']};
}}

/* Tooltips */
QToolTip {{
    background-color: {colors['text_primary']};
    color: white;
    border: none;
    padding: 4px 8px;
    border-radius: 3px;
}}

/* Message Boxes */
QMessageBox {{
    background-color: {colors['bg_primary']};
}}

QMessageBox QLabel {{
    color: {colors['text_primary']};
}}

/* Professional Card Style */
QGroupBox#card {{
    background-color: {colors['bg_secondary']};
    border: 1px solid {colors['border']};
    border-radius: 6px;
    margin: 0px;
    padding: 12px;
}}

/* Success/Error/Warning Boxes */
QGroupBox#successBox {{
    background-color: rgba(34, 134, 58, 0.1);
    border: 1px solid {colors['success']};
    border-radius: 4px;
}}

QGroupBox#errorBox {{
    background-color: rgba(203, 36, 49, 0.1);
    border: 1px solid {colors['error']};
    border-radius: 4px;
}}

QGroupBox#warningBox {{
    background-color: rgba(176, 136, 0, 0.1);
    border: 1px solid {colors['warning']};
    border-radius: 4px;
}}

QGroupBox#infoBox {{
    background-color: rgba(3, 102, 214, 0.1);
    border: 1px solid {colors['info']};
    border-radius: 4px;
}}
"""
    return stylesheet


def apply_professional_style(app: QApplication, theme='light'):
    """Apply professional stylesheet to the entire application"""
    global CURRENT_THEME, COLORS
    
    app.setStyle('Fusion')
    stylesheet = generate_stylesheet(theme)
    app.setStyleSheet(stylesheet)
    
    CURRENT_THEME = theme
    COLORS = LIGHT_COLORS if theme == 'light' else DARK_COLORS
    
    # Save theme preference
    _save_theme_preference(theme)


def set_theme(app: QApplication, theme='light'):
    """Change the theme to light or dark"""
    stylesheet = generate_stylesheet(theme)
    app.setStyleSheet(stylesheet)
    
    global CURRENT_THEME, COLORS
    CURRENT_THEME = theme
    COLORS = LIGHT_COLORS if theme == 'light' else DARK_COLORS
    
    _save_theme_preference(theme)


def get_current_theme():
    """Get the current theme"""
    return CURRENT_THEME


def _save_theme_preference(theme):
    """Save theme preference to config file"""
    try:
        config_dir = Path.home() / '.steghunter'
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / 'theme_config.json'
        
        with open(config_file, 'w') as f:
            json.dump({'theme': theme}, f)
    except Exception:
        pass  # Silently fail if unable to save


def load_theme_preference():
    """Load saved theme preference"""
    try:
        config_file = Path.home() / '.steghunter' / 'theme_config.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('theme', 'light')
    except Exception:
        pass  # Silently fail if unable to load
    
    return 'light'
