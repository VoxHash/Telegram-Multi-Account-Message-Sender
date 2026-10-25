"""
Theme management for the application.

Provides a dense, modern desktop-client visual language with a VoxHash /
SendGram teal accent on deep charcoal surfaces (plus light, Dracula, and
high-contrast variants).
"""

import platform
from typing import Any, Dict, List, Optional, cast
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QFont

from ..services import get_settings, get_logger


class ThemeManager:
    """Manages application themes and styling."""

    def __init__(self) -> None:
        """Initialize theme manager."""
        self.settings = get_settings()
        self.logger = get_logger()
        self.qsettings = QSettings("VoxHash", "TelegramSender")

        # Load saved theme preference from database settings
        # Convert enum to string value
        self.current_theme = (
            self.settings.theme.value
            if hasattr(self.settings.theme, "value")
            else str(self.settings.theme)
        )

        # Apply initial theme
        self.apply_theme(self.current_theme)

    def detect_system_theme(self) -> str:
        """Detect system theme preference."""
        try:
            system = platform.system()

            if system == "Windows":
                # Windows 10/11 dark mode detection
                # winreg is Windows-only; stubs omit several attrs under Linux CI.
                import winreg as _winreg

                winreg_mod: Any = _winreg
                try:
                    key = winreg_mod.OpenKey(
                        winreg_mod.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                    )
                    value, _ = winreg_mod.QueryValueEx(key, "AppsUseLightTheme")
                    winreg_mod.CloseKey(key)
                    return "dark" if value == 0 else "light"
                except Exception:
                    return "light"

            elif system == "Darwin":  # macOS
                # macOS dark mode detection
                import subprocess

                try:
                    result = subprocess.run(
                        ["defaults", "read", "-g", "AppleInterfaceStyle"],
                        capture_output=True,
                        text=True,
                    )
                    return "dark" if "Dark" in result.stdout else "light"
                except Exception:
                    return "light"

            elif system == "Linux":
                # Linux GTK theme detection
                try:
                    import subprocess

                    result = subprocess.run(
                        ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                        capture_output=True,
                        text=True,
                    )
                    theme = result.stdout.strip().strip("'")
                    return "dark" if "dark" in theme.lower() else "light"
                except Exception:
                    return "light"

        except Exception as e:
            self.logger.warning(f"Failed to detect system theme: {e}")

        return "light"  # Default fallback

    def get_theme_colors(self, theme: str) -> Dict[str, str]:
        """Get color palette for a theme."""
        # Check for custom theme first
        if theme == "custom":
            custom_colors = self.get_custom_theme_colors()
            if custom_colors:
                return custom_colors

        if theme == "high_contrast":
            return {
                "background": "#000000",
                "surface": "#121212",
                "surface_alt": "#1a1a1a",
                "sidebar": "#000000",
                "primary": "#00ffff",
                "primary_hover": "#66ffff",
                "secondary": "#808080",
                "text": "#ffffff",
                "text_secondary": "#ffffff",
                "text_muted": "#cccccc",
                "border": "#00ffff",
                "success": "#00ff00",
                "warning": "#ffff00",
                "error": "#ff0000",
                "info": "#00ffff",
                "nav_hover": "#1a1a1a",
                "nav_active": "#003333",
                "input_bg": "#0a0a0a",
                "header_bg": "#0a0a0a",
            }
        elif theme == "dark":
            # Dense modern desktop client — VoxHash teal on deep charcoal
            return {
                "background": "#0c0e12",
                "surface": "#151922",
                "surface_alt": "#1c2230",
                "sidebar": "#090b0f",
                "primary": "#2ec4b6",
                "primary_hover": "#3dd9ca",
                "secondary": "#6b7280",
                "text": "#e8eaed",
                "text_secondary": "#9aa3b2",
                "text_muted": "#6b7280",
                "border": "#2a3142",
                "success": "#34d399",
                "warning": "#fbbf24",
                "error": "#f87171",
                "info": "#38bdf8",
                "nav_hover": "#151922",
                "nav_active": "#143532",
                "input_bg": "#11151c",
                "header_bg": "#0f1218",
            }
        elif theme == "dracula":
            return {
                "background": "#282a36",
                "surface": "#44475a",
                "surface_alt": "#6272a4",
                "sidebar": "#21222c",
                "primary": "#bd93f9",
                "primary_hover": "#d6b8ff",
                "secondary": "#6272a4",
                "text": "#f8f8f2",
                "text_secondary": "#a9abd0",
                "text_muted": "#6272a4",
                "border": "#6272a4",
                "success": "#50fa7b",
                "warning": "#ffb86c",
                "error": "#ff5555",
                "info": "#8be9fd",
                "nav_hover": "#343746",
                "nav_active": "#3d3258",
                "input_bg": "#343746",
                "header_bg": "#21222c",
            }
        else:  # light theme
            return {
                "background": "#f4f6f8",
                "surface": "#ffffff",
                "surface_alt": "#eef1f5",
                "sidebar": "#0f1419",
                "primary": "#0d9488",
                "primary_hover": "#0f766e",
                "secondary": "#64748b",
                "text": "#0f172a",
                "text_secondary": "#475569",
                "text_muted": "#94a3b8",
                "border": "#d8dee6",
                "success": "#059669",
                "warning": "#d97706",
                "error": "#dc2626",
                "info": "#0284c7",
                "nav_hover": "#1a2330",
                "nav_active": "#134e4a",
                "input_bg": "#ffffff",
                "header_bg": "#ffffff",
            }

    def _ensure_palette(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Fill optional palette keys so QSS templates stay complete."""
        defaults = {
            "surface_alt": colors.get("surface", "#151922"),
            "sidebar": colors.get("background", "#0c0e12"),
            "primary_hover": colors.get("primary", "#2ec4b6"),
            "text_muted": colors.get("text_secondary", "#6b7280"),
            "nav_hover": colors.get("surface", "#151922"),
            "nav_active": colors.get("surface", "#151922"),
            "input_bg": colors.get("surface", "#151922"),
            "header_bg": colors.get("surface", "#151922"),
        }
        merged = dict(defaults)
        merged.update(colors)
        return merged

    def get_stylesheet(self, theme: str) -> str:
        """Get QSS stylesheet for a theme."""
        colors = self._ensure_palette(self.get_theme_colors(theme))
        return self._build_stylesheet(colors)

    def get_stylesheet_from_colors(self, colors: Dict[str, str]) -> str:
        """Get stylesheet from color dictionary."""
        return self._build_stylesheet(self._ensure_palette(colors))

    def _build_stylesheet(self, colors: Dict[str, str]) -> str:
        """Build the full application QSS from a color map."""
        return f"""
        /* ——— Global ——— */
        QMainWindow {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}

        QWidget {{
            background-color: {colors['background']};
            color: {colors['text']};
            font-size: 13px;
            selection-background-color: {colors['primary']}55;
            selection-color: {colors['text']};
        }}

        QToolTip {{
            background-color: {colors['surface_alt']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            padding: 6px 10px;
            border-radius: 6px;
        }}

        /* ——— Navigation rail ——— */
        QFrame#navRail {{
            background-color: {colors['sidebar']};
            border: none;
            border-right: 1px solid {colors['border']};
        }}

        QLabel#navBrand {{
            background-color: transparent;
            color: {colors['text']};
            font-size: 15px;
            font-weight: 700;
            letter-spacing: 0.5px;
            padding: 4px 8px;
        }}

        QLabel#navBrandSub {{
            background-color: transparent;
            color: {colors['text_muted']};
            font-size: 10px;
            padding: 0 8px 12px 8px;
        }}

        QListWidget#navList {{
            background-color: transparent;
            border: none;
            outline: none;
            padding: 4px 8px;
        }}

        QListWidget#navList::item {{
            background-color: transparent;
            color: {colors['text_secondary']};
            border: none;
            border-radius: 8px;
            padding: 10px 12px;
            margin: 2px 0;
        }}

        QListWidget#navList::item:hover {{
            background-color: {colors['nav_hover']};
            color: {colors['text']};
        }}

        QListWidget#navList::item:selected {{
            background-color: {colors['nav_active']};
            color: {colors['primary']};
            font-weight: 600;
            border-left: 3px solid {colors['primary']};
        }}

        QFrame#contentShell {{
            background-color: {colors['background']};
            border: none;
        }}

        QFrame#contentHeader {{
            background-color: {colors['header_bg']};
            border: none;
            border-bottom: 1px solid {colors['border']};
        }}

        QLabel#pageTitle {{
            background-color: transparent;
            color: {colors['text']};
            font-size: 18px;
            font-weight: 700;
        }}

        QLabel#pageSubtitle {{
            background-color: transparent;
            color: {colors['text_muted']};
            font-size: 12px;
        }}

        QStackedWidget#pageStack {{
            background-color: {colors['background']};
            border: none;
        }}

        /* ——— Buttons ——— */
        QPushButton {{
            background-color: {colors['primary']};
            color: #0a0c10;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            min-height: 18px;
        }}

        QPushButton:hover {{
            background-color: {colors['primary_hover']};
        }}

        QPushButton:pressed {{
            background-color: {colors['primary']};
        }}

        QPushButton:disabled {{
            background-color: {colors['surface_alt']};
            color: {colors['text_muted']};
        }}

        QPushButton:flat {{
            background-color: transparent;
            color: {colors['primary']};
        }}

        /* ——— Inputs ——— */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox,
        QDateEdit, QDateTimeEdit, QTimeEdit {{
            background-color: {colors['input_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            padding: 7px 10px;
            selection-background-color: {colors['primary']}66;
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
        QSpinBox:focus, QDoubleSpinBox:focus,
        QDateEdit:focus, QDateTimeEdit:focus, QTimeEdit:focus {{
            border: 1px solid {colors['primary']};
        }}

        QComboBox {{
            background-color: {colors['input_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            padding: 6px 10px;
            min-height: 18px;
        }}

        QComboBox:hover, QComboBox:focus {{
            border-color: {colors['primary']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            selection-background-color: {colors['nav_active']};
            selection-color: {colors['primary']};
            outline: none;
        }}

        QCheckBox, QRadioButton {{
            color: {colors['text']};
            spacing: 8px;
            background-color: transparent;
        }}

        QCheckBox::indicator, QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {colors['border']};
            border-radius: 4px;
            background-color: {colors['input_bg']};
        }}

        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {colors['primary']};
            border-color: {colors['primary']};
        }}

        QLabel {{
            color: {colors['text']};
            background-color: transparent;
        }}

        /* ——— Grouping ——— */
        QGroupBox {{
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: {colors['surface']};
            font-weight: 600;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: {colors['text_secondary']};
        }}

        QFrame {{
            color: {colors['text']};
        }}

        /* ——— Tabs (nested, e.g. Settings) ——— */
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            border-radius: 8px;
            background-color: {colors['surface']};
            top: -1px;
        }}

        QTabBar::tab {{
            background-color: {colors['surface_alt']};
            color: {colors['text_secondary']};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            border: 1px solid {colors['border']};
            border-bottom: none;
        }}

        QTabBar::tab:selected {{
            background-color: {colors['surface']};
            color: {colors['primary']};
            font-weight: 600;
        }}

        QTabBar::tab:hover:!selected {{
            color: {colors['text']};
            background-color: {colors['nav_hover']};
        }}

        /* ——— Tables / lists ——— */
        QTableWidget, QTableView, QTreeWidget, QListWidget {{
            background-color: {colors['surface']};
            alternate-background-color: {colors['surface_alt']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            gridline-color: {colors['border']};
            outline: none;
        }}

        QTableWidget::item, QTableView::item, QTreeWidget::item, QListWidget::item {{
            padding: 8px;
            border: none;
        }}

        QTableWidget::item:selected, QTableView::item:selected,
        QTreeWidget::item:selected, QListWidget::item:selected {{
            background-color: {colors['nav_active']};
            color: {colors['primary']};
        }}

        QHeaderView::section {{
            background-color: {colors['surface_alt']};
            color: {colors['text_secondary']};
            padding: 8px 10px;
            border: none;
            border-bottom: 1px solid {colors['border']};
            border-right: 1px solid {colors['border']};
            font-weight: 600;
        }}

        /* ——— Scrollbars ——— */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 10px;
            margin: 2px;
            border-radius: 5px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {colors['border']};
            border-radius: 5px;
            min-height: 24px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {colors['primary']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            height: 0px;
            background: none;
        }}

        QScrollBar:horizontal {{
            background-color: transparent;
            height: 10px;
            margin: 2px;
            border-radius: 5px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {colors['border']};
            border-radius: 5px;
            min-width: 24px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {colors['primary']};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            width: 0px;
            background: none;
        }}

        /* ——— Chrome ——— */
        QStatusBar {{
            background-color: {colors['sidebar']};
            color: {colors['text_secondary']};
            border-top: 1px solid {colors['border']};
            min-height: 26px;
        }}

        QStatusBar QLabel {{
            background-color: transparent;
            color: {colors['text_secondary']};
            padding: 0 6px;
        }}

        QMenuBar {{
            background-color: {colors['sidebar']};
            color: {colors['text']};
            border-bottom: 1px solid {colors['border']};
            padding: 2px;
        }}

        QMenuBar::item {{
            padding: 6px 10px;
            border-radius: 4px;
        }}

        QMenuBar::item:selected {{
            background-color: {colors['nav_active']};
            color: {colors['primary']};
        }}

        QMenu {{
            background-color: {colors['surface']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 7px 24px;
            border-radius: 4px;
        }}

        QMenu::item:selected {{
            background-color: {colors['nav_active']};
            color: {colors['primary']};
        }}

        QMenu::separator {{
            height: 1px;
            background: {colors['border']};
            margin: 4px 8px;
        }}

        QProgressBar {{
            background-color: {colors['surface_alt']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            text-align: center;
            color: {colors['text']};
            min-height: 14px;
        }}

        QProgressBar::chunk {{
            background-color: {colors['primary']};
            border-radius: 5px;
        }}

        QSplitter::handle {{
            background-color: {colors['border']};
        }}

        QDialog {{
            background-color: {colors['background']};
            color: {colors['text']};
        }}

        QMessageBox {{
            background-color: {colors['surface']};
        }}

        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        """

    def apply_theme(self, theme: str) -> None:
        """Apply a theme to the application."""
        if theme == "auto":
            actual_theme = self.detect_system_theme()
        else:
            actual_theme = theme

        # Update current theme
        self.current_theme = actual_theme

        # Save preference to both QSettings and database
        self.qsettings.setValue("theme", theme)

        # Apply stylesheet
        app = QApplication.instance()
        if isinstance(app, QApplication):
            stylesheet = self.get_stylesheet(actual_theme)
            app.setStyleSheet(stylesheet)
            self._apply_app_font(app)

            self.logger.info(f"Theme applied: {actual_theme} (from setting: {theme})")

    def _apply_app_font(self, app: QApplication) -> None:
        """Prefer a clean modern UI font when available on the host."""
        from PyQt5.QtGui import QFontDatabase

        preferred = [
            "Inter",
            "Segoe UI",
            "SF Pro Text",
            "Ubuntu",
            "Noto Sans",
            "Cantarell",
            "DejaVu Sans",
        ]
        available = {name.lower() for name in QFontDatabase().families()}
        for family in preferred:
            if family.lower() in available:
                app.setFont(QFont(family, 10))
                return
        base = QFont(app.font())
        base.setPointSize(10)
        app.setFont(base)

    def get_available_themes(self) -> List[str]:
        """Get list of available themes."""
        return ["auto", "light", "dark", "dracula", "high_contrast"]

    def get_current_theme(self) -> str:
        """Get the current active theme."""
        return self.current_theme

    def get_custom_theme_colors(self) -> Optional[Dict[str, str]]:
        """Get custom theme colors from settings."""
        custom_colors = self.qsettings.value("custom_theme_colors")
        if custom_colors:
            try:
                import json

                parsed: Any = (
                    json.loads(custom_colors) if isinstance(custom_colors, str) else custom_colors
                )
                if isinstance(parsed, dict) and all(
                    isinstance(k, str) and isinstance(v, str) for k, v in parsed.items()
                ):
                    return cast(Dict[str, str], parsed)
                return None
            except Exception:
                return None
        return None

    def set_custom_theme_colors(self, colors: Dict[str, str]) -> None:
        """Set custom theme colors."""
        import json

        self.qsettings.setValue("custom_theme_colors", json.dumps(colors))
        self.logger.info("Custom theme colors saved")

    def apply_custom_theme(self, colors: Dict[str, str]) -> None:
        """Apply a custom theme with provided colors."""
        self.set_custom_theme_colors(colors)
        app = QApplication.instance()
        if isinstance(app, QApplication):
            stylesheet = self.get_stylesheet_from_colors(colors)
            app.setStyleSheet(stylesheet)
            self._apply_app_font(app)
            self.current_theme = "custom"
            self.logger.info("Custom theme applied")
