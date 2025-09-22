"""
Theme management for the application.
"""

import platform
from typing import Dict, Any
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings

from ..services import get_settings, get_logger


class ThemeManager:
    """Manages application themes and styling."""
    
    def __init__(self):
        """Initialize theme manager."""
        self.settings = get_settings()
        self.logger = get_logger()
        self.qsettings = QSettings("VoxHash", "TelegramSender")
        
        # Load saved theme preference
        self.current_theme = self.qsettings.value("theme", "auto", str)
        
        # Apply initial theme
        self.apply_theme(self.current_theme)
    
    def detect_system_theme(self) -> str:
        """Detect system theme preference."""
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows 10/11 dark mode detection
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    winreg.CloseKey(key)
                    return "dark" if value == 0 else "light"
                except:
                    return "light"
            
            elif system == "Darwin":  # macOS
                # macOS dark mode detection
                import subprocess
                try:
                    result = subprocess.run(
                        ["defaults", "read", "-g", "AppleInterfaceStyle"],
                        capture_output=True, text=True
                    )
                    return "dark" if "Dark" in result.stdout else "light"
                except:
                    return "light"
            
            elif system == "Linux":
                # Linux GTK theme detection
                try:
                    import subprocess
                    result = subprocess.run(
                        ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                        capture_output=True, text=True
                    )
                    theme = result.stdout.strip().strip("'")
                    return "dark" if "dark" in theme.lower() else "light"
                except:
                    return "light"
            
        except Exception as e:
            self.logger.warning(f"Failed to detect system theme: {e}")
        
        return "light"  # Default fallback
    
    def get_theme_colors(self, theme: str) -> Dict[str, str]:
        """Get color palette for a theme."""
        if theme == "dark":
            return {
                "background": "#2b2b2b",
                "surface": "#3c3c3c",
                "primary": "#0078d4",
                "secondary": "#6c757d",
                "text": "#ffffff",
                "text_secondary": "#cccccc",
                "border": "#555555",
                "success": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "info": "#17a2b8",
            }
        else:  # light theme
            return {
                "background": "#ffffff",
                "surface": "#f8f9fa",
                "primary": "#0078d4",
                "secondary": "#6c757d",
                "text": "#212529",
                "text_secondary": "#6c757d",
                "border": "#dee2e6",
                "success": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "info": "#17a2b8",
            }
    
    def get_stylesheet(self, theme: str) -> str:
        """Get QSS stylesheet for a theme."""
        colors = self.get_theme_colors(theme)
        
        return f"""
        QMainWindow {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        
        QWidget {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        
        QPushButton {{
            background-color: {colors['primary']};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {colors['primary']}dd;
        }}
        
        QPushButton:pressed {{
            background-color: {colors['primary']}aa;
        }}
        
        QPushButton:disabled {{
            background-color: {colors['secondary']};
            color: {colors['text_secondary']};
        }}
        
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 6px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {colors['primary']};
        }}
        
        QLabel {{
            color: {colors['text']};
        }}
        
        QGroupBox {{
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }}
        
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors['background']};
        }}
        
        QTabBar::tab {{
            background-color: {colors['surface']};
            color: {colors['text']};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['background']};
            border-bottom: 2px solid {colors['primary']};
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors['primary']}20;
        }}
        
        QTableWidget {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            gridline-color: {colors['border']};
        }}
        
        QTableWidget::item {{
            padding: 8px;
        }}
        
        QTableWidget::item:selected {{
            background-color: {colors['primary']}40;
        }}
        
        QHeaderView::section {{
            background-color: {colors['primary']};
            color: white;
            padding: 8px;
            border: none;
        }}
        
        QScrollBar:vertical {{
            background-color: {colors['surface']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors['border']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors['primary']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QStatusBar {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border-top: 1px solid {colors['border']};
        }}
        
        QMenuBar {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border-bottom: 1px solid {colors['border']};
        }}
        
        QMenuBar::item {{
            padding: 4px 8px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['primary']}40;
        }}
        
        QMenu {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
        }}
        
        QMenu::item {{
            padding: 6px 20px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors['primary']}40;
        }}
        
        QProgressBar {{
            background-color: {colors['surface']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {colors['primary']};
            border-radius: 3px;
        }}
        """
    
    def apply_theme(self, theme: str):
        """Apply a theme to the application."""
        if theme == "auto":
            actual_theme = self.detect_system_theme()
        else:
            actual_theme = theme
        
        self.current_theme = actual_theme
        
        # Save preference
        self.qsettings.setValue("theme", theme)
        
        # Apply stylesheet
        app = QApplication.instance()
        if app:
            stylesheet = self.get_stylesheet(actual_theme)
            app.setStyleSheet(stylesheet)
            
            self.logger.info(f"Theme applied: {actual_theme}")
    
    def get_available_themes(self) -> list:
        """Get list of available themes."""
        return ["auto", "light", "dark"]
    
    def get_current_theme(self) -> str:
        """Get current theme."""
        return self.current_theme
