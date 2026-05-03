"""
StegHunter GUI Application Entry Point
Modern dark theme with vibrant colors
"""
import sys
from PyQt5.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.gui.modern_style import apply_modern_style

def main():
    app = QApplication(sys.argv)
    
    # Apply modern styling
    apply_modern_style(app)
    
    window = MainWindow()
    window.setWindowTitle("🔍 StegHunter - Advanced Steganography Detection Tool")
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
