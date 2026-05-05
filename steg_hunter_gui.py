"""
StegHunter GUI Application Entry Point
"""
import os
import warnings
import sys

# Suppress TensorFlow and oneDNN warnings before importing anything that uses TF
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

from PyQt5.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.gui.professional_style import apply_professional_style, load_theme_preference

def main():
    app = QApplication(sys.argv)
    
    # Load saved theme preference
    saved_theme = load_theme_preference()
    apply_professional_style(app, theme=saved_theme)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
