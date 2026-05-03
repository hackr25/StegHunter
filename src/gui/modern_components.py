"""
Enhanced GUI Components for StegHunter
Provides modern, reusable UI components
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QGroupBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPixmap


class ModernCard(QFrame):
    """Modern card-style container with gradient and shadow effect"""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border: 2px solid #00d4ff;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        
        if title:
            title_label = QLabel(title)
            title_font = QFont()
            title_font.setPointSize(12)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #00d4ff;")
            layout.addWidget(title_label)
            layout.addSpacing(10)
        
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
        self.setLayout(layout)
    
    def add_widget(self, widget):
        """Add widget to card content"""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add layout to card content"""
        self.content_layout.addLayout(layout)


class StatusIndicator(QWidget):
    """Modern status indicator with animated color"""
    
    def __init__(self, status_text="", status_type="info", parent=None):
        super().__init__(parent)
        self.status_type = status_type
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Status dot
        self.dot = QLabel("●")
        dot_font = QFont()
        dot_font.setPointSize(16)
        self.dot.setFont(dot_font)
        self.update_status(status_type)
        layout.addWidget(self.dot)
        
        # Status text
        self.text = QLabel(status_text)
        self.text.setFont(QFont())
        layout.addWidget(self.text)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_status(self, status_type):
        """Update status indicator"""
        self.status_type = status_type
        
        if status_type == "success":
            self.dot.setStyleSheet("color: #00cc44; font-weight: bold;")
            self.text.setStyleSheet("color: #00cc44; font-weight: bold;")
        elif status_type == "error":
            self.dot.setStyleSheet("color: #ff0000; font-weight: bold;")
            self.text.setStyleSheet("color: #ff0000; font-weight: bold;")
        elif status_type == "warning":
            self.dot.setStyleSheet("color: #ffaa00; font-weight: bold;")
            self.text.setStyleSheet("color: #ffaa00; font-weight: bold;")
        else:  # info
            self.dot.setStyleSheet("color: #00d4ff; font-weight: bold;")
            self.text.setStyleSheet("color: #00d4ff; font-weight: bold;")
    
    def set_text(self, text):
        """Update status text"""
        self.text.setText(text)


class ModernButton(QPushButton):
    """Modern button with custom styling"""
    
    def __init__(self, text="", button_type="default", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        
        if button_type == "primary":
            self.setObjectName("primaryButton")
        elif button_type == "danger":
            self.setObjectName("dangerButton")
        elif button_type == "success":
            self.setObjectName("successButton")
        
        # Set minimum size for better appearance
        self.setMinimumHeight(35)
        self.setCursor(Qt.PointingHandCursor)


class InfoPanel(QFrame):
    """Information panel with styled background"""
    
    def __init__(self, title="", content="", panel_type="info", parent=None):
        super().__init__(parent)
        
        # Style based on type
        if panel_type == "success":
            bg_color = "#0f3460"
            border_color = "#00cc44"
            text_color = "#00cc44"
        elif panel_type == "warning":
            bg_color = "#3d3d1f"
            border_color = "#ffaa00"
            text_color = "#ffaa00"
        elif panel_type == "error":
            bg_color = "#3d1f1f"
            border_color = "#ff0000"
            text_color = "#ff0000"
        else:  # info
            bg_color = "#0f3460"
            border_color = "#00d4ff"
            text_color = "#00d4ff"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        if title:
            title_label = QLabel(title)
            title_font = QFont()
            title_font.setBold(True)
            title_font.setPointSize(11)
            title_label.setFont(title_font)
            title_label.setStyleSheet(f"color: {text_color};")
            layout.addWidget(title_label)
        
        if content:
            content_label = QLabel(content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("color: #e0e0e0;")
            layout.addWidget(content_label)
        
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
        
        self.setLayout(layout)
    
    def add_widget(self, widget):
        """Add widget to panel"""
        self.content_layout.addWidget(widget)


class SectionHeader(QLabel):
    """Section header with modern styling"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                padding: 10px 0px;
                border-bottom: 2px solid #00d4ff;
            }
        """)
