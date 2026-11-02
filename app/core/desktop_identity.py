"""Linux / Qt desktop identity for process and window-manager isolation.

Without a unique desktop-file id, Wayland/KDE sees this process as generic
``python3`` and groups or closes it with sibling VoxHash Python GUIs
(e.g. DB Storage Manager).

Call :func:`configure_qt_identity` **before** constructing ``QApplication``,
and/or :func:`apply_desktop_identity` on the instance before showing windows.
"""

from __future__ import annotations

# Freedesktop desktop entry basename (no .desktop) — Wayland app_id / KWin desktopFile.
DESKTOP_FILE_ID = "dev.voxhash.telegram-multi-account-sender"
# Qt application name (window titles / default QSettings app key).
APP_NAME = "Telegram Multi-Account Message Sender"
APP_DISPLAY_NAME = "Telegram Multi-Account Message Sender"
ORGANIZATION_NAME = "VoxHash"
# Unique per-app domain so QStandardPaths / default QSettings never collide.
ORGANIZATION_DOMAIN = "telegram-multi-account-sender.voxhash.dev"
# Must match packaging/linux/*.desktop StartupWMClass and DESKTOP_FILE_ID.
STARTUP_WM_CLASS = DESKTOP_FILE_ID


def configure_qt_identity(version: str | None = None) -> None:
    """Set unique org/app/desktop ids before ``QApplication(...)`` is created."""
    from PyQt5.QtCore import QCoreApplication
    from PyQt5.QtGui import QGuiApplication

    from app import __version__

    QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
    QCoreApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setApplicationVersion(
        version if version is not None else __version__
    )
    QGuiApplication.setApplicationDisplayName(APP_DISPLAY_NAME)
    QGuiApplication.setDesktopFileName(DESKTOP_FILE_ID)


def apply_desktop_identity(app, version: str | None = None) -> None:
    """Instance-level mirror of :func:`configure_qt_identity` (tests / late bind)."""
    from app import __version__

    app.setOrganizationName(ORGANIZATION_NAME)
    if hasattr(app, "setOrganizationDomain"):
        app.setOrganizationDomain(ORGANIZATION_DOMAIN)
    app.setApplicationName(APP_NAME)
    if hasattr(app, "setApplicationDisplayName"):
        app.setApplicationDisplayName(APP_DISPLAY_NAME)
    app.setApplicationVersion(version if version is not None else __version__)
    if hasattr(app, "setDesktopFileName"):
        app.setDesktopFileName(DESKTOP_FILE_ID)
