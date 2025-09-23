"""
About widget for displaying application information.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

from ...services import get_logger
from ...services.translation import _, get_translation_manager


class AboutWidget(QWidget):
    """Widget for displaying application information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.translation_manager = get_translation_manager()
        
        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Main content
        content_layout = QVBoxLayout()
        
        # Title
        self.title_label = QLabel(f"🚀 {_('app.title')}")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.title_label)
        
        # Version
        self.version_label = QLabel(_("app.version").format(version="1.0.0"))
        version_font = QFont()
        version_font.setPointSize(12)
        self.version_label.setFont(version_font)
        self.version_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.version_label)
        
        # Spacer
        content_layout.addSpacing(20)
        
        # About text
        self.about_text = QTextEdit()
        self.about_text.setReadOnly(True)
        self.about_text.setMinimumHeight(500)
        self.about_text.setMaximumHeight(800)
        self.update_about_content()
        content_layout.addWidget(self.about_text)
        
        # Add to main layout
        layout.addLayout(content_layout)
        layout.addStretch()
    
    def update_about_content(self):
        """Update the about content with current translations."""
        self.about_text.setHtml(f"""
        <div style="text-align: center; font-family: Arial, sans-serif;">
            <p style="font-size: 16px; line-height: 1.8; margin: 25px 0;">
                <strong>{_('about.description')}</strong>
            </p>
            
            <div style="margin: 40px 0; text-align: left; max-width: 700px; margin-left: auto; margin-right: auto;">
                <p style="font-size: 16px; margin: 20px 0; line-height: 1.6;"><strong>📄 {_('about.license')}</strong></p>
                
                <p style="font-size: 16px; margin: 20px 0; line-height: 1.6;"><strong>👨‍💻 {_('about.developer')}</strong></p>
                
                <p style="font-size: 16px; margin: 20px 0; line-height: 1.6;"><strong>⚠️ {_('about.disclaimer')}</strong></p>
                
                <p style="font-size: 16px; margin: 40px 0; text-align: center; font-style: italic; line-height: 1.6;">
                    {_('about.made_with')}
                </p>
            </div>
        </div>
        """)
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # Update the content with new translations
        self.title_label.setText(f"🚀 {_('app.title')}")
        self.version_label.setText(_("app.version").format(version="1.0.0"))
        self.update_about_content()
