"""
About widget for displaying application information.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

from ...services import get_logger


class AboutWidget(QWidget):
    """Widget for displaying application information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Main content
        content_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("🚀 Telegram Multi-Account Message Sender")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)
        
        # Version
        version_label = QLabel("Version 1.0.0")
        version_font = QFont()
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(version_label)
        
        # Spacer
        content_layout.addSpacing(20)
        
        # About text
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setMaximumHeight(400)
        about_text.setHtml("""
        <div style="text-align: center; font-family: Arial, sans-serif;">
            <p style="font-size: 14px; line-height: 1.6; margin: 20px 0;">
                <strong>Professional-grade desktop application for managing and sending messages across multiple Telegram accounts safely with advanced features like scheduling, spintax, media support, and compliance controls.</strong>
            </p>
            
            <div style="margin: 30px 0; text-align: left; max-width: 600px; margin-left: auto; margin-right: auto;">
                <p style="font-size: 14px; margin: 15px 0;"><strong>📄 License:</strong><br>
                BSD 3-Clause License - See LICENSE file for details</p>
                
                <p style="font-size: 14px; margin: 15px 0;"><strong>👨‍💻 Developer:</strong><br>
                VoxHash - contact@voxhash.dev</p>
                
                <p style="font-size: 14px; margin: 15px 0;"><strong>⚠️ Disclaimer:</strong><br>
                This application is for educational and legitimate business purposes only. Users are responsible for complying with Telegram's Terms of Service and applicable laws.</p>
                
                <p style="font-size: 14px; margin: 30px 0; text-align: center; font-style: italic;">
                    Made with ❤️ by VoxHash
                </p>
            </div>
        </div>
        """)
        content_layout.addWidget(about_text)
        
        # Add to main layout
        layout.addLayout(content_layout)
        layout.addStretch()
