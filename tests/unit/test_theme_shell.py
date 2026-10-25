"""Theme palette and main-window navigation shell smoke checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.gui.theme import ThemeManager


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
def test_dark_theme_has_dense_desktop_palette() -> None:
    """Dark theme exposes charcoal surfaces and a teal primary accent."""
    mgr = ThemeManager.__new__(ThemeManager)
    colors = mgr.get_theme_colors("dark")
    assert colors["background"].startswith("#")
    assert colors["primary"].lower() == "#2ec4b6"
    assert colors["sidebar"].startswith("#")
    # Dense dark: background should be near-black charcoal, not light
    bg = colors["background"].lstrip("#")
    assert int(bg[0:2], 16) < 0x40


@pytest.mark.unit
def test_stylesheet_includes_nav_rail_selectors() -> None:
    """QSS must style the navigation rail object names used by MainWindow."""
    mgr = ThemeManager.__new__(ThemeManager)
    qss = mgr.get_stylesheet("dark")
    assert "QFrame#navRail" in qss
    assert "QListWidget#navList" in qss
    assert "QStackedWidget#pageStack" in qss
    assert "QLabel#pageTitle" in qss


@pytest.mark.unit
def test_custom_colors_feed_stylesheet() -> None:
    """Custom color maps must appear in the generated QSS (not ignored)."""
    mgr = ThemeManager.__new__(ThemeManager)
    colors = {
        "background": "#112233",
        "surface": "#223344",
        "primary": "#aabbcc",
        "secondary": "#445566",
        "text": "#ffffff",
        "text_secondary": "#cccccc",
        "border": "#334455",
        "success": "#00ff00",
        "warning": "#ffff00",
        "error": "#ff0000",
        "info": "#00ffff",
    }
    qss = mgr.get_stylesheet_from_colors(colors)
    assert "#112233" in qss
    assert "#aabbcc" in qss


@pytest.mark.unit
def test_main_window_defines_nav_shell() -> None:
    """Source of MainWindow keeps the rail + stack shell (no top-level QTabWidget)."""
    source = (REPO_ROOT / "app" / "gui" / "main.py").read_text(encoding="utf-8")
    assert "navRail" in source
    assert "QStackedWidget" in source
    assert "QListWidget" in source
    assert "self.tab_widget = QTabWidget" not in source
