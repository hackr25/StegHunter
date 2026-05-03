"""
StegHunter GUI Application Entry Point
"""
import sys
from PyQt5.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.gui.professional_style import apply_professional_style

def main():
    app = QApplication(sys.argv)
    apply_professional_style(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
